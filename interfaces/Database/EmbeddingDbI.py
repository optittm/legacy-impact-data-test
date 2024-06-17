from abc import ABC, abstractmethod

class EmbeddingDbI(ABC):
    
    @abstractmethod
    def save_embedding(self, file_path : str, embedding : bytes, function_name : str = None):
        raise NotImplementedError()
    
    @abstractmethod
    def get_embedding(self, file_path : str, function_name : str = None):
        raise NotImplementedError()
    
    @abstractmethod
    def clean(self):
        raise NotImplementedError()