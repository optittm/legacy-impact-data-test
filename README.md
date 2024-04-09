# legacy-impact-data-test

## Installation

Create a [virtual environnement](https://docs.python.org/3/library/venv.html) and add all the dependencies needed :
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

Every command has a --help option available to get more info on the current cli call.

### Examples

```
$ python main.py find-repo --lang python --nb_repo 20
```
![Result](/assets/Example_find-repo.png)

```
$ python main.py get-data-repo --repository_name "nvbn/thefuck"
```
Fetching issues |████████████████████████████████| 41/41\
Fetching pulls |████████████████████████████████| 41/41\
Fetching data |████████████████████████████████| 34/34