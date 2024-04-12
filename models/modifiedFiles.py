from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class ModifiedFiles(Base) :
    __tablename__ = "modifiedFiles"
    
    gitFileId = Column(Integer, ForeignKey("gitFile.id"), primary_key=True)
    pullRequestId = Column(Integer, ForeignKey("pullRequest.id"), primary_key=True)
    status = Column(String)
    patch = Column(String)
    additions = Column(Integer)
    deletions = Column(Integer)
    changes = Column(Integer)