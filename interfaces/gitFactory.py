import os

from interfaces.abstractFactory import AbstractFactory
from github import Github, Auth
from dependency_injector import providers
from models.comment import Comment
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.repository import Repository
from rich.console import Console
from rich.table import Table

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
        self.files = pull_request.get_files()
        return self.files
    
    def get_pull_request(self, issue: Issue, repo: Repository):
        self.pullHtmlId = issue.pull_request.html_url.rsplit('/', 1)[-1]
        self.pull = repo.get_pull(number = int(self.pullHtmlId))
        return self.pull
    
    def get_repository(self):
        self.repository = self.g.get_repo(self.repo_name)
        return self.repository
    
    def get_comments(self, issue: Issue):
        self.comments = issue.get_comments()
        return self.comments
    
    def find_repos(self):
        i = 0
        console = Console()
        table = Table(title="Repositories")
        columns = ["FullName", "Stars", "Url"]
        for column in columns:
            table.add_column(column, justify="center")
        
        repos = self.g.search_repositories(query=f"stars:>={os.getenv('MIN_STARS')} language:{os.getenv('LANG')}")
        for repo in repos:
            table.add_row(repo.full_name, str(repo.stargazers_count), repo.html_url)
            i += 1
            if i == int(os.getenv('NB_REPO')):
                console.print(table)
                break