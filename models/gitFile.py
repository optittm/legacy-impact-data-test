from sqlalchemy import Column, Integer, String, ForeignKey
from models.db import Base

class GitFile(Base):
    __tablename__ = "gitFile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sha = Column(String)
    fileName = Column(String)
    repositoryId = Column(Integer, ForeignKey("repository.id"))