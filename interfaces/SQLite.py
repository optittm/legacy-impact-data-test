from __future__ import annotations
import logging
from interfaces.DbInterface import DbInterface
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.gitFile import GitFile
from models.comment import Comment
from models.testResult import TestResult
from sqlalchemy import update, select, func
from typing import List
from utils.missingFileException import MissingFileException

class SQLite(DbInterface):
    
    def __init__(self, session):
        self.session = session
    
    def insert(self, data: Repository | Issue | PullRequest | TestResult | GitFile):
        """Inserts the given data object into the database.
        
        Parameters:
            data (Repository | Issue | PullRequest | ModifiedFiles | Comment): The data object to insert.
        
        Commits the change to the database."""
    
        self.session.add(data)
        self.session.commit()
        return data.id
    
    def insert_many(self, data: List[ModifiedFiles | Comment | GitFile]):
        """Inserts the given list of data objects into the database.
        
        Parameters:
            data (list[Repository | Issue | PullRequest | ModifiedFiles | Comment]): 
                The list of data objects to insert.
        
        Commits the changes to the database."""
    
        self.session.add_all(data)
        self.session.commit()
        if not all(isinstance(x, ModifiedFiles) for x in data):
            return [data.id for data in data]
    
    def update_issueId_pullRequest(self, pullId: int, issueId: int):
        """Updates the issueId field of a PullRequest in the database.
    
        Parameters:
            pullId (int): The GitHub ID of the pull request to update.
            issueId (int): The new issue ID to set for the pull request."""
    
        stmt = update(PullRequest).where(PullRequest.githubId == pullId).values(issueId = issueId)
        self.session.execute(stmt)
    
    def get_file_id_by_filename(self, filename: str, repoId: int):
        """Retrieves the database ID of a file by its filename and repository ID.
        
        Parameters:
            filename (str): The filename to search for.
            repoId (int): The ID of the repository the file belongs to.
        
        Returns:
            int: The database ID of the file, or a dummy value if the file is not found."""
        
        stmt = select(GitFile.id).where(GitFile.fileName == filename).where(GitFile.repositoryId == repoId)
        fileId = self.session.execute(stmt).fetchone()
        if fileId == None:
            raise MissingFileException(filename)
        return fileId[0]
    
    def get_shas_texts_and_issueId(self, repositoryName: str):
        """Retrieves the title, body, base SHA, and issue ID for pull requests associated with a given repository.
    
        Parameters:
            repositoryName (str): The name of the repository to retrieve data for.
        
        Returns:
            list[tuple[str, str, str, int]]: A list of tuples containing the pull request title, body, base SHA, and issue ID."""
        stmt = select(Issue.title, Issue.body, PullRequest.shaBase, Issue.id).where(PullRequest.issueId == Issue.id).where(Issue.repositoryId == self.get_repoId_from_repoName(repositoryName))
        return(self.session.execute(stmt).fetchall())
    
    def get_repoId_from_repoName(self, repositoryName: str):
        """Retrieves the database ID of a repository by its full name.
    
        Parameters:
            repositoryName (str): The full name of the repository to retrieve the ID for.
        
        Returns:
            int: The database ID of the repository."""
        stmt = select(Repository.id).where(Repository.fullName == repositoryName)
        return(self.session.execute(stmt).fetchone()[0])
    
    def issue_already_treated(self, issueId: int):
        stmt = select(func.count(TestResult.issueId)).where(TestResult.issueId == issueId)
        result = self.session.execute(stmt).scalar()
        return result > 0