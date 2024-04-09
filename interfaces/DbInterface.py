from abc import ABC, abstractmethod

class DbInterface(ABC):
    
    @abstractmethod
    def database_insert(self):
        raise NotImplementedError()
    
    @abstractmethod
    def database_insert_many(self):
        raise NotImplementedError()
    
    @abstractmethod
    def database_update_issueId_pullRequest(self):
        raise NotImplementedError()