from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

class Equalizer(QWidget):
    eq_changed = pyqtSignal(int, float)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['Flat', 'Rock', 'Pop', 'Jazz', 'Classical', 'Bass Boost', 'Treble Boost'])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)
        
        freq_layout = QHBoxLayout()
        self.sliders = []
        self.value_labels = []
        frequencies = ['60Hz', '170Hz', '310Hz', '600Hz', '1kHz', '3kHz', '6kHz', '12kHz']
        
        for i, freq in enumerate(frequencies):
            slider_layout = QVBoxLayout()
            
            value_label = QLabel('0 dB')
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("font-size: 10px;")  # Remove color, rely on parent
            slider_layout.addWidget(value_label)
            self.value_labels.append(value_label)
            
            slider = QSlider(Qt.Vertical)
            slider.setRange(-12, 12)
            slider.setValue(0)
            slider.valueChanged.connect(
                lambda v, idx=i, lbl=value_label: self.slider_changed(idx, v, lbl)
            )
            slider_layout.addWidget(slider)
            
            freq_label = QLabel(freq)
            freq_label.setAlignment(Qt.AlignCenter)
            freq_label.setStyleSheet("font-size: 10px;")  # Remove color, rely on parent
            slider_layout.addWidget(freq_label)
            
            freq_layout.addLayout(slider_layout)
            self.sliders.append(slider)
        
        layout.addLayout(freq_layout)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_eq)
        layout.addWidget(reset_btn)
        
        self.setLayout(layout)
    
    def slider_changed(self, band_index, value, label):
        label.setText(f'{value} dB')
        self.eq_changed.emit(band_index, float(value))
    
    def apply_preset(self, preset_name):
        presets = {
            'Flat': [0, 0, 0, 0, 0, 0, 0, 0],
            'Rock': [4, 2, -2, -1, 1, 3, 4, 3],
            'Pop': [-1, 2, 4, 4, 1, -1, -1, -1],
            'Jazz': [3, 2, 1, 2, -1, -1, 0, 1],
            'Classical': [4, 3, 2, 0, -1, -1, 0, 3],
            'Bass Boost': [6, 4, 2, 0, 0, 0, 0, 0],
            'Treble Boost': [0, 0, 0, 0, 2, 4, 6, 8]
        }
        
        if preset_name in presets:
            values = presets[preset_name]
            for i, value in enumerate(values):
                if i < len(self.sliders):
                    self.sliders[i].setValue(value)
                    self.value_labels[i].setText(f'{value} dB')
                    self.eq_changed.emit(i, float(value))
    
    def reset_eq(self):
        for i, slider in enumerate(self.sliders):
            slider.setValue(0)
            self.value_labels[i].setText('0 dB')
            self.eq_changed.emit(i, 0.0)