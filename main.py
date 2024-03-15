import logging
import sqlalchemy as db
import os
import sys

from github import Github, Auth
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func
from utils.containers import Container, providers
from dependency_injector.wiring import inject
from interfaces.gitFactory import GithubFactory
from models.db import setup_db
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.comment import Comment
from progress.bar import IncrementalBar

logging.basicConfig(filename='logs.log', encoding='utf-8', level=logging.DEBUG)

@inject
def configure_session(container: Container):
    try:
        engine = db.create_engine("sqlite:///" + os.getenv("SQLITE_PATH"))
    except ArgumentError as e:
        raise (f"Error from sqlalchemy : {str(e)}")
    
    sessionM = sessionmaker()
    sessionM.configure(bind=engine)
    setup_db(engine)

    container.session.override(
        providers.Singleton(sessionM)
    )

@inject
def find_repo():
    gitFactory.find_repos(
        os.getenv('MIN_STARS'),
        os.getenv('LANG'),
        os.getenv('NB_REPO')
    )

@inject
def get_data_repo():
    max_id = gitFactory.session.query(func.max(ModifiedFiles.id)).scalar()
    i = max_id if max_id != None else 0
    j = -1
    
    repo = gitFactory.get_repository()
    gitFactory.session.add(repo)
    
    issues = list(gitFactory.get_issues())
    bar = IncrementalBar("Fetching data", max = len(issues))
    for issue in issues:
        j += 1
        bar.next()
        try:
            pull_request = gitFactory.get_pull_request(j)
            if not pull_request:
                logging.info("Pull Request not merged for issue: " + str(issue.id))
                continue
        except:
            logging.info("Error fetching pull request for the issue: " + str(issue.id))
            continue
        
        logging.info("Pull Request merged for issue: " + str(issue.id))
        gitFactory.session.add(issue)
        gitFactory.session.add(pull_request)
        gitFactory.session.add_all(list(gitFactory.get_comments(j)))
        gitFactory.session.add_all(list(gitFactory.get_modified_files(i)))
        logging.info("Committed data for issue: " + str(issue.id))
    
    gitFactory.session.commit()
    bar.finish()

if __name__ == "__main__":
    container = Container()
    configure_session(container)
    container.git_factory.override(
        providers.Factory(
            GithubFactory,
            session = container.session,
            repo_name = os.getenv("REPOSITORY_NAME"),
            g = Github(auth=Auth.Token(os.getenv('GITHUB_TOKEN')))
        )
    )
    gitFactory = container.git_factory()
    
    scripts = {
        "1": get_data_repo,
        "2": find_repo
    }
    arg = sys.argv[1]
    scripts[arg]()