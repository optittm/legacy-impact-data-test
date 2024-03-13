from abc import ABC, abstractmethod

class AbstractFactory(ABC):
    
    def __init__(self, session):
        self.session = session
    
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
    def get_pull_requests(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_modified_files(self):
        raise NotImplementedError()