import sys
import os
import random
import json
import csv
from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QGroupBox, QFileDialog, QMessageBox, QAction, QMenu, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon
from mutagen import File
from database_manager import DatabaseManager
from audio_processor import AudioProcessor
from visualizer import AudioVisualizer
from equalizer import Equalizer
from playlist import PlaylistWidget
from lyrics import LyricsWidget

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.current_song_id = None
        self.current_song_index = -1
        self.current_theme = "dark"
        self.shuffle_indices = []  # Daftar indeks untuk shuffle
        self.shuffle_played = []
        self.init_ui()
        self.init_player()
    
    def init_ui(self):
        self.setWindowTitle("Symphoria")
        self.setGeometry(100, 100, 1200, 900)

        self.create_status_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        left_panel = QWidget()
        left_panel.setFixedWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        self.lyrics_widget = LyricsWidget()
        self.playlist_widget = PlaylistWidget(self.db_manager, self.lyrics_widget)
        self.playlist_widget.song_selected.connect(self.play_song)
        left_layout.addWidget(self.playlist_widget)
        
        main_layout.addWidget(left_panel)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("border: 1px solid #555555; background-color: #353535;")
        self.cover_label.setObjectName("cover_label")
        info_layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)
        
        self.song_title = QLabel("No song loaded")
        self.song_title.setAlignment(Qt.AlignCenter)
        self.song_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        info_layout.addWidget(self.song_title)
        
        self.song_artist = QLabel("")
        self.song_artist.setAlignment(Qt.AlignCenter)
        self.song_artist.setStyleSheet("font-size: 14px; color: gray;")
        info_layout.addWidget(self.song_artist)
        
        right_layout.addWidget(info_widget)
        
        self.visualizer = AudioVisualizer()
        right_layout.addWidget(self.visualizer, alignment=Qt.AlignCenter)
        
        right_layout.addWidget(self.lyrics_widget, alignment=Qt.AlignCenter)
        
        progress_layout = QHBoxLayout()
        self.time_label = QLabel("00:00")
        progress_layout.addWidget(self.time_label)
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.sliderMoved.connect(self.seek_position)
        progress_layout.addWidget(self.progress_slider)
        
        self.duration_label = QLabel("00:00")
        progress_layout.addWidget(self.duration_label)
        
        right_layout.addLayout(progress_layout)
        
        controls_layout = QHBoxLayout()
        
        self.shuffle_btn = QPushButton()
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.setFixedSize(50, 50)
        self.shuffle_btn.clicked.connect(self.update_shuffle_state)
        self.shuffle_btn.setToolTip("Toggle Shuffle")
        self.shuffle_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/shuffle.png);
            }
            QPushButton:checked {
                image: url(asset/icons/shuffle_active.png);
            }
        """)
        controls_layout.addWidget(self.shuffle_btn)
        
        self.prev_btn = QPushButton()
        self.prev_btn.setFixedSize(50, 50)
        self.prev_btn.clicked.connect(self.previous_song)
        self.prev_btn.setToolTip("Previous Song")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/prev.png);
            }
        """)
        controls_layout.addWidget(self.prev_btn)
        
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(70, 70)
        self.play_btn.clicked.connect(self.toggle_playback)
        self.play_btn.setToolTip("Play/Pause")
        self.play_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/play.png);
            }
        """)
        self.play_btn.setProperty("state", "play")
        controls_layout.addWidget(self.play_btn)
        
        self.next_btn = QPushButton()
        self.next_btn.setFixedSize(50, 50)
        self.next_btn.clicked.connect(self.next_song)
        self.next_btn.setToolTip("Next Song")
        self.next_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/next.png);
            }
        """)
        controls_layout.addWidget(self.next_btn)
        
        self.repeat_btn = QPushButton()
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.setFixedSize(50, 50)
        self.repeat_btn.clicked.connect(self.update_repeat_state)
        self.repeat_btn.setToolTip("Toggle Repeat")
        self.repeat_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/repeat.png);
            }
            QPushButton:checked {
                image: url(asset/icons/repeat_active.png);
            }
        """)
        controls_layout.addWidget(self.repeat_btn)
        
        controls_layout.addStretch()
        
        volume_widget = QWidget()
        volume_widget.setFixedWidth(200)
        volume_layout = QHBoxLayout(volume_widget)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(5)

        volume_icon = QLabel()
        volume_icon.setFixedSize(30, 30)
        volume_icon.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                image: url(asset/icons/volume.png);
            }
        """)
        volume_layout.addWidget(volume_icon)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)

        controls_layout.addWidget(volume_widget)
        
        right_layout.addLayout(controls_layout)
        
        self.equalizer = Equalizer()
        equalizer_group = QGroupBox("Equalizer")
        equalizer_layout = QVBoxLayout(equalizer_group)
        equalizer_layout.addWidget(self.equalizer)
        right_layout.addWidget(equalizer_group)
        
        main_layout.addWidget(right_panel)

        self.create_menu_bar()
        
        self.statusBar().showMessage("Ready")
        self.apply_dark_theme()
    
    def init_player(self):
        self.audio_processor = AudioProcessor()
        self.visualizer.set_audio_processor(self.audio_processor)
        self.equalizer.eq_changed.connect(self.audio_processor.set_eq_gain)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)
        self.is_playing = False
        self.current_position = 0
        self.total_duration = 0

    def apply_theme(self):
        if self.current_theme == "dark":
            self.apply_dark_theme()
        else:  # light theme
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        dark_style = """
        QMainWindow { background-color: #2b2b2b; color: #ffffff; }
        QWidget { background-color: #2b2b2b; color: #ffffff; }
        QPushButton { background-color: #404040; border: 1px solid #555555; border-radius: 5px; padding: 5px; color: #ffffff; }
        QPushButton:pressed { background-color: #353535; }
        QPushButton:checked { background-color: #0078d4; }
        QSlider::groove:horizontal { height: 8px; background: #444444; border-radius: 4px; }
        QSlider::handle:horizontal { background: #0078d4; width: 16px; height: 16px; border-radius: 8px; margin: -4px 0; }
        QSlider::sub-page:horizontal { background: #0078d4; border-radius: 4px; }
        QListWidget { background-color: #353535; border: 1px solid #555555; }
        QListWidget::item { padding: 5px; border-bottom: 1px solid #444444; }
        QListWidget::item:selected { background-color: #0078d4; }
        QGroupBox { font-weight: bold; border: 1px solid #555555; border-radius: 5px; margin-top: 10px; padding-top: 10px; }
        QGroupBox::title { subcontrol-origin: margin; padding: 0 3px; }
        QLabel#cover_label { border: 1px solid #555555; background-color: #353535; }
        QComboBox { background-color: #353535; border: 1px solid #555555; border-radius: 3px; color: #ffffff; padding: 4px 8px; selection-background-color: #0078d4; }
        QComboBox:hover { border: 1px solid #0078d4; }
        QComboBox:focus { border: 2px solid #0078d4; }
        QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left: 1px solid #555555; border-top-right-radius: 3px; border-bottom-right-radius: 3px; background-color: #404040; }
        QComboBox::drop-down:hover { background-color: #4a4a4a; }
        QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 4px solid #cccccc; width: 0px; height: 0px; }
        QComboBox QAbstractItemView { background-color: #353535; color: #ffffff; selection-background-color: #0078d4; selection-color: #ffffff; border: 1px solid #555555; outline: none; }
        QComboBox QAbstractItemView::item { padding: 4px 8px; border: none; color: #ffffff; }
        QComboBox QAbstractItemView::item:selected { background-color: #0078d4; color: #ffffff; }
        QComboBox QAbstractItemView::item:hover { background-color: #404040; color: #ffffff; }
        QMenu { background-color: #353535; color: #ffffff; border: 1px solid #555555; }
        QMenu::item:selected { background-color: #0078d4; }
        QMenuBar { background-color: #2b2b2b; color: #ffffff; border-bottom: 1px solid #555555; }
        QMenuBar::item { background-color: transparent; padding: 4px 8px; }
        QMenuBar::item:selected { background-color: #404040; }
        QMenuBar::item:pressed { background-color: #0078d4; }
        QStatusBar { background-color: #353535; color: #ffffff; border-top: 1px solid #555555; }
        
        /* Modern Scrollbar Styling - Dark Theme */
        QScrollBar:vertical {
            background: transparent;
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #606060, stop:1 #4a4a4a);
            border: none;
            border-radius: 6px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #0078d4, stop:1 #005bb5);
        }
        
        QScrollBar::handle:vertical:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #005bb5, stop:1 #003d7a);
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        
        QScrollBar:horizontal {
            background: transparent;
            height: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #606060, stop:1 #4a4a4a);
            border: none;
            border-radius: 6px;
            min-width: 30px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #0078d4, stop:1 #005bb5);
        }
        
        QScrollBar::handle:horizontal:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #005bb5, stop:1 #003d7a);
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
            width: 0px;
        }
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        
        /* Special styling for corners */
        QScrollBar::corner {
            background: transparent;
        }
        """
        self.visualizer.set_theme(True)
        self.setStyleSheet(dark_style)

    def apply_light_theme(self):
        light_style = """
        QMainWindow { background-color: #f0f0f0; color: #333333; }
        QWidget { background-color: #f0f0f0; color: #333333; }
        QPushButton { background-color: #e0e0e0; border: 1px solid #cccccc; border-radius: 5px; padding: 5px; color: #333333; }
        QPushButton:pressed { background-color: #d0d0d0; }
        QPushButton:checked { background-color: #0078d4; color: #ffffff; }
        QSlider::groove:horizontal { height: 8px; background: #cccccc; border-radius: 4px; }
        QSlider::handle:horizontal { background: #0078d4; width: 16px; height: 16px; border-radius: 8px; margin: -4px 0; }
        QSlider::sub-page:horizontal { background: #0078d4; border-radius: 4px; }
        QListWidget { background-color: #ffffff; border: 1px solid #cccccc; }
        QListWidget::item { padding: 5px; border-bottom: 1px solid #e0e0e0; }
        QListWidget::item:selected { background-color: #0078d4; color: #ffffff; }
        QGroupBox { font-weight: bold; border: 1px solid #cccccc; border-radius: 5px; margin-top: 10px; padding-top: 10px; }
        QGroupBox::title { subcontrol-origin: margin; padding: 0 3px; }
        QLabel#cover_label { border: 1px solid #cccccc; background-color: #ffffff; }
        QComboBox { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 3px; color: #333333; padding: 4px 8px; selection-background-color: #0078d4; }
        QComboBox:hover { border: 1px solid #0078d4; }
        QComboBox:focus { border: 2px solid #0078d4; }
        QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left: 1px solid #cccccc; border-top-right-radius: 3px; border-bottom-right-radius: 3px; background-color: #f0f0f0; }
        QComboBox::drop-down:hover { background-color: #e0e0e0; }
        QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 4px solid #666666; width: 0px; height: 0px; }
        QComboBox QAbstractItemView { background-color: #ffffff; color: #333333; selection-background-color: #0078d4; selection-color: #ffffff; border: 1px solid #cccccc; outline: none; }
        QComboBox QAbstractItemView::item { padding: 4px 8px; border: none; color: #333333; }
        QComboBox QAbstractItemView::item:selected { background-color: #0078d4; color: #ffffff; }
        QComboBox QAbstractItemView::item:hover { background-color: #e6f3ff; color: #333333;}
        QMenu { background-color: #ffffff; color: #333333; border: 1px solid #cccccc; }
        QMenu::item:selected { background-color: #0078d4; color: #ffffff; }
        QMenuBar { background-color: #f0f0f0; color: #333333; border-bottom: 1px solid #cccccc; }
        QMenuBar::item { background-color: transparent; padding: 4px 8px; }
        QMenuBar::item:selected { background-color: #d0d0d0; }
        QMenuBar::item:pressed { background-color: #0078d4; color: #ffffff; }
        QStatusBar { background-color: #ffffff; color: #333333; border-top: 1px solid #cccccc; }
        
        /* Modern Scrollbar Styling - Light Theme */
        QScrollBar:vertical {
            background: transparent;
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #d0d0d0, stop:1 #b0b0b0);
            border: none;
            border-radius: 6px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #0078d4, stop:1 #005bb5);
        }
        
        QScrollBar::handle:vertical:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 #005bb5, stop:1 #003d7a);
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        
        QScrollBar:horizontal {
            background: transparent;
            height: 12px;
            border-radius: 6px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #d0d0d0, stop:1 #b0b0b0);
            border: none;
            border-radius: 6px;
            min-width: 30px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #0078d4, stop:1 #005bb5);
        }
        
        QScrollBar::handle:horizontal:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #005bb5, stop:1 #003d7a);
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
            width: 0px;
        }
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        
        /* Special styling for corners */
        QScrollBar::corner {
            background: transparent;
        }
        """
        self.visualizer.set_theme(False)
        self.setStyleSheet(light_style)

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme()
        print(f"Switched to {self.current_theme} theme")

    def update_shuffle_state(self):
        state = self.shuffle_btn.isChecked()
        print(f"Shuffle {'enabled' if state else 'disabled'}")
    
    def update_repeat_state(self):
        state = self.repeat_btn.isChecked()
        print(f"Repeat {'enabled' if state else 'disabled'}")
    
    def toggle_playback(self):
        if self.is_playing:
            self.audio_processor.pause_playback()
            self.is_playing = False
            self.play_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    image: url(asset/icons/play.png);
                }
            """)
            self.play_btn.setProperty("state", "play")
            print("Playback paused")
        else:
            self.audio_processor.resume_playback()
            self.is_playing = True
            self.play_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    image: url(asset/icons/pause.png);
                }
            """)
            self.play_btn.setProperty("state", "pause")
            print("Playback resumed")
    
    def play_song(self, file_path, index=-1):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        
        print(f"Playing song: {file_path}, provided index: {index}")
        self.current_song_index = index if index >= 0 else 0
        print(f"Set current_song_index to: {self.current_song_index}")
        
        self.audio_processor.stop_playback()
        self.visualizer.reset_visualization()
        self.lyrics_widget.clear_lyrics()
        self.audio_processor.set_audio_file(file_path)
        
        try:
            audio_file = File(file_path)
            title = os.path.basename(file_path)
            artist = "Unknown Artist"
            
            if audio_file:
                title = str(audio_file.get('TIT2', [title])[0]) if audio_file.get('TIT2') else title
                artist = str(audio_file.get('TPE1', [artist])[0]) if audio_file.get('TPE1') else artist
                self.total_duration = int(audio_file.info.length * 1000) if audio_file.info else 0
                self.progress_slider.setRange(0, self.total_duration)
                self.duration_label.setText(self.format_time(self.total_duration))
                
                cover_data = None
                for tag in audio_file.tags.values():
                    if hasattr(tag, 'data') and tag.mime.startswith('image/'):
                        cover_data = tag.data
                        break
                
                if cover_data:
                    pixmap = QPixmap()
                    pixmap.loadFromData(cover_data)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            self.cover_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.cover_label.setPixmap(scaled_pixmap)
                    else:
                        self.load_default_cover()
                else:
                    self.load_default_cover()
            
            self.song_title.setText(title)
            self.song_artist.setText(artist)
            
            item = self.playlist_widget.playlist_list.item(self.current_song_index)
            if item:
                song_id = item.data(Qt.UserRole + 1)
                self.current_song_id = song_id
                cursor = self.db_manager.conn.cursor()
                cursor.execute('SELECT lyrics_path FROM songs WHERE id = ?', (song_id,))
                result = cursor.fetchone()
                if result and result[0] and os.path.exists(result[0]):
                    self.lyrics_widget.load_lyrics_file(result[0])
                    print(f"Loaded lyrics from database: {result[0]}")
                else:
                    lyrics_file = os.path.splitext(file_path)[0] + '.lrc'
                    if os.path.exists(lyrics_file):
                        self.lyrics_widget.load_lyrics_file(lyrics_file)
                        self.db_manager.assign_lyrics(song_id, lyrics_file)
                        print(f"Automatically loaded and assigned lyrics: {lyrics_file}")
            
        except Exception as e:
            print(f"Error reading metadata: {e}")
            self.song_title.setText(os.path.basename(file_path))
            self.song_artist.setText("Unknown Artist")
            self.load_default_cover()
            self.total_duration = 0
            self.lyrics_widget.clear_lyrics()
        
        self.audio_processor.start_playback()
        self.is_playing = True
        self.play_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/pause.png);
            }
        """)
        self.play_btn.setProperty("state", "pause")
        self.statusBar().showMessage(f"Playing: {os.path.basename(file_path)}")
        self.current_song_info.setText(f"♪ {title} - {artist}")
    
    def load_default_cover(self):
        default_path = "asset/song_cover.png"
        if os.path.exists(default_path):
            default_pixmap = QPixmap(default_path)
            scaled_pixmap = default_pixmap.scaled(
                self.cover_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.cover_label.setPixmap(scaled_pixmap)
        else:
            print(f"Default cover not found: {default_path}")
            self.cover_label.clear()
    
    def update_shuffle_state(self):
        state = self.shuffle_btn.isChecked()
        if state:
            # Inisialisasi daftar indeks untuk shuffle
            total_songs = self.playlist_widget.playlist_list.count()
            self.shuffle_indices = list(range(total_songs))
            random.shuffle(self.shuffle_indices)
            self.shuffle_played = []
            print(f"Shuffle enabled, initialized {len(self.shuffle_indices)} indices")
        else:
            self.shuffle_indices = []
            self.shuffle_played = []
            print("Shuffle disabled")
    
    def next_song(self, auto_next=False):
        playlist_list = self.playlist_widget.playlist_list
        total_songs = playlist_list.count()
        if total_songs == 0:
            print("No songs in playlist")
            return
        
        if self.repeat_btn.isChecked() and self.current_song_index >= 0:
            print("Repeating current song")
            self.seek_position(0)
            self.audio_processor.start_playback()
            return
        
        if self.shuffle_btn.isChecked():
            # Jika semua lagu sudah diputar, buat ulang daftar indeks
            if not self.shuffle_indices:
                self.shuffle_indices = list(range(total_songs))
                random.shuffle(self.shuffle_indices)
                self.shuffle_played = []
                print("All songs played, reshuffling indices")
            
            # Ambil indeks berikutnya dari daftar shuffle
            self.current_song_index = self.shuffle_indices.pop(0)
            self.shuffle_played.append(self.current_song_index)
            print(f"Shuffle: Selected index {self.current_song_index}, remaining {len(self.shuffle_indices)} songs")
        else:
            # Mode normal, pilih lagu berikutnya secara berurutan
            if self.current_song_index < 0:
                self.current_song_index = 0
            else:
                self.current_song_index = (self.current_song_index + 1) % total_songs
        
        item = playlist_list.item(self.current_song_index)
        if item:
            file_path = item.data(Qt.UserRole)
            print(f"Next song: {file_path}, index: {self.current_song_index}")
            self.play_song(file_path, self.current_song_index)
        else:
            print(f"No item at index {self.current_song_index}")

    def previous_song(self):
        playlist_list = self.playlist_widget.playlist_list
        total_songs = playlist_list.count()
        if total_songs == 0:
            print("No songs in playlist")
            return
        
        if self.shuffle_btn.isChecked():
            # Jika ada lagu yang sudah diputar, ambil lagu sebelumnya dari daftar yang sudah diputar
            if len(self.shuffle_played) > 1:
                self.shuffle_indices.insert(0, self.current_song_index)
                self.shuffle_played.pop()  # Hapus lagu saat ini
                self.current_song_index = self.shuffle_played[-1]  # Ambil lagu sebelumnya
                print(f"Shuffle: Reverting to previous index {self.current_song_index}")
            else:
                # Jika tidak ada lagu sebelumnya, acak ulang
                self.shuffle_indices = list(range(total_songs))
                random.shuffle(self.shuffle_indices)
                self.current_song_index = self.shuffle_indices.pop(0)
                self.shuffle_played = [self.current_song_index]
                print(f"Shuffle: No previous song, selected new index {self.current_song_index}")
        else:
            # Mode normal, pilih lagu sebelumnya secara berurutan
            if self.current_song_index < 0:
                self.current_song_index = total_songs - 1
            else:
                self.current_song_index = (self.current_song_index - 1) % total_songs
        
        item = playlist_list.item(self.current_song_index)
        if item:
            file_path = item.data(Qt.UserRole)
            print(f"Previous song: {file_path}, index: {self.current_song_index}")
            self.play_song(file_path, self.current_song_index)
        else:
            print(f"No item at index {self.current_song_index}")
    
    def change_volume(self, value):
        gain = value / 100.0
        self.audio_processor.set_volume(gain)
        print(f"Volume set to {value}%")
    
    def seek_position(self, position):
        self.audio_processor.set_position(position)
        self.current_position = position
        self.time_label.setText(self.format_time(position))
        self.lyrics_widget.update_lyrics_display(position)
        print(f"Seeking to: {position}")
    
    def update_progress(self):
        if self.is_playing and self.audio_processor.audio_data_buffer is not None:
            self.current_position = int((self.audio_processor.position / self.audio_processor.sample_rate) * 1000)
            self.progress_slider.setValue(self.current_position)
            self.time_label.setText(self.format_time(self.current_position))
            self.lyrics_widget.update_lyrics_display(self.current_position)
            
            if self.current_position >= self.total_duration - 100 and self.total_duration > 0:
                print(f"Song ended at position {self.current_position}, duration {self.total_duration}")
                if self.repeat_btn.isChecked():
                    print("Repeating current song")
                    self.seek_position(0)
                    self.audio_processor.start_playback()
                else:
                    print("Moving to next song")
                    self.next_song(auto_next=True)
            self.time_info.setText(f"{self.format_time(self.current_position)} / {self.format_time(self.total_duration)}")
    
    def format_time(self, milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('File')
        
        import_action = QAction('Import Songs', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.playlist_widget.add_songs)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        export_csv_action = QAction('Export Playlist to CSV', self)
        export_csv_action.triggered.connect(self.export_playlist_csv)
        file_menu.addAction(export_csv_action)
        
        export_json_action = QAction('Export Playlist to JSON', self)
        export_json_action.triggered.connect(self.export_playlist_json)
        file_menu.addAction(export_json_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        playback_menu = menubar.addMenu('Playback')
        
        play_pause_action = QAction('Play/Pause', self)
        play_pause_action.setShortcut('Ctrl+Space')
        play_pause_action.triggered.connect(self.toggle_playback)
        playback_menu.addAction(play_pause_action)
        
        next_action = QAction('Next Song', self)
        next_action.setShortcut('Ctrl+Right')
        next_action.triggered.connect(self.next_song)
        playback_menu.addAction(next_action)
        
        prev_action = QAction('Previous Song', self)
        prev_action.setShortcut('Ctrl+Left')
        prev_action.triggered.connect(self.previous_song)
        playback_menu.addAction(prev_action)
        
        playback_menu.addSeparator()
        
        shuffle_action = QAction('Toggle Shuffle', self)
        shuffle_action.setShortcut('Ctrl+S')
        shuffle_action.setCheckable(True)
        shuffle_action.triggered.connect(self.shuffle_btn.click)
        playback_menu.addAction(shuffle_action)
        
        repeat_action = QAction('Toggle Repeat', self)
        repeat_action.setShortcut('Ctrl+R')
        repeat_action.setCheckable(True)
        repeat_action.triggered.connect(self.repeat_btn.click)
        playback_menu.addAction(repeat_action)
        
        view_menu = menubar.addMenu('View')
        
        show_eq_action = QAction('Show/Hide Equalizer', self)
        show_eq_action.setCheckable(True)
        show_eq_action.setChecked(True)
        show_eq_action.triggered.connect(self.toggle_equalizer)
        view_menu.addAction(show_eq_action)
        
        show_lyrics_action = QAction('Show/Hide Lyrics', self)
        show_lyrics_action.setCheckable(True)
        show_lyrics_action.setChecked(True)
        show_lyrics_action.triggered.connect(self.toggle_lyrics)
        view_menu.addAction(show_lyrics_action)

        toggle_theme_action = QAction('Toggle Theme', self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(toggle_theme_action)

        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        status_bar = self.statusBar()
        
        self.student_info = QLabel("Created by: Rizky Maulana Ramdhani - Student ID: F1D022095")
        self.student_info.setStyleSheet("font-size: 11px;")
        status_bar.addWidget(self.student_info)
        
        status_bar.addWidget(QLabel(""), 1)
        
        self.current_song_info = QLabel("No song loaded")
        self.current_song_info.setStyleSheet("font-size: 11px;")
        status_bar.addWidget(self.current_song_info, 2)
        
        self.time_info = QLabel("00:00 / 00:00")
        self.time_info.setStyleSheet("font-size: 11px;")
        status_bar.addPermanentWidget(self.time_info)

    def toggle_equalizer(self):
        for child in self.findChildren(QGroupBox):
            if child.title() == "Equalizer":
                child.setVisible(not child.isVisible())
                break

    def toggle_lyrics(self):
        self.lyrics_widget.setVisible(not self.lyrics_widget.isVisible())

    def show_about(self):
        QMessageBox.about(self, "About Symphoria", 
                        "Symphoria Music Player v1.0\n\n"
                        "Features:\n"
                        "• Audio playback with equalizer\n"
                        "• Playlist management\n"
                        "• Audio visualization\n"
                        "• Lyrics display (.lrc files)\n"
                        "• Export/Import functionality\n\n"
                        "Built with PyQt5 and Python")

    def export_playlist_csv(self):
        current_index = self.playlist_widget.playlist_combo.currentIndex()
        if current_index == 0:
            songs = self.db_manager.get_all_songs()
            filename = "all_songs.csv"
        else:
            playlist_id = self.playlist_widget.playlist_combo.itemData(current_index)
            playlist_name = self.playlist_widget.playlist_combo.currentText()
            songs = self.db_manager.get_songs_in_playlist(playlist_id)
            filename = f"{playlist_name.replace(' ', '_')}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Playlist to CSV", filename, "CSV Files (*.csv)")
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Title', 'Artist', 'Album', 'Duration (seconds)', 
                                'File Path', 'Genre', 'Year', 'Play Count', 'Rating', 'Lyrics Path'])
                    
                    for song in songs:
                        song_id, title, artist, album, duration, file_path_song, genre, year, play_count, rating, lyrics_path = song
                        writer.writerow([title, artist, album, duration, file_path_song, 
                                    genre, year, play_count, rating, lyrics_path])
                
                QMessageBox.information(self, "Export Successful", 
                                    f"Playlist exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export playlist: {str(e)}")

    def export_playlist_json(self):
        current_index = self.playlist_widget.playlist_combo.currentIndex()
        if current_index == 0:
            songs = self.db_manager.get_all_songs()
            filename = "all_songs.json"
            playlist_name = "All Songs"
        else:
            playlist_id = self.playlist_widget.playlist_combo.itemData(current_index)
            playlist_name = self.playlist_widget.playlist_combo.currentText()
            songs = self.db_manager.get_songs_in_playlist(playlist_id)
            filename = f"{playlist_name.replace(' ', '_')}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Playlist to JSON", filename, "JSON Files (*.json)")
        
        if file_path:
            try:
                playlist_data = {
                    "playlist_name": playlist_name,
                    "export_date": datetime.now().isoformat(),
                    "total_songs": len(songs),
                    "songs": []
                }
                
                for song in songs:
                    song_id, title, artist, album, duration, file_path_song, genre, year, play_count, rating, lyrics_path = song
                    song_data = {
                        "id": song_id,
                        "title": title,
                        "artist": artist,
                        "album": album,
                        "duration": duration,
                        "file_path": file_path_song,
                        "genre": genre,
                        "year": year,
                        "play_count": play_count,
                        "rating": rating,
                        "lyrics_path": lyrics_path
                    }
                    playlist_data["songs"].append(song_data)
                
                with open(file_path, 'w', encoding='utf-8') as jsonfile:
                    json.dump(playlist_data, jsonfile, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Export Successful", 
                                    f"Playlist exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export playlist: {str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Symphoria Music Player")
        
    app.setWindowIcon(QIcon())
        
    player = MusicPlayer()
    player.show()
        
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()