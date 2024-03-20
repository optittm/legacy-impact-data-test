from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class Issue(Base) :
    __tablename__ = "issue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    githubId = Column(Integer)
    title = Column(String)
    body = Column(String)
    state = Column(String)
    repositoryId = Column(Integer, ForeignKey("repository.id"))