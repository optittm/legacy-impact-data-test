import re
import os
import nltk

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
    
    def init_repo(self, repoFullName: str):
        self.repoName = repoFullName.split("/")[-1]
        self.path_repos = f"./test/{self.repoName}"
        return self.path_repos
    
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
    
    def __transform_code_into_text(self, filename):
        # Get source code content
        f = open(filename, encoding="utf8")
        lines = ''.join(f.readlines())
        f.close()
        s = ""

        # See : https://pygments.org/docs/quickstart/
        #TODO: To be tested with C++ multi comment style, constants, etc.
        #TODO: remove comment mark
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
                if token[1] not in ["'",':', ';']:
                    s = s + ' ' + token[1]
            elif token[0] == Token.Name.Function:
                s = s + ' ' + self.__split_function_name(token[1]);
            elif token[0] == Token.Name:
                s = s + ' ' + self.__split_function_name(token[1]);     #Variable name

        # Remove duplicate spaces and new lines
        s = " ".join(s.split())

        # Expand acronyms
        s = self.__replace_acronyms(s)

        # Auto correct
        spell = Speller()
        s = spell(s)
        return s
    
    def text_similarity_scikit(self, text1, text2):
        # Convert the texts into TF-IDF vectors
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([text1, text2])

        # Calculate the cosine similarity between the vectors
        similarity = cosine_similarity(vectors)
        return similarity
    
    def get_max_file_score_from_issue(self, text: str):
        s1 = []
        max_score = 0
        regex_real_file_path = fr"\.\/test\/{self.repoName}\\(.+)"
        function_bar = IncrementalBar(f"Generating semantic token via Algorithmic", max=sum(len(files) for _, _, files in os.walk(self.path_repos)))
        
        for root, _, files in os.walk(self.path_repos):
            for file in files:
                function_bar.next()
                if file.endswith('.py'):
                    filename = os.path.join(root, file)
                    score = self.text_similarity_scikit(self.__transform_code_into_text(filename), text)
                    s1.append([filename, score[0][1]])
        function_bar.finish()
        
        for input in s1:
            if max_score < input[1]:
                max_score = input[1]
                max_input = input[0]
        
        match = re.search(regex_real_file_path, max_input)
        return match.group(1).replace("\\", "/"), max_score