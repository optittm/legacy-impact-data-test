import pickle
import os

from interfaces.Database.EmbeddingDbI import EmbeddingDbI
from sqlalchemy import Column, Integer, String, BLOB, create_engine, select, insert, update
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Embeddings1(Base):
    __tablename__ = 'embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String)
    function_name = Column(String)
    embedding = Column(BLOB)

class EmbeddingT5(EmbeddingDbI):
    def __init__(self) -> None:
        engine = create_engine('sqlite:///Embeddings1.db')
        Base.metadata.create_all(engine)
        self.conn = engine.connect()
    
    def get_embedding(self, file_path, function_name):
        """Retrieves an embedding from the database for the given file path and function name.
        
        Args:
            file_path (str): The file path associated with the embedding.
            function_name (str): The name of the function associated with the embedding.
        
        Returns:
            bytes or None: The embedding data if found, otherwise None."""
        stmt = select(Embeddings1.embedding).where((Embeddings1.file_path == file_path) & (Embeddings1.function_name == function_name))
        results = self.conn.execute(stmt)
        self.conn.commit()
        row = results.fetchone()
        if row:
            return pickle.loads(row[0])
        return None
    
    def save_embedding(self, file_path, function_name, embedding):
        """Saves an embedding to the database.
        
        Args:
            file_path (str): The file path associated with the embedding.
            function_name (str): The name of the function associated with the embedding.
            embedding (bytes): The embedding data to be saved.
        
        This method first checks if an embedding already exists in the database for the given file_path and function_name.
        If an existing embedding is found, it updates the embedding data.
        If no existing embedding is found, it inserts a new record into the database."""
        new = insert(Embeddings1).values(file_path=file_path, function_name=function_name, embedding=pickle.dumps(embedding))
        old = update(Embeddings1).where((Embeddings1.file_path == file_path) & (Embeddings1.function_name == function_name)).values(embedding=pickle.dumps(embedding))
        sel = self.conn.execute(select(Embeddings1).where((Embeddings1.file_path == file_path) & (Embeddings1.function_name == function_name)))
        if sel.first() is None:
            self.conn.execute(new)
        else:
            self.conn.execute(old)
    
    def clean(self):
        """Closes the database connection and removes the SQLite database file.
        
        This method is used to clean up the EmbeddingT5 class instance by closing the database connection and deleting the SQLite database file.
        It should be called when the EmbeddingT5 instance is no longer needed to free up system resources."""
        self.conn.close()
        os.remove("./Embeddings1.db")