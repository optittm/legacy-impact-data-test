from abc import ABC, abstractmethod

class AbcFactoryGit(ABC):
    
    @abstractmethod
    def get_issue(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_repository(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_comments(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_pull_requests(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_modified_files(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_gitFile(self):
        raise NotImplementedError()