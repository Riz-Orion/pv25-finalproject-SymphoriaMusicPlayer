from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QListWidget, QPushButton, QFileDialog, QInputDialog, QMenu, QMessageBox, QLabel, QListWidgetItem, QAction, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSignal
from mutagen import File
import os
from PyQt5.QtGui import QPixmap, QIcon

class SongItemWidget(QWidget):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(50, 50)
        self.cover_label.setStyleSheet("border: 1px solid #555555;")
        self.load_cover()
        layout.addWidget(self.cover_label)
        
        info_layout = QVBoxLayout()
        self.title_label = QLabel("Unknown Title")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;background: transparent;")
        info_layout.addWidget(self.title_label)
        
        self.artist_label = QLabel("Unknown Artist")
        self.artist_label.setStyleSheet("font-size: 12px; background: transparent;")
        info_layout.addWidget(self.artist_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        self.load_metadata()
    
    def load_cover(self):
        try:
            audio_file = File(self.file_path)
            cover_data = None
            if audio_file:
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
                    return
            self.load_default_cover()
        except Exception as e:
            print(f"Error loading cover: {e}")
            self.load_default_cover()
    
    def load_default_cover(self):
        default_path = "asset/song_cover.png"
        if os.path.exists(default_path):
            default_pixmap = QPixmap(default_path)
            scaled_pixmap = default_pixmap.scaled(
                self.cover_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.cover_label.setPixmap(scaled_pixmap)
        else:
            self.cover_label.clear()
    
    def load_metadata(self):
        try:
            audio_file = File(self.file_path)
            if audio_file:
                title = str(audio_file.get('TIT2', [os.path.basename(self.file_path)])[0])
                artist = str(audio_file.get('TPE1', ['Unknown Artist'])[0])
                self.title_label.setText(title)
                self.artist_label.setText(artist)
        except Exception as e:
            print(f"Error loading metadata: {e}")
            self.title_label.setText(os.path.basename(self.file_path))
            self.artist_label.setText("Unknown Artist")
    
    def get_title(self):
        return self.title_label.text()

class PlaylistWidget(QWidget):
    song_selected = pyqtSignal(str, int)
    
    def __init__(self, db_manager, lyrics_widget=None):
        super().__init__()
        self.db_manager = db_manager
        self.lyrics_widget = lyrics_widget
        self.current_playlist_id = None
        self.songs_data = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)

        self.playlist_combo = QComboBox()
        self.playlist_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #555555;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::item {
                padding: 5px;
            }
        """)
        self.playlist_combo.addItem("All Songs")
        playlists = self.db_manager.get_all_playlists()
        for pid, name in playlists:
            self.playlist_combo.addItem(name, pid)
        self.playlist_combo.currentIndexChanged.connect(self.load_songs)
        layout.addWidget(self.playlist_combo)

        # Modifikasi untuk scrolling yang lebih halus
        self.playlist_list = QListWidget()
        self.playlist_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)  # Aktifkan scrolling per piksel
        self.playlist_list.verticalScrollBar().setSingleStep(10)  # Kecepatan scroll per langkah
        self.playlist_list.setFocusPolicy(Qt.StrongFocus)  # Pastikan menerima fokus untuk mouse wheel
        self.playlist_list.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.playlist_list.setSelectionMode(QListWidget.SingleSelection)
        self.playlist_list.itemDoubleClicked.connect(self.play_selected)
        self.playlist_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.playlist_list)

        button_layout = QVBoxLayout()
        
        main_buttons = QHBoxLayout()
        
        self.add_song_btn = QPushButton()
        self.add_song_btn.setFixedSize(40, 40)
        self.add_song_btn.setToolTip("Add new songs to library")
        self.add_song_btn.clicked.connect(self.add_songs)
        self.add_song_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/add.png);
            }
        """)
        main_buttons.addWidget(self.add_song_btn)
        
        self.new_playlist_btn = QPushButton()
        self.new_playlist_btn.setFixedSize(40, 40)
        self.new_playlist_btn.setToolTip("Create a new playlist")
        self.new_playlist_btn.clicked.connect(self.create_playlist)
        self.new_playlist_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/new_playlist.png);
            }
        """)
        main_buttons.addWidget(self.new_playlist_btn)
        
        self.delete_playlist_btn = QPushButton()
        self.delete_playlist_btn.setFixedSize(40, 40)
        self.delete_playlist_btn.setToolTip("Delete selected playlist")
        self.delete_playlist_btn.clicked.connect(self.delete_playlist)
        self.delete_playlist_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/remove_playlist.png);
            }
        """)
        main_buttons.addWidget(self.delete_playlist_btn)
        
        button_layout.addLayout(main_buttons)
        
        song_buttons = QHBoxLayout()
        
        self.remove_song_btn = QPushButton()
        self.remove_song_btn.setFixedSize(40, 40)
        self.remove_song_btn.setToolTip("Remove selected song")
        self.remove_song_btn.clicked.connect(self.remove_song)
        self.remove_song_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/remove.png);
            }
        """)
        song_buttons.addWidget(self.remove_song_btn)
        
        self.sort_btn = QPushButton()
        self.sort_btn.setFixedSize(40, 40)
        self.sort_btn.setToolTip("Sort songs by title")
        self.sort_btn.clicked.connect(self.sort_by_title)
        self.sort_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/sort.png);
            }
        """)
        song_buttons.addWidget(self.sort_btn)
        
        self.sort_artist_btn = QPushButton()
        self.sort_artist_btn.setFixedSize(40, 40)
        self.sort_artist_btn.setToolTip("Sort songs by artist")
        self.sort_artist_btn.clicked.connect(self.sort_by_artist)
        self.sort_artist_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/sort_artist.png);
            }
        """)
        song_buttons.addWidget(self.sort_artist_btn)
        
        self.add_lyrics_btn = QPushButton()
        self.add_lyrics_btn.setFixedSize(40, 40)
        self.add_lyrics_btn.setToolTip("Add lyrics file for selected song")
        self.add_lyrics_btn.clicked.connect(self.add_lyrics)
        self.add_lyrics_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                image: url(asset/icons/lyric.png);
            }
        """)
        song_buttons.addWidget(self.add_lyrics_btn)
        
        button_layout.addLayout(song_buttons)
        layout.addLayout(button_layout)
        
        self.load_songs()
    
    def load_songs(self):
        self.playlist_list.clear()
        self.songs_data.clear()
        current_index = self.playlist_combo.currentIndex()
        
        if current_index == 0:
            self.current_playlist_id = None
            songs = self.db_manager.get_all_songs()
        else:
            self.current_playlist_id = self.playlist_combo.itemData(current_index)
            songs = self.db_manager.get_songs_in_playlist(self.current_playlist_id)
        
        print(f"Loading songs: {len(songs)} items found")
        for song in songs:
            print(f"Song data: {song}")
            song_id, title, artist, album, duration, file_path, genre, year, play_count, rating, lyrics_path = song
            
            item_widget = SongItemWidget(file_path)
            
            item = QListWidgetItem(self.playlist_list)
            item.setData(Qt.UserRole, file_path)
            item.setData(Qt.UserRole + 1, song_id)
            item.setSizeHint(item_widget.sizeHint())
            
            self.playlist_list.setItemWidget(item, item_widget)
            
            self.songs_data.append({
                'item': item,
                'widget': item_widget,
                'file_path': file_path,
                'song_id': song_id,
                'title': title
            })

        current_index = self.playlist_combo.currentIndex()
        self.delete_playlist_btn.setEnabled(current_index > 0)
    
    def sort_by_title(self):
        try:
            print("Starting sort by title...")
            if not self.songs_data:
                print("No songs to sort")
                return
            
            self.songs_data.sort(key=lambda x: x['title'].lower() if x['title'] else "")
            print(f"Sorted {len(self.songs_data)} songs")

            temp_songs_data = self.songs_data.copy()
            self.playlist_list.clear()
            self.songs_data.clear()
            print("Playlist cleared")

            for i, song_data in enumerate(temp_songs_data):
                file_path = song_data['file_path']
                song_id = song_data['song_id']
                title = song_data['title']
                
                new_item_widget = SongItemWidget(file_path)
                
                new_item = QListWidgetItem(self.playlist_list)
                new_item.setData(Qt.UserRole, file_path)
                new_item.setData(Qt.UserRole + 1, song_id)
                new_item.setSizeHint(new_item_widget.sizeHint())
                
                self.playlist_list.setItemWidget(new_item, new_item_widget)
                
                self.songs_data.append({
                    'item': new_item,
                    'widget': new_item_widget,
                    'file_path': file_path,
                    'song_id': song_id,
                    'title': title
                })
                print(f"Added item at index {i}: {file_path}, title: {title}")
            
            print("Sorting completed successfully")
        except Exception as e:
            print(f"Error during sorting: {e}")
            raise
    
    def add_songs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Songs", "", "Audio Files (*.mp3 *.wav)")
        if files:
            for file_path in files:
                print(f"Adding song: {file_path}")
                self.db_manager.add_song(file_path)
            self.load_songs()
    
    def add_lyrics(self):
        item = self.playlist_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a song to add lyrics.")
            return
        
        song_id = item.data(Qt.UserRole + 1)
        file_path = item.data(Qt.UserRole)
        if not song_id:
            print("No song ID found for the selected item")
            return
        
        lyrics_file, _ = QFileDialog.getOpenFileName(
            self, "Select Lyrics File", "", "Lyrics Files (*.lrc)"
        )
        if lyrics_file:
            if self.lyrics_widget.load_lyrics_file(lyrics_file):
                self.db_manager.assign_lyrics(song_id, lyrics_file)
                QMessageBox.information(self, "Success", f"Lyrics assigned to {os.path.basename(file_path)}")
            else:
                QMessageBox.critical(self, "Error", "Failed to load lyrics file.")
    
    def create_playlist(self):
        name, ok = QInputDialog.getText(self, "New Playlist", "Enter playlist name:")
        if ok and name:
            playlist_id = self.db_manager.create_playlist(name)
            if playlist_id:
                self.playlist_combo.addItem(name, playlist_id)
                self.playlist_combo.setCurrentIndex(self.playlist_combo.count() - 1)
                QMessageBox.information(self, "Success", f"Playlist '{name}' created successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to create playlist.")
    
    def play_selected(self, item):
        file_path = item.data(Qt.UserRole)
        if file_path:
            index = self.playlist_list.row(item)
            print(f"Emitting song_selected: file_path={file_path}, index={index}")
            self.song_selected.emit(file_path, index)
    
    def show_context_menu(self, position):
        item = self.playlist_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        add_to_playlist_action = QAction("Add to Playlist", self)
        add_to_playlist_action.triggered.connect(lambda: self.add_to_playlist(item))
        menu.addAction(add_to_playlist_action)
        
        add_lyrics_action = QAction("Add Lyrics", self)
        add_lyrics_action.triggered.connect(lambda: self.add_lyrics())
        menu.addAction(add_lyrics_action)
        
        remove_action = QAction("Remove Song", self)
        remove_action.triggered.connect(lambda: self.remove_song(item))
        menu.addAction(remove_action)
        
        menu.exec_(self.playlist_list.mapToGlobal(position))
    
    def add_to_playlist(self, item):
        song_id = item.data(Qt.UserRole + 1)
        if not song_id:
            return
        
        playlists = self.db_manager.get_all_playlists()
        if not playlists:
            QMessageBox.information(self, "No Playlists", "No playlists available. Create a playlist first.")
            return
        
        playlist_names = [name for _, name in playlists]
        playlist_id_map = {name: pid for pid, name in playlists}
        name, ok = QInputDialog.getItem(self, "Add to Playlist", "Select playlist:", playlist_names, 0, False)
        
        if ok and name:
            playlist_id = playlist_id_map[name]
            position = len(self.db_manager.get_songs_in_playlist(playlist_id)) if playlist_id else 0
            self.db_manager.add_song_to_playlist(playlist_id, song_id, position)
            
            if self.current_playlist_id == playlist_id:
                self.load_songs()
    
    def remove_song(self, item=None):
        if not item:
            item = self.playlist_list.currentItem()
            if not item:
                QMessageBox.warning(self, "No Selection", "Please select a song to remove.")
                return
        
        song_id = item.data(Qt.UserRole + 1)
        if not song_id:
            print("No song ID found for the selected item")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Removal", "Are you sure you want to remove this song?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.current_playlist_id:
                self.db_manager.remove_song_from_playlist(self.current_playlist_id, song_id)
            else:
                self.db_manager.remove_song(song_id)
            
            self.load_songs()
            print(f"Song with ID {song_id} removed")

    def delete_playlist(self):
        current_index = self.playlist_combo.currentIndex()
        if current_index == 0:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete 'All Songs' view.")
            return
    
        playlist_id = self.playlist_combo.itemData(current_index)
        playlist_name = self.playlist_combo.currentText()
    
        if not playlist_id:
            QMessageBox.warning(self, "No Selection", "Please select a playlist to delete.")
            return
    
        reply = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete playlist '{playlist_name}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
    
        if reply == QMessageBox.Yes:
            if self.db_manager.delete_playlist(playlist_id):
                self.playlist_combo.removeItem(current_index)
                self.playlist_combo.setCurrentIndex(0)
                QMessageBox.information(self, "Success", f"Playlist '{playlist_name}' deleted successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete playlist.")

    def sort_by_artist(self):
        try:
            print("Starting sort by artist...")
            if not self.songs_data:
                print("No songs to sort")
                return
        
            self.songs_data.sort(key=lambda x: x['widget'].artist_label.text().lower())
            print(f"Sorted {len(self.songs_data)} songs by artist")

            temp_songs_data = self.songs_data.copy()
            self.playlist_list.clear()
            self.songs_data.clear()

            for song_data in temp_songs_data:
                file_path = song_data['file_path']
                song_id = song_data['song_id']
                title = song_data['title']
            
                new_item_widget = SongItemWidget(file_path)
            
                new_item = QListWidgetItem(self.playlist_list)
                new_item.setData(Qt.UserRole, file_path)
                new_item.setData(Qt.UserRole + 1, song_id)
                new_item.setSizeHint(new_item_widget.sizeHint())
            
                self.playlist_list.setItemWidget(new_item, new_item_widget)
            
                self.songs_data.append({
                    'item': new_item,
                    'widget': new_item_widget,
                    'file_path': file_path,
                    'song_id': song_id,
                    'title': title
                })
        
            print("Sorting by artist completed successfully")
        except Exception as e:
            print(f"Error during sorting by artist: {e}")