import logging

from utils.containers import Container, providers
from dependency_injector.wiring import inject
from interfaces.gitFactory import GithubFactory

logging.basicConfig(filename='logs.log', encoding='utf-8', level=logging.DEBUG)

@inject
def main():
    repo = gitFactory.get_repository()
    # repo.save()
    issues = gitFactory.get_issues(repo)
    # issues.save()
    for issue in issues:
        try:
            pull_request = gitFactory.get_pull_requests(issue, repo)
            if pull_request.merged_at == None:
                logging.info("Pull Request not merged for issue: " + str(issue.id))
                continue
        except:
            logging.info("Error fetching pull request for the issue: " + str(issue.id))
            continue
        # pull_request.save()
        comments = gitFactory.get_comments(issue)
        # comments.save()
        modified_files = gitFactory.get_modified_files(pull_request)
        for file in modified_files:
            # file.save()
            continue

if __name__ == "__main__":
    container = Container()
    container.git_factory.override(
        providers.Factory(
            GithubFactory,
            session = container.session
        )
    )
    gitFactory = container.git_factory()
    
    main()