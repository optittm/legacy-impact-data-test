from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class ModifiedFiles(Base) :
    __tablename__ = "modifiedFiles"
    
    sha = Column(String, primary_key=True)
    filename = Column(String)
    status = Column(String)
    patch = Column(String)
    additions = Column(Integer)
    deletions = Column(Integer)
    changes = Column(Integer)
    pullRequestId = Column(Integer, ForeignKey("pullRequest.id"))
    
    def __init__(self, sha: str, filename: str, status: str, patch: str, additions: int, deletions: int, changes: int, pullRequestId: int):
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
            "sha": self.sha,
            "filename": self.filename,
            "status": self.status,
            "patch": self.patch,
            "additions": self.additions,
            "deletions": self.deletions,
            "changes": self.changes,
            "pullRequestId": self.pullRequestId
        }