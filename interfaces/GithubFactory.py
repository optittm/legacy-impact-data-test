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
    
    def get_issues(self):
        """Gets issues from the GitHub API.
        
        Searches for merged pull requests in the repository 
        and yields Issue objects for each one.
        
        Yields:
            Issue: The issue with details and repository id."""
        
        issues = self.g.search_issues(query=f"repo:{self.repository.full_name} is:pr is:merged")
        issuesList = []
        for issue in issues:
            issuesList.append(Issue(
                githubId = issue.id,
                title = issue.title,
                body = issue.body,
                state = issue.state,
                repositoryId = self.repository.id
            ))
        return issuesList, issues
    
    def get_modified_files(self, pull: PullRequest):
        """Gets modified files from a pull request. 
        
        Iterates through the files modified in the pull request, assigns 
        each one an id, and yields ModifiedFiles objects containing file
        details and the pull request id.
        
        Parameters:
            max_id_db (int): The maximum id currently stored in the db.
        
        Yields:
            ModifiedFiles: The modified file with details and pull request id."""
        
        files = pull.get_files()
        for file in files:
            yield ModifiedFiles(
                sha = file.sha,
                filename = file.filename,
                status = file.status,
                patch = file.patch,
                additions = file.additions,
                deletions = file.deletions,
                changes = file.changes,
                pullRequestId = pull.id
            )
    
    def get_pull_request(self, issue: Issue):
        """Gets a pull request from the GitHub API.
        
        Iterates through the issues searching for merged pull requests. 
        Checks if the pull request is merged, and returns a PullRequest object 
        containing details of the pull request if it is merged, otherwise returns None.
        
        Parameters:
            j (int): The index of the current issue being checked.
        
        Returns:
            PullRequest: A PullRequest object containing pull request details if merged and it's issue id.
            None: If the pull request is not merged."""
        
        pullHtmlId = issue.pull_request.html_url.rsplit('/', 1)[-1]
        pull = self.repository.get_pull(number = int(pullHtmlId))
        if pull.is_merged():
            return PullRequest(
                githubId = pull.id,
                title = pull.title,
                body = pull.body,
                state = pull.state,
                shaBase = pull.base.sha,
                issueId = issue.id
            ), pull
        else:
            return None
    
    def get_repository(self, repo_name: str):
        """Gets a GitHub repository object for the given repository name.
        
        Parameters:
            repo_name (str): The name of the repository.
        
        Returns:
            Repository: A Repository object containing details like id, full name, 
            description, language, and star count."""
        
        self.repository = self.g.get_repo(repo_name)
        return Repository(
            id = self.repository.id,
            fullName = self.repository.full_name,
            description = self.repository.description,
            language = self.repository.language,
            stars = self.repository.stargazers_count
        )
    
    def get_comments(self, issue: Issue):
        """Gets the comments for the pull request associated with the issue at index j.
        
        Iterates through the comments for the issue and yields Comment objects containing 
        the comment details.
        
        Parameters:
            j (int): The index of the issue to get comments for.
        
        Yields:
            Comment: The next comment for the issue."""
        
        self.comments = issue.get_comments()
        for comment in self.comments:
            yield Comment(
                githubId = comment.id,
                body = comment.body,
                issueId = issue.id
            )
    
    def find_repos(self, stars, lang, nb_repo):
        """Searches GitHub repositories based on stars, language, and number of repos.
        
        Iterates through paginated search results up to the specified number of repos. 
        Yields repository name, stars, pull requests, and URL for each qualifying repo.
        
        Parameters:
            stars (int): Minimum stars threshold. 
            lang (str): Language to filter by.
            nb_repo (int): Maximum number of repos to return.
        
        Yields:
            tuple: (name, stars, pulls, url) for each qualifying repo."""
        
        i = 0        
        repos = self.g.search_repositories(query=f"stars:>={stars} language:{lang}")
        for repo in repos:
            yield(
                repo.full_name,
                str(repo.stargazers_count),
                str(self.g.search_issues(query=f"repo:{repo.full_name} is:merged linked:issue").totalCount),
                repo.html_url
            )
            i += 1
            if i == int(nb_repo):
                break