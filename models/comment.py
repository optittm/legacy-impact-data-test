from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class Comment(Base) :
    __tablename__ = "comment"
    
    id = Column(Integer, primary_key=True)
    body = Column(String)
    issueId = Column(Integer, ForeignKey("issue.id"))