import logging
import sqlalchemy as db
import os
import click

from github import Github, Auth
from rich.console import Console
from rich.table import Table
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func
from utils.containers import Container, providers
from dependency_injector.wiring import inject
from interfaces.GithubFactory import GithubFactory
from models.db import setup_db
from models.modifiedFiles import ModifiedFiles
from progress.bar import IncrementalBar

logging.basicConfig(filename='logs.log', encoding='utf-8', level=logging.DEBUG)

@click.group()
def cli():
    pass

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

@click.command()
@click.option('--min_stars', envvar='MIN_STARS', default=os.getenv('MIN_STARS'), help='Minimum stars for a repository')
@click.option('--lang', envvar='LANG', default=os.getenv('LANG'), help='Language of the repository')
@click.option('--nb_repo', envvar='NB_REPO', default=os.getenv('NB_REPO'), help='Number of repositories to fetch')
@inject
def find_repo(min_stars, lang, nb_repo):
    console = Console()
    table = Table(title="Repositories")
    columns = ["FullName", "Stars", "Nb Issues", "Topics", "Url"]
    for column in columns:
        table.add_column(column, justify="center")
    
    repos_data = GithubFactory.find_repos(min_stars, lang, nb_repo)
    for data in repos_data:
        table.add_row(data[0], data[1], data[2], data[3], data[4])
    console.print(table)

@click.command()
@click.option('--repository_name', envvar='REPOSITORY_NAME', default=os.getenv('REPOSITORY_NAME'), help='Name of the repository')
@inject
def get_data_repo(repository_name):
    max_id = GithubFactory.session.query(func.max(ModifiedFiles.id)).scalar()
    i = max_id if max_id != None else 0
    j = -1
    
    repo = GithubFactory.get_repository(repository_name)
    GithubFactory.session.add(repo)
    
    issues = list(GithubFactory.get_issues())
    bar = IncrementalBar("Fetching data", max = len(issues))
    for issue in issues:
        j += 1
        bar.next()
        try:
            pull_request = GithubFactory.get_pull_request(j)
            if not pull_request:
                logging.info("Pull Request not merged for issue: " + str(issue.id))
                continue
        except:
            logging.info("Error fetching pull request for the issue: " + str(issue.id))
            continue
        
        logging.info("Pull Request merged for issue: " + str(issue.id))
        GithubFactory.session.add(issue)
        GithubFactory.session.add(pull_request)
        GithubFactory.session.add_all(list(GithubFactory.get_comments(j)))
        GithubFactory.session.add_all(list(GithubFactory.get_modified_files(i)))
        logging.info("Committed data for issue: " + str(issue.id))
    
    GithubFactory.session.commit()
    bar.finish()

cli.add_command(get_data_repo)
cli.add_command(find_repo)

if __name__ == "__main__":
    container = Container()
    configure_session(container)
    container.git_factory.override(
        providers.Factory(
            GithubFactory,
            session = container.session,
            g = Github(auth=Auth.Token(os.getenv('GITHUB_TOKEN')))
        )
    )
    GithubFactory = container.git_factory()
    
    cli()