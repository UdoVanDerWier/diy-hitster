import sqlite3
from cryptography.fernet import Fernet

class Database() :
    def __init__(self, path: str="./database/database.db") : 
        self.path = path
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor() 

    def encrypt(self, text: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, text: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()

    def init_tables(self) : 
        with self.conn as conn :
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    spotify_id TEXT PRIMARY KEY,
                    refresh_token TEXT,
                    api_key TEXT
                );
            """)
            conn.commit()

    def add_user(self, spotify_id: str, refresh_token: str, api_key: str):
        encrypted_refresh = self.encrypt(refresh_token)
        encrypted_key = self.encrypt(api_key)

        with self.connection as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (spotify_id, refresh_token, api_key)
                VALUES (?, ?, ?);
            """, (spotify_id, encrypted_refresh, encrypted_key))

    def get_user(self, spotify_id: str):
        with self.connection as conn:
            cur = conn.execute("""
                SELECT spotify_id, refresh_token, api_key
                FROM users WHERE spotify_id = ?;
            """, (spotify_id,))
            row = cur.fetchone()

            if not row:
                return None

            spotify_id, enc_refresh, enc_key = row
            return {
                "spotify_id": spotify_id,
                "refresh_token": self.decrypt(enc_refresh),
                "api_key": self.decrypt(enc_key)
            }
