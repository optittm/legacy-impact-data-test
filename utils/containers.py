from dependency_injector import containers, providers
from interfaces.AbcFactoryGit import AbcFactoryGit
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

class Container(containers.DeclarativeContainer):
    load_dotenv()
    sessionM = sessionmaker()
    session = providers.Singleton(sessionM)
    
    git_factory = providers.AbstractFactory(AbcFactoryGit)