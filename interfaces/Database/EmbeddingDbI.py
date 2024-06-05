from abc import ABC, abstractmethod

class EmbeddingDbI(ABC):
    
    @abstractmethod
    def save_embedding(self, file_path : str, function_name : str, embedding : bytes):
        raise NotImplementedError()
    
    @abstractmethod
    def get_embedding(self, file_path : str, function_name : str):
        raise NotImplementedError()