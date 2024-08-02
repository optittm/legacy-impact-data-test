# legacy-impact-data-test

This project's goal is to compare different methods of semantic search on GitHub repositories

## Installation

Create a [virtual environnement](https://docs.python.org/3/library/venv.html) and add all the dependencies needed with :
```
$ python -m venv c:\path\to\myenv
$ pip install -r requirements.txt
```

## Usage

- Fill a .env file like the .env-example for the default parameters of the inputs.
- A [Github Personnal Token](https://github.com/settings/tokens) is required (only 60 API calls per hour otherwise)

You are ready to call the script with your cli !

### Options

- get-data-repo : get the data of the Github repository put in the .env file.
    - --repository_name : name of the repository to get the data from
- find-repo : find public repositories on Github which have over the minimum amount of stars and the language put in the .env file
    - --lang : language of the repository to find
    - --min_stars : minimum amount of stars of the repository to find
    - --nb_repo : number of repositories to find
- semantic-test-repo : uses CodeT5 or Algorthmic Methods to get the probability of all files being the one to modify when comparing to issues in the db
    - --repository_name : name of the repository to test\
    To change between CodeT5, Algorthmic Methods and Generative AI, change the value of ```container.semantic_test``` and ```container.db_embedding``` in the function ```__configure_session``` in ```main.py```

Every command has a --help option available to get more info on the current cli call.

### Examples

```
$ python main.py find-repo --lang python --nb_repo 20
```
![Result](/assets/Example_find-repo.png)

```
$ python main.py get-data-repo --repository_name "nvbn/thefuck"
```
Fetching files ⣾\
Fetching issues |████████████████████████████████| 41/41\
Fetching pulls |████████████████████████████████| 41/41\
Fetching data |████████████████████████████████| 34/34

## Jupyter Notebooks

There are 3 notebooks in the project :
- big_functions : study of the functions that are too big when tokenizing them for CodeT5
- interpretResults : study of the results with CodeT5
- issueStudy : study of the quality of issues to see if it impacts the CodeT5 results

Those notebooks can also be used to compare with the Algorithmic Methods. However, I couldn't get enough results before the end of my internship to compare.

## What's Next ?

Improvement to the semantic search, are to be added : 
- Improvement to the Algorithmic Method following the state of the art made.
- Adding more semantic search methods like with Generative AI.

Real comparison between all the semantic search methods used is to be added.