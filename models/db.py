from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def setup_db(engine):
    Base.metadata.create_all(engine)