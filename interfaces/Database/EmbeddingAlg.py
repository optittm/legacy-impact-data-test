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
        stmt = select(Embeddings2.embedding).where(Embeddings2.file_path == file_path)
        results = self.conn.execute(stmt)
        self.conn.commit()
        row = results.fetchone()
        if row:
            return pickle.loads(row[0])
        return None
    
    def save_embedding(self, file_path, embedding, function_name = None):
        new = insert(Embeddings2).values(file_path=file_path, embedding=pickle.dumps(embedding))
        old = update(Embeddings2).where(Embeddings2.file_path == file_path).values(embedding=pickle.dumps(embedding))
        sel = self.conn.execute(select(Embeddings2).where(Embeddings2.file_path == file_path))
        if sel.first() is None:
            self.conn.execute(new)
        else:
            self.conn.execute(old)
    
    def clean(self):
        self.conn.close()
        os.remove("./Embeddings2.db")