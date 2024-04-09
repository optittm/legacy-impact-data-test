from sqlalchemy import Column, Integer, String
from models.db import Base

class Repository(Base) :
    __tablename__ = "repository"
    
    id = Column(Integer, primary_key=True)
    fullName = Column(String)
    description = Column(String)
    language = Column(String)
    stars = Column(Integer)