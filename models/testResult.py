from sqlalchemy import Column, ForeignKey, Integer, String
from models.db import Base

class TestResult(Base) :
    __tablename__ = "testResult"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    issueId = Column(Integer, ForeignKey("issue.id"))
    results_array = Column(String)