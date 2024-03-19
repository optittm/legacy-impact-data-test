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
    
    def database_insert(self, data: Repository | Issue | PullRequest | ModifiedFiles | Comment):
        self.session.add(data)
        self.session.commit()
    
    def database_insert_many(self, data: list[Repository | Issue | PullRequest | ModifiedFiles | Comment]):
        self.session.add_all(data)
        self.session.commit()
    
    def query_max_id(self):
        return self.session.query(func.max(ModifiedFiles.id)).scalar()