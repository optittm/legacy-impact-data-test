from interfaces.DbInterface import DbInterface
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.comment import Comment
from sqlalchemy.sql.expression import func

class SQLite(DbInterface):
    
    def __init__(self, session):
        self.session = session
    
    """Inserts the given data object into the database.
    
    Parameters:
        data (Repository | Issue | PullRequest | ModifiedFiles | Comment): The data object to insert.
    
    Commits the change to the database."""
    def database_insert(self, data: Repository | Issue | PullRequest | ModifiedFiles | Comment):
        self.session.add(data)
        self.session.commit()
    
    """Inserts the given list of data objects into the database.
    
    Parameters:
        data (list[Repository | Issue | PullRequest | ModifiedFiles | Comment]): 
            The list of data objects to insert.
    
    Commits the changes to the database."""
    def database_insert_many(self, data: list[Repository | Issue | PullRequest | ModifiedFiles | Comment]):
        self.session.add_all(data)
        self.session.commit()