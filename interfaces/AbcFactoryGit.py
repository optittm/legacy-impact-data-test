from abc import ABC, abstractmethod
from models.issue import Issue
from models.pullRequest import PullRequest

class AbcFactoryGit(ABC):
    
    @abstractmethod
    def get_issue(self, number: int):
        raise NotImplementedError()
    
    @abstractmethod
    def get_repository(self, repo_name: str):
        raise NotImplementedError()
    
    @abstractmethod
    def get_comments(self, issue: Issue, issueId: int):
        raise NotImplementedError()
    
    @abstractmethod
    def get_pull_requests(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_modified_files(self, pull: PullRequest, pullId: int):
        raise NotImplementedError()
    
    @abstractmethod
    def get_gitFiles(self):
        raise NotImplementedError()
    
    @abstractmethod
    def find_repos(self, stars: int, lang: str, nb_repo: int):
        raise NotImplementedError()
    
    @abstractmethod
    def create_test_repo(self, shaBase, repoFullName: str, path_repos: str):
        raise NotImplementedError()