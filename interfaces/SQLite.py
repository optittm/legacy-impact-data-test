from __future__ import annotations
from interfaces.DbInterface import DbInterface
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.comment import Comment
from sqlalchemy import update

class SQLite(DbInterface):
    
    def __init__(self, session):
        self.session = session
    
    def database_insert(self, data: Repository | Issue | PullRequest | ModifiedFiles | Comment):
        """Inserts the given data object into the database.
        
        Parameters:
            data (Repository | Issue | PullRequest | ModifiedFiles | Comment): The data object to insert.
        
        Commits the change to the database."""
    
        self.session.add(data)
        self.session.commit()
        return data.id
    
    def database_insert_many(self, data: list[Repository | Issue | PullRequest | ModifiedFiles | Comment]):
        """Inserts the given list of data objects into the database.
        
        Parameters:
            data (list[Repository | Issue | PullRequest | ModifiedFiles | Comment]): 
                The list of data objects to insert.
        
        Commits the changes to the database."""
    
        self.session.add_all(data)
        self.session.commit()
        return [data.id for data in data]
    
    def database_update_issueId_pullRequest(self, pullId: int, issueId: int):
        """Updates the issueId field of a PullRequest in the database.
    
        Parameters:
            pullId (int): The GitHub ID of the pull request to update.
            issueId (int): The new issue ID to set for the pull request."""
    
        self.session.query(PullRequest).filter(PullRequest.githubId == pullId).update({"issueId": issueId})
        self.session.commit()