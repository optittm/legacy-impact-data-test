import logging
import os
import click
import subprocess
import sqlalchemy as db

from github import Github, Auth
from rich.table import Table
from rich.console import Console
from progress.bar import IncrementalBar
from interfaces.Database.EmbeddingT5 import EmbeddingT5
from interfaces.Database.EmbeddingAlg import EmbeddingAlg
from interfaces.Semantic.CodeT5 import CodeT5
from interfaces.Semantic.Algorithmic import Algorithmic
from interfaces.Database.SQLite import SQLite
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
def __configure_session(container: Container):
    """Configures the SQLite database session and dependency injection container for the application.

    This function sets up the SQLite database connection, creates a session factory, and configures the dependency injection container with the necessary components:

    - SQLite database interface
    - GitHub API factory
    - Semantic code analysis components (CodeT5, Algorithmic)
    - Embedding components (EmbeddingT5, EmbeddingAlg)

    The function uses environment variables to retrieve the SQLite database path and GitHub API token. It also sets up the database schema using the `setup_db` function.

    The configured container is then returned, allowing the application to use the various components through dependency injection.
    """
    
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
    container.db_embedding.override(
        providers.Singleton(
            EmbeddingT5 # EmbeddingT5, EmbeddingAlg or EmbeddingGen (EmbeddingGen not implemented yet)
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
@click.option('--nb_result', envvar='NB_RESULT', default=os.getenv('NB_RESULT'), help='Number of results to return')
@inject
def semantic_test_repo(repository_name, nb_result):
    """Runs a semantic test on a given GitHub repository.

    This function retrieves the text and SHA values for each issue in the specified repository, and then performs a semantic test on the code changes associated with each issue.
    The results of the test are stored in a SQLite database.

    Parameters:
        repository_name (str): The name of the GitHub repository to test.
        nb_result (int): The number of top results to display for each issue.

    Returns:
        None"""
    
    text_and_shas = sqlite.get_shas_texts_and_issueId(repository_name)
    path = semantic.init_repo(repository_name, embedding)
    
    for title, body, sha, issueId in text_and_shas:
        if sqlite.issue_exists(issueId):
            logging.info(f"Issue {issueId} has already been treated. Skipping...")
            continue
        
        start = default_timer()
        file_diff = githubFactory.setup_repo(sha, repository_name, path)
        results = semantic.get_max_file_score_from_issue(title.join(', ' + body), file_diff)
        
        for i in range(int(nb_result)):
            print(f"the {i+1} result is {results[i][0]} with a score of {results[i][1]}")
        
        for result in results:
            try:
                fileId = sqlite.get_file_id_by_filename(result[0], sqlite.get_repoId_from_repoName(repository_name))
                result[0] = fileId
            except MissingFileException:
                logging.warning(f"No file found with name {result[0]} in repo {repository_name}")
                fileId = 0
        
        testResult = TestResult(issueId = issueId, results_array = str(results))
        sqlite.insert(testResult)
        end = default_timer()
        logging.info(f"duration of the test: {end - start}")
    
@click.command()
@inject
def test():
    """Runs a test command and checks for a specific error pattern in the output.

    This function performs the following steps:
    1. Activates the virtual environment using the `activate_command`.
    2. Runs the `main.py semantic-test-repo` command and captures the output.
    3. Checks the output for the error pattern "Token indices sequence length is longer than the specified maximum sequence length for this model".
    4. If the error pattern is found, it prints "Error detected: token too long", otherwise it prints "No error detected".
    5. Finally, it cleans up the embedding.

    This function is likely used for testing or debugging purposes, to ensure that the semantic test command is running without encountering the specified error."""
    
    activate_command = "cd .venv/Scripts && activate.bat && cd ../.."
    run_command = "python main.py semantic-test-repo"

    # Run activation command and capture output
    process = subprocess.Popen(activate_command, shell=True, text=True)
    process.communicate()

    if process.returncode != 0:
        print("Activation failed. Exiting.")
        return

    # Run main.py command and capture output
    process = subprocess.Popen(run_command, stderr=subprocess.PIPE, shell=True, text=True)
    _, stderr = process.communicate()
    error_pattern = "Token indices sequence length is longer than the specified maximum sequence length for this model"

    for line in stderr.splitlines():
        line = line.strip()
        print(line)
        if line.startswith(error_pattern):
            print("Error detected: token too long")
            #break
        else:
            print("No error detected")
    
    embedding.clean()

cli.add_command(semantic_test_repo)
cli.add_command(get_data_repo)
cli.add_command(find_repo)
cli.add_command(test)

if __name__ == "__main__":
    container = Container()
    __configure_session(container)
    
    sqlite = container.db_interface()
    githubFactory = container.git_factory()
    semantic = container.semantic_test()
    embedding = container.db_embedding()
    
    cli()

