import logging
import os
import re
import click
import subprocess
import sqlalchemy as db

from github import Github, Auth
from rich.table import Table
from rich.console import Console
from progress.bar import IncrementalBar
from interfaces.CodeT5 import CodeT5
from interfaces.Algorithmic import Algorithmic
from interfaces.SQLite import SQLite
from interfaces.GithubFactory import GithubFactory
from utils.containers import Container, providers
from dependency_injector.wiring import inject
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ArgumentError
from models.testResult import TestResult
from models.db import setup_db
from timeit import default_timer
from utils.missingFileException import MissingFileException

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
    container.semantic_test.override(
        providers.Factory(
            CodeT5 # CodeT5, Algorithmic or AIGEN (AIGEN not implemented yet)
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
    sqlite.insert(githubFactory.get_repository(repository_name))
    sqlite.insert_many(list(githubFactory.get_gitFiles()))
    
    pullList, pulls, issueNumbers = githubFactory.get_pull_requests()
    bar = IncrementalBar("Fetching data", max = len(issueNumbers))
    for pull, pullItem, issueNumber in zip(pulls, pullList, issueNumbers):
        j += 1
        bar.next()
        issue, issueItem = githubFactory.get_issue(issueNumber)
        if issue == 0 and issueItem == 0:
            continue
        newPullId = sqlite.insert(pullItem)
        newIssueId = sqlite.insert(issueItem)
        sqlite.update_issueId_pullRequest(pullItem.githubId, newIssueId)
        sqlite.insert_many(list(githubFactory.get_comments(issue, newIssueId)))
        sqlite.insert_many(list(githubFactory.get_modified_files(pull, newPullId)))
        logging.info("Committed data for issue: " + str(pullItem.issueId))
    
    bar.finish()

@click.command()
@click.option('--repository_name', envvar='REPOSITORY_NAME', default=os.getenv('REPOSITORY_NAME'), help='Name of the repository')
@inject
def semantic_test_repo(repository_name):
    text_and_shas = sqlite.get_shas_texts_and_issueId(repository_name)
    path = semantic.init_repo(repository_name)
    for title, body, sha, issueId in text_and_shas:
        if sqlite.issue_already_treated(issueId):
            logging.info(f"Issue {issueId} has already been treated. Skipping...")
            continue
        
        start = default_timer()
        
        file_diff = githubFactory.create_test_repo(sha, repository_name, path)
        results = semantic.get_max_file_score_from_issue(title.join(', ' + body), file_diff)
        try: fileId = sqlite.get_file_id_by_filename(results[0], sqlite.get_repoId_from_repoName(repository_name))
        except MissingFileException:
            logging.warning(f"No file found with name {results[0]} in repo {repository_name}")
            fileId = 0
        testResult = TestResult(score = results[1], issueId = issueId, gitFileId = fileId)
        
        sqlite.insert(testResult)
        
        end = default_timer()
        logging.info(f"duration of the test: {end - start}")
    
    

@click.command()
@inject
def test():
    command = "cd .venv/Scripts && activate.bat && cd ../.. && python main.py semantic-test-repo"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, text=True)
    stdout, _ = process.communicate()
    print(stdout)
    regex_error_pattern = r"Running this sequence through the model will result in indexing errors"
    if re.search(regex_error_pattern, stdout):
        print("Error detected: token too long")
    else:
        print("No error detected")
    
    semantic.clean()

cli.add_command(semantic_test_repo)
cli.add_command(get_data_repo)
cli.add_command(find_repo)
cli.add_command(test)

if __name__ == "__main__":
    container = Container()
    configure_session(container)
    
    sqlite = container.db_interface()
    githubFactory = container.git_factory()
    semantic = container.semantic_test()
    
    cli()

