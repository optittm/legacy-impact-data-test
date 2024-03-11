from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from models.db import Base

class PullRequest(Base) :
    __tablename__ = "pullRequest"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(String)
    state = Column(String)
    mergedAt = Column(DateTime)
    shaBase = Column(String)
    issueId = Column(Integer, ForeignKey("issue.id"))
    
    def __init__(self, id: int, title: str, body: str, state: str, mergedAt: str, shaBase: str, issueId: int):
        self.id = id
        self.title = title
        self.body = body
        self.state = state
        self.mergedAt = mergedAt
        self.shaBase = shaBase
        self.issueId = issueId
    
    def get_pull_request_data(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "mergedAt": self.mergedAt,
            "shaBase": self.shaBase,
            "issueId": self.issueId
        }