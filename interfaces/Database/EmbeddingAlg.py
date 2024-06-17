import pickle
import os

from interfaces.Database.EmbeddingDbI import EmbeddingDbI
from sqlalchemy import Column, Integer, String, BLOB, create_engine, select, insert, update
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Embeddings2(Base):
    __tablename__ = 'embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String)
    embedding = Column(BLOB)

class EmbeddingAlg(EmbeddingDbI):
    def __init__(self) -> None:
        engine = create_engine('sqlite:///Embeddings2.db')
        Base.metadata.create_all(engine)
        self.conn = engine.connect()
    
    def get_embedding(self, file_path, function_name = None):
        """Retrieves an embedding from the database for the given file path and function name.
        
        Args:
            file_path (str): The file path associated with the embedding.
        
        Returns:
            bytes or None: The embedding data if found, otherwise None."""
        stmt = select(Embeddings2.embedding).where(Embeddings2.file_path == file_path)
        results = self.conn.execute(stmt)
        self.conn.commit()
        row = results.fetchone()
        if row:
            return pickle.loads(row[0])
        return None
    
    def save_embedding(self, file_path, embedding, function_name = None):
        """Saves an embedding to the database.
        
        Args:
            file_path (str): The file path associated with the embedding.
            embedding (bytes): The embedding data to be saved.
        
        This method first checks if an embedding already exists in the database for the given file_path.
        If an existing embedding is found, it updates the embedding data.
        If no existing embedding is found, it inserts a new record into the database."""
        new = insert(Embeddings2).values(file_path=file_path, embedding=pickle.dumps(embedding))
        old = update(Embeddings2).where(Embeddings2.file_path == file_path).values(embedding=pickle.dumps(embedding))
        sel = self.conn.execute(select(Embeddings2).where(Embeddings2.file_path == file_path))
        if sel.first() is None:
            self.conn.execute(new)
        else:
            self.conn.execute(old)
    
    def clean(self):
        """Closes the database connection and removes the SQLite database file.
        
        This method is used to clean up the EmbeddingAlg class instance by closing the database connection and deleting the SQLite database file.
        It should be called when the EmbeddingT5 instance is no longer needed to free up system resources."""
        self.conn.close()
        os.remove("./Embeddings2.db")