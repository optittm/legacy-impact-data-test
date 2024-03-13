import os

from interfaces.abstractFactory import AbstractFactory
from github import Github, Auth
from dependency_injector import providers
from models.comment import Comment
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.repository import Repository

class GithubFactory(AbstractFactory):
    
    pull_request = providers.Factory(PullRequest)
    modified_files = providers.Factory(ModifiedFiles)
    issue = providers.Factory(Issue)
    repository = providers.Factory(Repository)
    comment = providers.Factory(Comment)
    
    def __init__(self, session):
        AbstractFactory.__init__(self, session)
        self.repo_name = os.getenv('REPOSITORY_NAME')
        self.g = Github(auth=Auth.Token(os.getenv('GITHUB_TOKEN')))
    
    def get_issues(self, repo: Repository):
        self.issues = repo.get_issues(state = "all")
        return self.issues
    
    def get_modified_files(self, pull_request: PullRequest):
        self.files = pull_request.pull.get_files()
        return self.files
    
    def get_pull_requests(self, issue: Issue, repo: Repository):
        self.pullHtmlId = issue.pull_request.html_url.rsplit('/', 1)[-1]
        self.pull = repo.get_pull(number = self.pullHtmlId)
        return self.pull
    
    def get_repository(self):
        self.repository = self.g.get_repo(self.repo_name)
        return self.repository
    
    def get_comments(self, issue: Issue):
        self.comments = issue.get_comments()
        return self.comments