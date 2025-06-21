import sqlite3
from mutagen import File
import os
from PyQt5.QtCore import QDateTime, Qt

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('music_library.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                artist TEXT,
                album TEXT,
                duration INTEGER,
                file_path TEXT UNIQUE,
                genre TEXT,
                year INTEGER,
                play_count INTEGER DEFAULT 0,
                rating INTEGER DEFAULT 0,
                lyrics_path TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY,
                name TEXT,
                created_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id INTEGER,
                song_id INTEGER,
                position INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                FOREIGN KEY (song_id) REFERENCES songs (id)
            )
        ''')
        self.conn.commit()
    
    def add_song(self, file_path):
        cursor = self.conn.cursor()
        try:
            print(f"Processing file: {file_path}")
            audio_file = File(file_path)
            title = os.path.basename(file_path)
            artist = "Unknown Artist"
            album = "Unknown Album"
            duration = 0
            genre = None
            year = None
        
            if audio_file:
                title = str(audio_file.get('TIT2', [title])[0]) if audio_file.get('TIT2') else title
                artist = str(audio_file.get('TPE1', [artist])[0]) if audio_file.get('TPE1') else artist
                album = str(audio_file.get('TALB', [album])[0]) if audio_file.get('TALB') else album
                duration = int(audio_file.info.length) if audio_file.info else 0
                genre = str(audio_file.get('TCON', [None])[0]) if audio_file.get('TCON') else None
            
                if audio_file.get('TDRC'):
                    tdrc = audio_file.get('TDRC')[0]
                    print(f"TDRC value: {tdrc}, type: {type(tdrc)}")
                    try:
                        year_str = str(tdrc)
                        year = int(year_str.split('-')[0]) if year_str else None
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing year from TDRC: {e}")
                        year = None
        
            song_data = (title, artist, album, duration, file_path, genre, year, None)
            print(f"Song data to insert: {song_data}")
            cursor.execute('''
                INSERT OR REPLACE INTO songs 
                (title, artist, album, duration, file_path, genre, year, lyrics_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', song_data)
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
    
    def assign_lyrics(self, song_id, lyrics_path):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE songs SET lyrics_path = ? WHERE id = ?
            ''', (lyrics_path, song_id))
            self.conn.commit()
            print(f"Assigned lyrics {lyrics_path} to song ID {song_id}")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
    
    def get_all_songs(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM songs ORDER BY artist, album, title')
        return cursor.fetchall()
    
    def update_play_count(self, song_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE songs SET play_count = play_count + 1 WHERE id = ?', (song_id,))
        self.conn.commit()
    
    def create_playlist(self, name):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO playlists (name, created_date) VALUES (?, ?)',
                         (name, QDateTime.currentDateTime().toString(Qt.ISODate)))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
    
    def get_all_playlists(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name FROM playlists ORDER BY name')
        return cursor.fetchall()
    
    def add_song_to_playlist(self, playlist_id, song_id, position):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO playlist_songs (playlist_id, song_id, position) VALUES (?, ?, ?)',
                         (playlist_id, song_id, position))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
    
    def get_songs_in_playlist(self, playlist_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.* FROM songs s
            JOIN playlist_songs ps ON s.id = ps.song_id
            WHERE ps.playlist_id = ?
            ORDER BY ps.position
        ''', (playlist_id,))
        return cursor.fetchall()
    
    def remove_song(self, song_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('DELETE FROM playlist_songs WHERE song_id = ?', (song_id,))
            cursor.execute('DELETE FROM songs WHERE id = ?', (song_id,))
            self.conn.commit()
            print(f"Song ID {song_id} removed from database")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
    
    def remove_song_from_playlist(self, playlist_id, song_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?', 
                         (playlist_id, song_id))
            self.conn.commit()
            print(f"Song ID {song_id} removed from playlist ID {playlist_id}")
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def delete_playlist(self, playlist_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('DELETE FROM playlist_songs WHERE playlist_id = ?', (playlist_id,))
            cursor.execute('DELETE FROM playlists WHERE id = ?', (playlist_id,))
            self.conn.commit()
            print(f"Playlist ID {playlist_id} deleted")
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False