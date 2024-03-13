import os

from dependency_injector import containers, providers
from interfaces.abstractFactory import AbstractFactory
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
engine = create_engine("sqlite:///" + os.getenv("SQLITE_PATH"))
Session = sessionmaker(bind=engine)

class Container(containers.DeclarativeContainer):
    
    session = providers.Singleton(Session)
    
    git_factory = providers.AbstractFactory(AbstractFactory)