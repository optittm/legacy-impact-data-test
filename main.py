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

logging.basicConfig(filename='logs.log', level=logging.DEBUG)

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
    container.db_interface.override(
        providers.Singleton(
            SQLite,
            session = container.session
        )
    )
    container.git_factory.override(
        providers.Factory(
            GithubFactory,
            g = Github(auth=Auth.Token(os.getenv('GITHUB_TOKEN'))),
            db = container.db_interface
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
    """find_repo command to search for GitHub repositories based on criteria.

    Parameters:
    - min_stars: Minimum number of stars for repository to be included.
    - lang: Language to filter repositories by. 
    - nb_repo: Max number of repositories to return.

    Prints a table with repository name, stars, issues, topics, and URL.
    Uses the injected githubFactory to search GitHub and find repositories 
    matching the criteria."""

    console = Console()
    table = Table(title="Repositories")
    columns = ["FullName", "Stars", "Issues", "Size", "Url"]
    for column in columns:
        table.add_column(column, justify="center")
    
    repos_data = githubFactory.find_repos(min_stars, lang, nb_repo)
    for data in repos_data:
        table.add_row(data[0], data[1], data[2], data[3], data[4])
    console.print(table)

@click.command()
@click.option('--repository_name', envvar='REPOSITORY_NAME', default=os.getenv('REPOSITORY_NAME'), help='Name of the repository')
@inject
def get_data_repo(repository_name):
    """Fetches and stores data for a given GitHub repository.

    Iterates through the pull  and pull requests for the repository, 
    fetching additional data like comments and modified files. Stores all
    the data in a local SQLite database for later analysis.

    Parameters:
        repository_name: The name of the GitHub repository to fetch data for."""
    
    j = -1
    sqlite.database_insert(githubFactory.get_repository(repository_name))
    sqlite.database_insert_many(list(githubFactory.get_gitFile()))
    
    pullList, pulls, issueNumbers = githubFactory.get_pull_requests()
    bar = IncrementalBar("Fetching data", max = len(issueNumbers))
    for pull, pullItem, issueNumber in zip(pulls, pullList, issueNumbers):
        j += 1
        bar.next()
        newPullId = sqlite.database_insert(pullItem)
        issue, issueItem = githubFactory.get_issue(issueNumber)
        newIssueId = sqlite.database_insert(issueItem)
        sqlite.database_update_issueId_pullRequest(pullItem.githubId, newIssueId)
        sqlite.database_insert_many(list(githubFactory.get_comments(issue, newIssueId)))
        sqlite.database_insert_many(list(githubFactory.get_modified_files(pull, newPullId)))
        logging.info("Committed data for issue: " + str(pullItem.issueId))
    
    bar.finish()

cli.add_command(get_data_repo)
cli.add_command(find_repo)

if __name__ == "__main__":
    container = Container()
    configure_session(container)
    
    sqlite = container.db_interface()
    githubFactory = container.git_factory()
    
    cli()