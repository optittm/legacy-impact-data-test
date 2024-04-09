from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from models.db import Base

class PullRequest(Base) :
    __tablename__ = "pullRequest"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    githubId = Column(Integer)
    title = Column(String)
    body = Column(String)
    state = Column(String)
    shaBase = Column(String)
    issueId = Column(Integer, ForeignKey("issue.id"))