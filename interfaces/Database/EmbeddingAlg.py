import pickle
import sqlite3
import os

from interfaces.Database.EmbeddingDbI import EmbeddingDbI

class EmbeddingAlg(EmbeddingDbI):
    def __init__(self) -> None:
        self.conn = sqlite3.connect('Embeddings.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            embedding BLOB
            )''')
        self.conn.commit()
    
    def get_embedding(self, file_path, function_name = None):
        self.c.execute('SELECT embedding FROM embeddings WHERE file_path = ?', (file_path,))
        row = self.c.fetchone()
        if row:
            return pickle.loads(row[0])
        return None
    
    def save_embedding(self, file_path, embedding, function_name = None):
        self.c.execute('INSERT OR REPLACE INTO Embeddings (file_path, embedding) VALUES (?, ?)', (file_path, pickle.dumps(embedding)))
        self.conn.commit()
    
    def clean(self):
        self.conn.close()
        os.remove("./Embeddings.db")