import logging
import re
import os

from interfaces.AbcFactoryGit import AbcFactoryGit
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.comment import Comment
from models.gitFile import GitFile
from progress.bar import IncrementalBar
from progress.spinner import PixelSpinner
from utils.missingFileException import MissingFileException

class GithubFactory(AbcFactoryGit):
    
    def __init__(self, g, db):
        self.g = g
        self.file_id = 0
        self.db = db
    
    def get_issue(self, number: int):
        """Gets an issue from the Github API.
        
        Parameters:
        number: The issue number.
        
        Returns:
        A tuple containing the Github issue object and the local Issue model object."""
        try:
            issue = self.repository.get_issue(number=number)
        except:
            logging.exception(f"Could not find Issue with ID : {number}")
            return 0, 0
        return issue, Issue(
            githubId = issue.id,
            title = issue.title,
            body = issue.body,
            state = issue.state,
            repositoryId = self.repository.id
        )
    
    def get_modified_files(self, pull: PullRequest, pullId: int):
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
            try:
                fileId = self.db.get_file_id_by_filename(file.filename, self.repository.id)
            except MissingFileException:
                fileId = self.db.insert(GitFile(
                    sha = file.sha,
                    fileName = file.filename,
                    repositoryId = self.repository.id
                ))
            
            yield ModifiedFiles(
                gitFileId = fileId,
                pullRequestId = pullId,
                status = file.status,
                patch = file.patch,
                additions = file.additions,
                deletions = file.deletions,
                changes = file.changes
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
        
        issueBar = IncrementalBar("Fetching issues", max = issues.totalCount)
        for issue in issues:
            issueBar.next()
            pullHtmlId = issue.pull_request.html_url.rsplit('/', 1)[-1]
            pull = self.repository.get_pull(number = int(pullHtmlId))
            pulls.append(pull)
        issueBar.finish()
        
        pullList, issueNumbers = [], []
        pullBar = IncrementalBar("Fetching pulls", max = len(pulls))
        for pull in pulls:
            pullBar.next()
            title_ids = self.__find_issues_ids_in_text(pull.title)
            if pull.body is not None:
                body_ids = self.__find_issues_ids_in_text(pull.body)
            comment_ids = []
            for comment in pull.get_comments():
                comment_ids.extend(self.__find_issues_ids_in_text(comment.body))
            
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
        pullBar.finish()
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
    
    def get_comments(self, issue: Issue, issueId: int):
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
                issueId = issueId
            )
    
    def get_gitFiles(self):
        """Recursively fetches all files in the repository, yielding a GitFile object for each file.
        
        The method uses a PixelSpinner to provide visual feedback while fetching the files.
        It first gets the contents of the repository root directory, then recursively fetches the contents of any subdirectories.
        For each file, it yields a GitFile object containing the file's SHA, file name, and repository ID."""
        
        contents = self.repository.get_contents("")
        contentSpinner = PixelSpinner("Fetching files ")
        while contents:
            contentSpinner.next()
            file = contents.pop(0)
            if file.type == "dir":
                contents.extend(self.repository.get_contents(file.path))
            else:
                yield GitFile(
                    sha = file.sha,
                    fileName = file.path,
                    repositoryId = self.repository.id
                )
        contentSpinner.finish()
    
    def find_repos(self, stars: int, lang: str, nb_repo: int):
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
            totalIssues = self.g.search_issues(query=f"repo:{repo.full_name} is:merged linked:issue")
            totalIssues.get_page(0)
            yield(
                repo.full_name,
                str(repo.stargazers_count),
                str(totalIssues.totalCount),
                str(repo.size),
                repo.html_url
            )
            i += 1
            if i == int(nb_repo):
                break
    
    def create_test_repo(self, shaBase, repoFullName: str, path_repos: str):
        """Creates a test repository by cloning the repository specified by `self.repoFullName` and checking out the base commit specified by `shaBase`.
        
        If the test repository directory does not exist, it will be created under the `./test` directory. The repository will then be cloned from the specified URL and the base commit will be checked out.
        
        Parameters:
            shaBase : The commit hash of the base commit to check out in the test repository."""
        if not os.path.exists(path_repos):
            if not os.path.exists("./test"):
                os.mkdir("./test")
            os.system(f"cd ./test && git clone https://github.com/{repoFullName}")
        
        os.system(f"cd {path_repos} && git checkout {shaBase}")
    
    def __find_issues_ids_in_text(self, text):
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