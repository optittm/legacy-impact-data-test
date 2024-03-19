from abc import ABC, abstractmethod

class AbcFactoryGit(ABC):
    
    @abstractmethod
    def get_issues(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_repository(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_comments(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_pull_request(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_modified_files(self):
        raise NotImplementedError()
    
    @abstractmethod
    def find_repos(self):
        raise NotImplementedError()