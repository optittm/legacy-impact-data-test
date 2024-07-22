from dependency_injector import containers, providers
from interfaces.AbcFactoryGit import AbcFactoryGit
from interfaces.Semantic.SemanticTest import SemanticTest
from interfaces.Database.DbInterface import DbInterface
from interfaces.Database.EmbeddingDbI import EmbeddingDbI
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

class Container(containers.DeclarativeContainer):
    """This class is a container that provides dependency injection for various interfaces and factories used in the application.
    The `Session` provider is a singleton that provides a SQLAlchemy session for database interactions.
    The `git_factory` provider is an abstract factory that creates instances of `AbcFactoryGit`, which is used for interacting with a Git repository.
    The `db_interface` provider is an abstract singleton that provides an instance of `DbInterface`, which is used for interacting with a database.
    The `semantic_test` provider is an abstract factory that creates instances of `SemanticTest`, which is used for performing semantic tests.
    The `db_embedding` provider is an abstract singleton that provides an instance of `EmbeddingDbI`, which is used for interacting with an embedding database."""
    
    load_dotenv()
    Session = sessionmaker()
    session = providers.Singleton(Session)
    
    git_factory = providers.AbstractFactory(AbcFactoryGit)
    db_interface = providers.AbstractSingleton(DbInterface)
    semantic_test = providers.AbstractFactory(SemanticTest)
    db_embedding = providers.AbstractSingleton(EmbeddingDbI)