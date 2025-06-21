import numpy as np
from scipy.fft import fft
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QLinearGradient
from PyQt5.QtCore import QTimer

class AudioVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 100)
        self.bars = [0] * 32
        self.processor = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(50)
        self.bar_smoothing = 0.8
        self.peak_hold = [0] * 32
        self.peak_decay = [0] * 32
        
        # Theme-aware colors
        self.is_dark_theme = True  # Default to dark theme
        self.update_colors()
    
    def set_theme(self, is_dark):
        """Set theme untuk visualizer"""
        self.is_dark_theme = is_dark
        self.update_colors()
        self.update()
    
    def update_colors(self):
        """Update colors berdasarkan theme"""
        if self.is_dark_theme:
            # Dark theme colors - vibrant colors
            self.bass_color = QColor(255, 100, 100)      # Vibrant red
            self.mid_color = QColor(100, 255, 100)       # Vibrant green  
            self.treble_color = QColor(100, 150, 255)    # Vibrant blue
            self.peak_color = QColor(255, 255, 255)      # White
        else:
            # Light theme colors
            self.bass_color = QColor(220, 80, 80)        # Darker red
            self.mid_color = QColor(80, 180, 80)         # Darker green
            self.treble_color = QColor(80, 120, 220)     # Darker blue
            self.peak_color = QColor(60, 60, 60)         # Dark gray
    
    def set_audio_processor(self, processor):
        self.processor = processor
        if processor:
            processor.audio_data.connect(self.process_audio_data)
    
    def process_audio_data(self, audio_chunk):
        try:
            fft_data = np.abs(fft(audio_chunk))
            fft_data = fft_data[:len(fft_data)//2]
            bar_count = len(self.bars)
            chunk_size = max(1, len(fft_data) // bar_count)
            new_bars = []
            for i in range(bar_count):
                start_idx = i * chunk_size
                end_idx = min(start_idx + chunk_size, len(fft_data))
                if start_idx < len(fft_data):
                    magnitude = np.mean(fft_data[start_idx:end_idx])
                    height = min(int(magnitude * 1000), self.height() - 10)
                    new_bars.append(height)
                else:
                    new_bars.append(0)
            for i in range(len(self.bars)):
                self.bars[i] = int(self.bars[i] * self.bar_smoothing + 
                                new_bars[i] * (1 - self.bar_smoothing))
                if new_bars[i] > self.peak_hold[i]:
                    self.peak_hold[i] = new_bars[i]
                    self.peak_decay[i] = 0
                else:
                    self.peak_decay[i] += 1
                    if self.peak_decay[i] > 10:
                        self.peak_hold[i] = max(0, self.peak_hold[i] - 2)
        except Exception as e:
            print(f"Error processing audio data: {e}")
    
    def reset_visualization(self):
        self.bars = [0] * 32
        self.peak_hold = [0] * 32
        self.update()
    
    def update_display(self):
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bar_width = self.width() // len(self.bars)
        
        for i, height in enumerate(self.bars):
            if height <= 0:
                continue
                
            x = i * bar_width
            y = self.height() - height
            
            # Determine color based on frequency range
            if i < len(self.bars) // 3:
                # Bass frequencies
                color = self.bass_color
            elif i < 2 * len(self.bars) // 3:
                # Mid frequencies  
                color = self.mid_color
            else:
                # Treble frequencies
                color = self.treble_color
            
            # Create gradient effect for bars
            gradient = QLinearGradient(0, y, 0, self.height())
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color.darker(120))
            
            # Draw bar with gradient
            painter.fillRect(x + 1, y, bar_width - 2, height, gradient)
            
            # Draw peak indicator
            peak_y = self.height() - self.peak_hold[i]
            if self.peak_hold[i] > 5:
                painter.fillRect(x + 1, peak_y - 2, bar_width - 2, 2, self.peak_color)