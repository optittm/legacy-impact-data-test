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
        stmt = select(Embeddings1.embedding).where(Embeddings1.file_path == file_path and Embeddings1.function_name == function_name)
        results = self.conn.execute(stmt)
        self.conn.commit()
        row = results.fetchone()
        if row:
            return pickle.loads(row[0])
        return None
    
    def save_embedding(self, file_path, function_name, embedding):
        new = insert(Embeddings1).values(file_path=file_path, function_name=function_name, embedding=pickle.dumps(embedding))
        old = update(Embeddings1).where(Embeddings1.file_path == file_path and Embeddings1.function_name == function_name).values(embedding=pickle.dumps(embedding))
        sel = self.conn.execute(select(Embeddings1).where(Embeddings1.file_path == file_path and Embeddings1.function_name == function_name))
        if sel.first() is None:
            self.conn.execute(new)
        else:
            self.conn.execute(old)
    
    def clean(self):
        self.conn.close()
        os.remove("./Embeddings1.db")