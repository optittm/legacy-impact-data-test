import logging
import os
import click
import sqlalchemy as db

from github import Github, Auth
from rich.console import Console
from rich.table import Table
from interfaces.SQLite import SQLite
from utils.containers import Container, providers
from dependency_injector.wiring import inject
from interfaces.GithubFactory import GithubFactory
from progress.bar import IncrementalBar
from sqlalchemy.orm import sessionmaker
from models.db import setup_db
from sqlalchemy.exc import ArgumentError

logging.basicConfig(filename='logs.log', encoding='utf-8', level=logging.DEBUG)

@inject
def configure_session(container: Container):
    try:
        engine = db.create_engine("sqlite:///" + os.getenv("SQLITE_PATH"))
    except ArgumentError as e:
        raise (f"Error from sqlalchemy : {str(e)}")
    
    Session = sessionmaker()
    Session.configure(bind=engine)
    setup_db(engine)
    
    container.session.override(
        providers.Singleton(Session)
    )
    container.git_factory.override(
        providers.Factory(
            GithubFactory,
            g = Github(auth=Auth.Token(os.getenv('GITHUB_TOKEN')))
        )
    )
    container.db_interface.override(
        providers.Singleton(
            SQLite,
            session = container.session
        )
    )

@click.group()
def cli():
    pass

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
    
    repos_data = githubFactory.find_repos(min_stars, lang, nb_repo)
    for data in repos_data:
        table.add_row(data[0], data[1], data[2], data[3])
    console.print(table)

@click.command()
@click.option('--repository_name', envvar='REPOSITORY_NAME', default=os.getenv('REPOSITORY_NAME'), help='Name of the repository')
@inject
def get_data_repo(repository_name):
    max_id = sqlite.query_max_id()
    i = max_id if max_id != None else 0
    j = -1
    
    repo = githubFactory.get_repository(repository_name)
    sqlite.database_insert(repo)
    
    issues = list(githubFactory.get_issues())
    bar = IncrementalBar("Fetching data", max = len(issues))
    for issue in issues:
        j += 1
        bar.next()
        try:
            pull_request = githubFactory.get_pull_request(j)
            if not pull_request:
                logging.info("Pull Request not merged for issue: " + str(issue.id))
                continue
        except:
            logging.info("Error fetching pull request for the issue: " + str(issue.id))
            continue
        
        logging.info("Pull Request merged for issue: " + str(issue.id))
        sqlite.database_insert(issue)
        sqlite.database_insert(pull_request)
        sqlite.database_insert_many(list(githubFactory.get_comments(j)))
        sqlite.database_insert_many(list(githubFactory.get_modified_files(i)))
        logging.info("Committed data for issue: " + str(issue.id))
    
    bar.finish()

cli.add_command(get_data_repo)
cli.add_command(find_repo)

if __name__ == "__main__":
    container = Container()
    configure_session(container)
    
    githubFactory = container.git_factory()
    sqlite = container.db_interface()
    
    cli()