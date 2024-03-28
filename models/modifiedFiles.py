from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class ModifiedFiles(Base) :
    __tablename__ = "modifiedFiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sha = Column(String)
    filename = Column(String)
    status = Column(String)
    patch = Column(String)
    additions = Column(Integer)
    deletions = Column(Integer)
    changes = Column(Integer)
    pullRequestId = Column(Integer, ForeignKey("pullRequest.id"))