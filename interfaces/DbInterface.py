from __future__ import annotations
from abc import ABC, abstractmethod
from models.comment import Comment
from models.gitFile import GitFile
from models.issue import Issue
from models.modifiedFiles import ModifiedFiles
from models.pullRequest import PullRequest
from models.repository import Repository
from models.testResult import TestResult
from typing import List

class DbInterface(ABC):
    
    @abstractmethod
    def insert(self, data: Repository | Issue | PullRequest | TestResult | GitFile):
        raise NotImplementedError()
    
    @abstractmethod
    def insert_many(self, data: List[ModifiedFiles | Comment | GitFile]):
        raise NotImplementedError()
    
    @abstractmethod
    def update_issueId_pullRequest(self, pullId: int, issueId: int):
        raise NotImplementedError()
    
    @abstractmethod
    def get_file_id_by_filename(self, filename: str, repoId: int):
        raise NotImplementedError()
    
    @abstractmethod
    def get_shas_texts_and_issueId(self, repositoryName: str):
        raise NotImplementedError()
    
    @abstractmethod
    def get_repoId_from_repoName(self, repositoryName: str):
        raise NotImplementedError()