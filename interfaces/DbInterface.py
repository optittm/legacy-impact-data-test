from abc import ABC, abstractmethod

class DbInterface(ABC):
    
    @abstractmethod
    def insert(self):
        raise NotImplementedError()
    
    @abstractmethod
    def insert_many(self):
        raise NotImplementedError()
    
    @abstractmethod
    def update_issueId_pullRequest(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_file_id_by_filename(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_shas_texts_and_issueId(self):
        raise NotImplementedError()
    
    @abstractmethod
    def get_repoId_from_repoName(self):
        raise NotImplementedError()