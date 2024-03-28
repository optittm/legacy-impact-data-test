import re

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
    
    def get_issue(self, number: int):
        """Gets an issue from the Github API.
        
        Parameters:
        number: The issue number.
        
        Returns:
        A tuple containing the Github issue object and the local Issue model object."""
        
        issue = self.repository.get_issue(number=number)
        return issue, Issue(
            githubId = issue.id,
            title = issue.title,
            body = issue.body,
            state = issue.state,
            repositoryId = self.repository.id
        )
    
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
    
    def get_pull_requests(self):
        """Searches for merged pull requests linked to issues.
        
        Iterates through merged pull requests, extracting linked issue ids. 
        Creates PullRequest objects containing issue ids.
        
        Returns:
            pullList: List of PullRequest objects
            pulls: Raw search results"""
        
        pulls = []
        issues = self.g.search_issues(query=f"repo:{self.repository.full_name} is:pr is:merged linked:issue")
        for issue in issues:
            pullHtmlId = issue.pull_request.html_url.rsplit('/', 1)[-1]
            pull = self.repository.get_pull(number = int(pullHtmlId))
            pulls.append(pull)
        
        pullList, issueNumbers = [], []
        for pull in pulls:
            title_ids = self.get_ids(pull.title)
            body_ids = self.get_ids(pull.body)
            comment_ids = []
            for comment in pull.get_comments():
                comment_ids.extend(self.get_ids(comment.body))
            
            if title_ids:
                issueNumbers.append(int(title_ids[0]))
            elif body_ids:
                issueNumbers.append(int(body_ids[0]))
            elif comment_ids:
                issueNumbers.append(int(comment_ids[0]))
            
            pullList.append(PullRequest(
                githubId = pull.id,
                title = pull.title,
                body = pull.body,
                state = pull.state,
                shaBase = pull.base.sha,
                issueId = 0
            ))
        return pullList, pulls, issueNumbers
    
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
        repos = self.g.search_repositories(query=f"stars:>={stars} language:{lang} is:public")
        for repo in repos:
            yield(
                repo.full_name,
                str(repo.stargazers_count),
                str(self.g.search_issues(query=f"repo:{repo.full_name} is:merged linked:issue").get_page(0).totalCount),
                str(repo.size),
                repo.html_url
            )
            i += 1
            if i == int(nb_repo):
                break
    
    def get_ids(self, text):
        """Gets issue ids from pr text.
        
        Parses the given text looking for references to issues in the forms of '#1234' or 'https://github.com/user/repo/issues/1234' and returns a list of the referenced ids.
        
        Parameters:
            text: The text to parse for issue and PR ids.
        
        Returns:
            A list of found issue and PR ids."""
        
        list_links = ["close", "closes", "closed", "fix", "fixes", "fixed", "resolve", "resolves", "resolved"]
        regex_simple_link = "\s+#(\d+)|".join(link.strip() for link in list_links) + "\s+#(\d+)"
        regex_url_link = "\s+https?://[^/]+/[^/]+/[^/]+/[^/]+/([0-9]+)|".join(link.strip() for link in list_links) + "\s+https?://[^/]+/[^/]+/[^/]+/[^/]+/([0-9]+)"
        ids = []
        
        for match in re.finditer(regex_simple_link + "|" + regex_url_link, text.lower()):
            for group in match.groups():
                if group is not None:
                    ids.append(group)

        return ids