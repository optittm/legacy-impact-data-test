from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class Comment(Base) :
    __tablename__ = "comment"
    
    id = Column(Integer, primary_key=True)
    body = Column(String)
    issueId = Column(Integer, ForeignKey("issue.id"))
    
    def __init__(self, id: int, body: str, issueId: int):
        self.id = id
        self.body = body
        self.issueId = issueId
    
    def get_comment_data(self):
        return{
            "id": self.id,
            "body": self.body,
            "issueId": self.issueId
        }