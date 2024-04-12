from __future__ import annotations
import logging
from interfaces.DbInterface import DbInterface
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.gitFile import GitFile
from models.comment import Comment
from sqlalchemy import update, select

class SQLite(DbInterface):
    
    def __init__(self, session):
        self.session = session
        self.missingFileId = 0
    
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
        if not all(isinstance(x, ModifiedFiles) for x in data):
            return [data.id for data in data]
    
    def database_update_issueId_pullRequest(self, pullId: int, issueId: int):
        """Updates the issueId field of a PullRequest in the database.
    
        Parameters:
            pullId (int): The GitHub ID of the pull request to update.
            issueId (int): The new issue ID to set for the pull request."""
    
        self.session.query(PullRequest).filter(PullRequest.githubId == pullId).update({"issueId": issueId})
        self.session.commit()
    
    def database_get_file_id_by_filename(self, filename: str, repoId: int):
        """Retrieves the database ID of a file by its filename and repository ID.
        
        Parameters:
            filename (str): The filename to search for.
            repoId (int): The ID of the repository the file belongs to.
        
        Returns:
            int: The database ID of the file, or a dummy value if the file is not found."""
        
        stmt = select(GitFile.id).where(GitFile.fileName == filename).where(GitFile.repositoryId == repoId)
        try: 
            return self.session.execute(stmt).fetchone()[0]
        except:
            self.missingFileId -= 1
            return self.missingFileId # Return a dummy value if file not found