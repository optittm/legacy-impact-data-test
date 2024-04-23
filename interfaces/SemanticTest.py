from abc import ABC, abstractmethod

class SemanticTest(ABC):
    
    @abstractmethod
    def get_max_file_score_from_issue(self, text_issue : str):
        raise NotImplementedError()
    
    @abstractmethod
    def init_repo(self, repoFullName: str):
        raise NotImplementedError()