import logging
import sqlalchemy as db
import os

from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker
from utils.containers import Container, providers
from dependency_injector.wiring import inject
from interfaces.gitFactory import GithubFactory
from models.db import setup_db
from models.repository import Repository
from models.issue import Issue
from models.pullRequest import PullRequest
from models.modifiedFiles import ModifiedFiles
from models.comment import Comment

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
def main():
    i = 0
    repo = gitFactory.get_repository()
    repository = Repository(repo.id, repo.full_name, repo.description, repo.language, repo.stargazers_count)
    gitFactory.session.add(repository)
    
    issues = gitFactory.get_issues(repo)
    for issue in issues:
        try:
            pull_request = gitFactory.get_pull_request(issue, repo)
            if pull_request.merged_at == None:
                logging.info("Pull Request not merged for issue: " + str(issue.id))
                continue
        except:
            logging.info("Error fetching pull request for the issue: " + str(issue.id))
            continue
        
        logging.info("Pull Request merged for issue: " + str(issue.id))
        issue_to_save = Issue(issue.id, issue.title, issue.body, issue.state, repo.id)
        gitFactory.session.add(issue_to_save)
        
        pull_request_to_save = PullRequest(pull_request.id, pull_request.title, pull_request.body, pull_request.state, pull_request.merged_at, pull_request.base.sha, issue.id)
        gitFactory.session.add(pull_request_to_save)
        
        comments = gitFactory.get_comments(issue)
        for comment in comments:
            comment_to_save = Comment(comment.id, comment.body, issue.id)
            gitFactory.session.add(comment_to_save)
        
        modified_files = gitFactory.get_modified_files(pull_request)
        for file in modified_files:
            i += 1
            file_to_save = ModifiedFiles(i, file.sha, file.filename, file.status, file.patch, file.additions, file.deletions, file.changes, pull_request.id)
            gitFactory.session.add(file_to_save)
        logging.info("Committed data for issue: " + str(issue.id))
    
    gitFactory.session.commit()

if __name__ == "__main__":
    container = Container()
    configure_session(container)
    container.git_factory.override(
        providers.Factory(
            GithubFactory,
            session = container.session
        )
    )
    gitFactory = container.git_factory()
    
    main()