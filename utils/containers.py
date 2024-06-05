from dependency_injector import containers, providers
from interfaces.AbcFactoryGit import AbcFactoryGit
from interfaces.Semantic.SemanticTest import SemanticTest
from interfaces.Database.DbInterface import DbInterface
from interfaces.Database.EmbeddingDbI import EmbeddingDbI
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

class Container(containers.DeclarativeContainer):
    load_dotenv()
    Session = sessionmaker()
    session = providers.Singleton(Session)
    
    git_factory = providers.AbstractFactory(AbcFactoryGit)
    db_interface = providers.AbstractSingleton(DbInterface)
    semantic_test = providers.AbstractFactory(SemanticTest)
    db_embedding = providers.AbstractSingleton(EmbeddingDbI)