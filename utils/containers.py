from dependency_injector import containers, providers
from interfaces.AbcFactoryGit import AbcFactoryGit
from dotenv import load_dotenv
from interfaces.DbInterface import DbInterface
from sqlalchemy.orm import sessionmaker

class Container(containers.DeclarativeContainer):
    load_dotenv()
    Session = sessionmaker()
    session = providers.Singleton(Session)
    
    git_factory = providers.AbstractFactory(AbcFactoryGit)
    db_interface = providers.AbstractSingleton(DbInterface)