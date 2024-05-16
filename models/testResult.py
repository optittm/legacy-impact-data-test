from sqlalchemy import Column, ForeignKey, Integer
from models.db import Base

class TestResult(Base) :
    __tablename__ = "testResult"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Integer)
    issueId = Column(Integer, ForeignKey("issue.id"))
    gitFileId = Column(Integer, ForeignKey("gitFile.id"))