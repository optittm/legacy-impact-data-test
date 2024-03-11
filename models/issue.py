from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class Issue(Base) :
    __tablename__ = "issue"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(String)
    state = Column(String)
    repositoryId = Column(Integer, ForeignKey("repository.id"))
    
    def __init__(self, id: int, title: str, body: str, state: str, repositoryId: int):
        self.id = id
        self.title = title
        self.body = body
        self.state = state
        self.repositoryId = repositoryId
    
    def get_issue_data(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "repositoryId": self.repositoryId
        }