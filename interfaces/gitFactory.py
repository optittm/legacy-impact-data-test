from interfaces.abstractFactory import AbstractFactory
from rich.console import Console
from rich.table import Table
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.comment import Comment

class GithubFactory(AbstractFactory):
    
    def __init__(self, session, repo_name, g):
        AbstractFactory.__init__(self, session, repo_name)
        self.g = g
        self.file_id = 0
    
    def get_issues(self):
        self.issues = self.g.search_issues(query=f"repo:{self.repository.full_name} is:pr is:merged")
        for issue in self.issues:
            yield Issue(
                id = issue.id,
                title = issue.title,
                body = issue.body,
                state = issue.state,
                repositoryId = self.repository.id
            )
    
    def get_modified_files(self, i: int):
        self.files = self.pull.get_files()
        if i > self.file_id:
            self.file_id = i
        for file in self.files:
            self.file_id += 1
            yield ModifiedFiles(
                id = self.file_id,
                sha = file.sha,
                filename = file.filename,
                status = file.status,
                patch = file.patch,
                additions = file.additions,
                deletions = file.deletions,
                changes = file.changes,
                pullRequestId = self.pull.id
            )
    
    def get_pull_request(self, j: int):
        self.pullHtmlId = self.issues[j].pull_request.html_url.rsplit('/', 1)[-1]
        self.pull = self.repository.get_pull(number = int(self.pullHtmlId))
        if self.pull.is_merged():
            return PullRequest(
                id = self.pull.id,
                title = self.pull.title,
                body = self.pull.body,
                state = self.pull.state,
                shaBase = self.pull.base.sha,
                issueId = self.issues[j].id
            )
        else:
            return False
    
    def get_repository(self):
        self.repository = self.g.get_repo(self.repo_name)
        return Repository(
            id = self.repository.id,
            fullName = self.repository.full_name,
            description = self.repository.description,
            language = self.repository.language,
            stars = self.repository.stargazers_count
        )
    
    def get_comments(self, j: int):
        self.comments = self.issues[j].get_comments()
        for comment in self.comments:
            yield Comment(
                id = comment.id,
                body = comment.body,
                issueId = self.issues[j].id
            )
    
    def find_repos(self, stars, lang, nb_repo):
        i = 0
        console = Console()
        table = Table(title="Repositories")
        columns = ["FullName", "Stars", "Url"]
        for column in columns:
            table.add_column(column, justify="center")
        
        repos = self.g.search_repositories(query=f"stars:>={stars} language:{lang}")
        for repo in repos:
            table.add_row(repo.full_name, str(repo.stargazers_count), repo.html_url)
            i += 1
            if i == int(nb_repo):
                console.print(table)
                break