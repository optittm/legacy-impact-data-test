import pickle
import sqlite3

from interfaces.Database.EmbeddingDbI import EmbeddingDbI

class GitEmbedding(EmbeddingDbI):
    def __init__(self) -> None:
        self.conn = sqlite3.connect('Embeddings.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            function_name TEXT,
            embedding BLOB
            )''')
        self.conn.commit()
    def get_embedding(self, file_path, function_name):
        self.c.execute('SELECT embedding FROM embeddings WHERE file_path = ? AND function_name = ?', (file_path, function_name))
        row = self.c.fetchone()
        if row:
            return pickle.loads(row[0])
        return None

    def save_embedding(self, file_path, function_name, embedding):
        self.c.execute('INSERT OR REPLACE INTO embeddings (file_path, function_name, embedding) VALUES (?, ?, ?)', (file_path, function_name, pickle.dumps(embedding)))
        self.conn.commit()