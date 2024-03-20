from interfaces.AbcFactoryGit import AbcFactoryGit
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.comment import Comment

class GithubFactory(AbcFactoryGit):
    
    def __init__(self, g):
        self.g = g
        self.file_id = 0
    
    """Gets issues from the GitHub API.
    
    Searches for merged pull requests in the repository 
    and yields Issue objects for each one.
    
    Yields:
        Issue: The issue with details and repository id."""
    def get_issues(self):
        self.issues = self.g.search_issues(query=f"repo:{self.repository.full_name} is:pr is:merged")
        issuesList = []
        for issue in self.issues:
            issuesList.append(Issue(
                id = issue.id,
                title = issue.title,
                body = issue.body,
                state = issue.state,
                repositoryId = self.repository.id
            ))
        return issuesList, self.issues
    
    """Gets modified files from a pull request. 
    
    Iterates through the files modified in the pull request, assigns 
    each one an id, and yields ModifiedFiles objects containing file
    details and the pull request id.
    
    Parameters:
        max_id_db (int): The maximum id currently stored in the db.
    
    Yields:
        ModifiedFiles: The modified file with details and pull request id."""
    def get_modified_files(self, max_id_db: int):
        self.files = self.pull.get_files()
        if max_id_db > self.file_id:
            self.file_id = max_id_db
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
    
    """Gets a pull request from the GitHub API.
    
    Iterates through the issues searching for merged pull requests. 
    Checks if the pull request is merged, and returns a PullRequest object 
    containing details of the pull request if it is merged, otherwise returns None.
    
    Parameters:
        j (int): The index of the current issue being checked.
    
    Returns:
        PullRequest: A PullRequest object containing pull request details if merged and it's issue id.
        None: If the pull request is not merged."""
    def get_pull_request(self, issue: Issue):
        self.pullHtmlId = issue.pull_request.html_url.rsplit('/', 1)[-1]
        self.pull = self.repository.get_pull(number = int(self.pullHtmlId))
        if self.pull.is_merged():
            return PullRequest(
                id = self.pull.id,
                title = self.pull.title,
                body = self.pull.body,
                state = self.pull.state,
                shaBase = self.pull.base.sha,
                issueId = issue.id
            )
        else:
            return None
    
    """Gets a GitHub repository object for the given repository name.
    
    Parameters:
        repo_name (str): The name of the repository.
    
    Returns:
        Repository: A Repository object containing details like id, full name, 
        description, language, and star count."""
    def get_repository(self, repo_name: str):
        self.repository = self.g.get_repo(repo_name)
        return Repository(
            id = self.repository.id,
            fullName = self.repository.full_name,
            description = self.repository.description,
            language = self.repository.language,
            stars = self.repository.stargazers_count
        )
    
    """Gets the comments for the pull request associated with the issue at index j.
    
    Iterates through the comments for the issue and yields Comment objects containing 
    the comment details.
    
    Parameters:
        j (int): The index of the issue to get comments for.
    
    Yields:
        Comment: The next comment for the issue."""
    def get_comments(self, issue: Issue):
        self.comments = issue.get_comments()
        for comment in self.comments:
            yield Comment(
                id = comment.id,
                body = comment.body,
                issueId = issue.id
            )
    
    """Searches GitHub repositories based on stars, language, and number of repos.
    
    Iterates through paginated search results up to the specified number of repos. 
    Yields repository name, stars, pull requests, and URL for each qualifying repo.
    
    Parameters:
        stars (int): Minimum stars threshold. 
        lang (str): Language to filter by.
        nb_repo (int): Maximum number of repos to return.
    
    Yields:
        tuple: (name, stars, pulls, url) for each qualifying repo."""
    def find_repos(self, stars, lang, nb_repo):
        i = 0        
        repos = self.g.search_repositories(query=f"stars:>={stars} language:{lang}")
        for repo in repos:
            yield(
                repo.full_name,
                str(repo.stargazers_count),
                str(self.g.search_issues(query=f"repo:{repo.full_name} is:pr is:merged").totalCount),
                repo.html_url
            )
            i += 1
            if i == int(nb_repo):
                break