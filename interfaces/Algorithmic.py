import re
import os
import nltk
import sqlite3
import pickle

from nltk.corpus import words, wordnet
from autocorrect import Speller
from pygments.token import Token
from pygments.lexers import get_lexer_for_filename
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from interfaces.SemanticTest import SemanticTest
from progress.bar import IncrementalBar

class Algorithmic(SemanticTest):
    def __init__(self):
        try:
            nltk.data.find('corpora/wordnet.zip')
            nltk.data.find('corpora/words.zip')
        except LookupError:
            nltk.download('wordnet')
            nltk.download('words')
        self.conn = sqlite3.connect('transformed_texts.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS transformed_texts (
            file_path TEXT PRIMARY KEY,
            transformed_text BLOB
            )''')
        self.conn.commit()
    
    def init_repo(self, repoFullName: str):
        self.repoName = repoFullName.split("/")[-1]
        self.path_repos = f"./test/{self.repoName}"
        return self.path_repos
    
    def __save_transformed_text_to_db(self, file_path, transformed_text):
        self.c.execute('INSERT OR REPLACE INTO transformed_texts (file_path, transformed_text) VALUES (?, ?)', (file_path, pickle.dumps(transformed_text)))
        self.conn.commit()

    def __get_transformed_text_from_db(self, file_path):
        self.c.execute('SELECT transformed_text FROM transformed_texts WHERE file_path = ?', (file_path,))
        row = self.c.fetchone()
        if row:
            return pickle.loads(row[0])
        return None
    
    def __expand_acronyms_with_wordnet(self, text):
        expanded_text = text
        pattern = re.compile(r'\b[A-Z]+\b')
        acronyms = pattern.findall(text)
        for acronym in acronyms:
            synsets = wordnet.synsets(acronym)
            if synsets:
                hypernyms = synsets[0].hypernyms()
                if hypernyms:
                    expansion = hypernyms[0].lemmas()[0].name().replace('_', ' ')
                    expanded_text = expanded_text.replace(acronym, expansion)
        return expanded_text

    # Modified replace_acronyms function
    def __replace_acronyms(self, text):
        english_word_set = set(words.words())
        expanded_text = self.__expand_acronyms_with_wordnet(text)
        for word in text.split():
            if word.isupper():
                if word.lower() in english_word_set:
                    expanded_text = expanded_text.replace(word, word.lower())
        return expanded_text
    
    def __split_function_name(self, s):
        """Splits a function name into diferent words, e.g.:
            thisIsMyVariable => "this is my variable"
            this_is_my_variable => "this is my variable"
        Args:
            s (_type_): _description_

        Returns:
            _type_: _description_
        """
        # use map to add an underscore before each uppercase letter
        modified_string = list(map(lambda x: '_' + x if x.isupper() else x, s))
        # join the modified string and split it at the underscores
        split_string = ''.join(modified_string).split('_')
        # remove any empty strings from the list
        split_string = list(filter(lambda x: x != '', split_string))
        return " ".join(split_string)
    
    def __transform_code_into_text(self, filename, recalculate=False):
        if not recalculate:
            cached_text = self.__get_transformed_text_from_db(filename)
            if cached_text is not None:
                return cached_text

        with open(filename, encoding="utf8") as f:
            lines = ''.join(f.readlines())

        s = ""
        lexer = get_lexer_for_filename(filename)
        tokens = lexer.get_tokens(lines)
        for token in tokens:
            if token[0] == Token.Literal.String.Doc:
                s = s + ' ' + token[1]
            elif token[0] == Token.Comment.Single:
                s = s + ' ' + token[1]
            elif token[0] == Token.Comment.Multiline:
                s = s + ' ' + token[1]
            elif token[0] == Token.Literal.String.Single:
                if token[1] not in ["'", ':', ';']:
                    s = s + ' ' + token[1]
            elif token[0] == Token.Name.Function:
                s = s + ' ' + self.__split_function_name(token[1])
            elif token[0] == Token.Name:
                s = s + ' ' + self.__split_function_name(token[1])

        s = " ".join(s.split())
        s = self.__replace_acronyms(s)
        spell = Speller()
        s = spell(s)

        self.__save_transformed_text_to_db(filename, s)
        return s
    
    def __text_similarity_scikit(self, text1, text2):
        # Convert the texts into TF-IDF vectors
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([text1, text2])

        # Calculate the cosine similarity between the vectors
        similarity = cosine_similarity(vectors)
        return similarity
    
    def get_max_file_score_from_issue(self, text: str, files_to_recalculate=[]):
        s1 = []
        max_score = 0
        regex_real_file_path = fr"\.\/test\/{self.repoName}\\(.+)"
        function_bar = IncrementalBar(f"Generating semantic token via Algorithmic", max=sum(len(files) for _, _, files in os.walk(self.path_repos)))
        
        for root, _, files in os.walk(self.path_repos):
            for file in files:
                function_bar.next()
                if file.endswith('.py'):
                    filename = os.path.join(root, file)
                    if files_to_recalculate is not None:
                        recalculate = re.search(regex_real_file_path, filename).group(1).replace("\\", "/") in files_to_recalculate
                    else:
                        recalculate = False
                    transformed_text = self.__transform_code_into_text(filename, recalculate)
                    score = self.__text_similarity_scikit(transformed_text, text)
                    s1.append([filename, score[0][1]])

        function_bar.finish()
        
        for input in s1:
            if max_score < input[1]:
                max_score = input[1]
                max_input = input[0]
        
        match = re.search(regex_real_file_path, max_input).group(1).replace("\\", "/")
        return match, max_score