import numpy as np
from scipy.fft import fft
from scipy import signal
import librosa
import sounddevice as sd
from PyQt5.QtCore import QThread, pyqtSignal

class AudioEqualizer:
    def __init__(self):
        self.sample_rate = 44100
        self.frequencies = [60, 170, 310, 600, 1000, 3000, 6000, 12000]
        self.gains = [0.0] * len(self.frequencies)
        self.filters = []
        self.init_filters()
    
    def init_filters(self):
        self.filters = []
        for i, freq in enumerate(self.frequencies):
            if i == 0:
                b, a = signal.iirfilter(2, freq / self.sample_rate * 2, btype='lowpass', 
                                    ftype='butter', fs=self.sample_rate)
            elif i == len(self.frequencies) - 1:
                b, a = signal.iirfilter(2, freq / self.sample_rate * 2, btype='highpass', 
                                    ftype='butter', fs=self.sample_rate)
            else:
                bandwidth = 0.5
                low_freq = freq / (1 + bandwidth)
                high_freq = freq * (1 + bandwidth)
                b, a = signal.iirfilter(2, [low_freq / self.sample_rate * 2, high_freq / self.sample_rate * 2], 
                                    btype='bandpass', ftype='butter', fs=self.sample_rate)
            self.filters.append((b, a))
    
    def set_gain(self, band_index, gain_db):
        if 0 <= band_index < len(self.gains):
            self.gains[band_index] = gain_db
    
    def apply_eq(self, audio_data):
        if len(audio_data) == 0:
            return audio_data
            
        try:
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            output = np.zeros_like(audio_data)
            
            for i, (b, a) in enumerate(self.filters):
                filtered = signal.lfilter(b, a, audio_data)
                gain_linear = 10 ** (self.gains[i] / 20.0)
                filtered *= gain_linear
                output += filtered
            
            max_val = np.max(np.abs(output))
            if max_val > 1.0:
                output = output / max_val
                
            return output
        except Exception as e:
            print(f"Error in equalizer: {e}")
            return audio_data

class AudioProcessor(QThread):
    audio_data = pyqtSignal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.current_file = None
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.audio_data_buffer = None
        self.position = 0
        self.equalizer = AudioEqualizer()
        self.output_stream = None
        self.volume_gain = 0.7
        
    def set_audio_file(self, file_path):
        try:
            self.audio_data_buffer, self.sample_rate = librosa.load(
                file_path, sr=self.sample_rate, mono=True
            )
            self.equalizer.sample_rate = self.sample_rate
            self.equalizer.init_filters()
            self.current_file = file_path
            self.position = 0
            self.init_audio_output()
        except Exception as e:
            print(f"Error loading audio file: {e}")
            self.audio_data_buffer = None
    
    def init_audio_output(self):
        try:
            if self.output_stream is not None:
                self.output_stream.stop()
                self.output_stream.close()
            
            self.output_stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self.chunk_size,
                callback=self.audio_callback
            )
        except Exception as e:
            print(f"Error initializing audio output: {e}")
    
    def audio_callback(self, outdata, frames, time, status):
        if self.audio_data_buffer is not None and self.is_running:
            if self.position < len(self.audio_data_buffer):
                end_pos = min(self.position + frames, len(self.audio_data_buffer))
                chunk = self.audio_data_buffer[self.position:end_pos]
                
                if len(chunk) > 0:
                    processed_chunk = self.equalizer.apply_eq(chunk)
                    processed_chunk *= getattr(self, 'volume_gain', 1.0)
                    
                    if len(processed_chunk) < frames:
                        padded_chunk = np.zeros(frames)
                        padded_chunk[:len(processed_chunk)] = processed_chunk
                        processed_chunk = padded_chunk
                    
                    outdata[:] = processed_chunk.reshape(-1, 1)
                    self.audio_data.emit(processed_chunk)
                    self.position += len(chunk)
                else:
                    outdata.fill(0)
            else:
                outdata.fill(0)
                if self.is_running:
                    self.is_running = False
        else:
            outdata.fill(0)
    
    def set_volume(self, gain):
        self.volume_gain = max(0.0, min(1.0, gain))
    
    def set_position(self, position_ms):
        if self.audio_data_buffer is not None:
            self.position = int((position_ms / 1000.0) * self.sample_rate)
    
    def set_eq_gain(self, band_index, gain_db):
        self.equalizer.set_gain(band_index, gain_db)
    
    def start_playback(self):
        self.is_running = True
        if self.output_stream is not None:
            self.output_stream.start()
        self.start()
    
    def stop_playback(self):
        self.is_running = False
        if self.output_stream is not None:
            self.output_stream.stop()
        self.quit()
        self.wait()
    
    def pause_playback(self):
        self.is_running = False
        if self.output_stream is not None:
            self.output_stream.stop()
    
    def resume_playback(self):
        self.is_running = True
        if self.output_stream is not None:
            self.output_stream.start()
    
    def run(self):
        while self.is_running:
            self.msleep(50)