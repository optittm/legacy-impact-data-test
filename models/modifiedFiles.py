from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class ModifiedFiles(Base) :
    __tablename__ = "modifiedFiles"
    
    id = Column(Integer, primary_key=True)
    sha = Column(String)
    filename = Column(String)
    status = Column(String)
    patch = Column(String)
    additions = Column(Integer)
    deletions = Column(Integer)
    changes = Column(Integer)
    pullRequestId = Column(Integer, ForeignKey("pullRequest.id"))
    
    def __init__(self, id: int, sha: str, filename: str, status: str, patch: str, additions: int, deletions: int, changes: int, pullRequestId: int):
        self.id = id
        self.sha = sha
        self.filename = filename
        self.status = status
        self.patch = patch
        self.additions = additions
        self.deletions = deletions
        self.changes = changes
        self.pullRequestId = pullRequestId
    
    def get_modified_files_data(self):
        return {
            "id": self.id,
            "sha": self.sha,
            "filename": self.filename,
            "status": self.status,
            "patch": self.patch,
            "additions": self.additions,
            "deletions": self.deletions,
            "changes": self.changes,
            "pullRequestId": self.pullRequestId
        }