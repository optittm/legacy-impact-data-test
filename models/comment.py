from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class Comment(Base) :
    __tablename__ = "comment"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    githubId = Column(Integer)
    body = Column(String)
    issueId = Column(Integer, ForeignKey("issue.id"))