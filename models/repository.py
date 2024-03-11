from sqlalchemy import Column, Integer, String
from models.db import Base

class Repository(Base) :
    __tablename__ = "repository"
    
    id = Column(Integer, primary_key=True)
    fullName = Column(String)
    description = Column(String)
    language = Column(String)
    stars = Column(Integer)
    
    def __init__(self, id: int, fullName: str, description: str, language: str, stars: int):
        self.id = id
        self.fullName = fullName
        self.description = description
        self.language = language
        self.stars = stars
    
    def get_repository_data(self):
        return {
            "id": self.id,
            "fullName": self.fullName,
            "description": self.description,
            "language": self.language,
            "stars": self.stars
        }