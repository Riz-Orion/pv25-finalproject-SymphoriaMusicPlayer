import re
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class LyricsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.lyrics_data = []
        self.current_position = 0
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Simple lyrics label
        self.lyrics_label = QLabel("No lyrics loaded")
        self.lyrics_label.setAlignment(Qt.AlignCenter)
        self.lyrics_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.lyrics_label)
        
        self.setLayout(layout)
    
    def load_lyrics_file(self, file_path):
        try:
            self.lyrics_data = self.parse_lrc_file(file_path)
            self.update_lyrics_display(0)
            print(f"Loaded lyrics from: {file_path}")
            return True
        except Exception as e:
            print(f"Error loading lyrics: {e}")
            self.lyrics_label.setText("Error loading lyrics")
            self.lyrics_data = []
            return False
    
    def parse_lrc_file(self, file_path):
        lyrics = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Match timestamp format [mm:ss.xx]
                    match = re.match(r'\[(\d{2}):(\d{2})\.(\d{2})\](.*)', line.strip())
                    if match:
                        minutes, seconds, hundredths, text = match.groups()
                        # Convert to milliseconds
                        timestamp = (int(minutes) * 60 + int(seconds)) * 1000 + int(hundredths) * 10
                        lyrics.append((timestamp, text.strip()))
            return sorted(lyrics, key=lambda x: x[0])
        except Exception as e:
            print(f"Error parsing .lrc file: {e}")
            return []
    
    def update_lyrics_display(self, position_ms):
        if not self.lyrics_data:
            self.lyrics_label.setText("No lyrics loaded")
            return
        
        current_lyric = " "
        for i, (timestamp, text) in enumerate(self.lyrics_data):
            if position_ms < timestamp:
                if i > 0:
                    current_lyric = self.lyrics_data[i-1][1]
                break
            current_lyric = text
        
        self.lyrics_label.setText(current_lyric)
        self.current_position = position_ms
    
    def clear_lyrics(self):
        self.lyrics_data = []
        self.lyrics_label.setText("No lyrics loaded")