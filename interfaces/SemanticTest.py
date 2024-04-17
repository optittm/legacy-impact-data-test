from abc import ABC, abstractmethod

class SemanticTest(ABC):
    
    @abstractmethod
    def test_issue(self):
        raise NotImplementedError()
    
    @abstractmethod
    def create_test_repo(self):
        raise NotImplementedError()
    
    @abstractmethod
    def init_repo(self):
        raise NotImplementedError()