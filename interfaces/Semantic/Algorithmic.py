import re
import os
import nltk

from nltk.corpus import words, wordnet
from autocorrect import Speller
from pygments.token import Token
from pygments.lexers import get_lexer_for_filename
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from interfaces.Semantic.SemanticTest import SemanticTest
from progress.bar import IncrementalBar

class Algorithmic(SemanticTest):
    def __init__(self):
        try:
            nltk.data.find('corpora/wordnet.zip')
            nltk.data.find('corpora/words.zip')
        except LookupError:
            nltk.download('wordnet')
            nltk.download('words')
    
    def init_repo(self, repoFullName: str, embedding):
        """Initializes a repository by setting the repository name, path, and regular expression for function names. It also stores the embedding object for the repository.
        
        Args:
            repoFullName (str): The full name of the repository in the format "owner/repo".
            embedding (object): The embedding object to be used for the repository.
        
        Returns:
            str: The path to the local repository."""
        self.repoName = repoFullName.split("/")[-1]
        self.path_repos = f"./test/{self.repoName}"
        self.regex_function_name = r"def\s+(\w+)"
        self.embedding_db = embedding
        return self.path_repos
    
    def __expand_acronyms_with_wordnet(self, text):
        """Expands acronyms in the given text using WordNet.
        
        Args:
            text (str): The input text to expand acronyms in.
        
        Returns:
            str: The input text with acronyms expanded."""
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
    
    def __replace_acronyms(self, text):
        """Replaces acronyms in the given text with their expanded forms, using a combination of WordNet and a list of English words.
        
        Args:
            text (str): The input text to replace acronyms in.
        
        Returns:
            str: The input text with acronyms replaced."""
        english_word_set = set(words.words())
        expanded_text = self.__expand_acronyms_with_wordnet(text)
        for word in text.split():
            if word.isupper():
                if word.lower() in english_word_set:
                    expanded_text = expanded_text.replace(word, word.lower())
        return expanded_text
    
    def __split_function_name(self, s):
        """Splits a function name into different words, e.g.:
            thisIsMyVariable => "this is my variable"
            this_is_my_variable => "this is my variable"
        
        Args:
            s (str): The function name to split.
        
        Returns:
            str: The function name split into individual words."""
        modified_string = list(map(lambda x: '_' + x if x.isupper() else x, s))
        split_string = ''.join(modified_string).split('_')
        split_string = list(filter(lambda x: x != '', split_string))
        return " ".join(split_string)
    
    def __transform_code_into_text(self, filename, recalculate):
        """Transforms the code in the given file into a text representation by extracting comments, strings, and function/variable names.
        
        Args:
            filename (str): The path to the file to transform.
            recalculate (bool): Whether to recalculate the text representation or use a cached version.
        
        Returns:
            str: The text representation of the code in the file."""
        if recalculate is False:
            cached_text = self.embedding_db.get_embedding(filename)
            if cached_text is not None:
                return cached_text

        with open(filename, encoding="utf8") as f:
            lines = ''.join(f.readlines())

        s = ""
        lexer = get_lexer_for_filename(filename)
        tokens = lexer.get_tokens(lines)
        for token in tokens:  
            token_type, token_value = token[0], token[1]
            comments_tokens = {Token.Literal.String.Doc, Token.Comment.Single, Token.Comment.Multiline}
            name_tokens = {Token.Name.Function, Token.Name}

            if token_type in comments_tokens:
                s += ' ' + token_value
            elif token_type == Token.Literal.String.Single:
                if token_value not in ["'", ':', ';']:
                    s += ' ' + token_value
            elif token_type in name_tokens:
                s += ' ' + self.__split_function_name(token_value)

        s = " ".join(s.split())
        s = self.__replace_acronyms(s)
        spell = Speller()
        s = spell(s)

        self.embedding_db.save_embedding(filename, s)
        return s
    
    def __text_similarity_scikit(self, text1, text2):
        """Calculates the text similarity between two input texts using the scikit-learn TF-IDF vectorizer and cosine similarity.
        
        Args:
            text1 (str): The first text to compare.
            text2 (str): The second text to compare.
        
        Returns:
            list: A list containing the cosine similarity score between the two input texts."""
        # Convert the texts into TF-IDF vectors
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([text1, text2])

        # Calculate the cosine similarity between the vectors
        similarity = cosine_similarity(vectors)
        return similarity
    
    def get_max_file_score_from_issue(self, text: str, files_to_recalculate=[]):
        """Generates a list of files and their similarity scores to the given text, sorted in descending order by similarity score.
        
        Args:
            text (str): The text to compare against the files.
            files_to_recalculate (list, optional): A list of file paths to recalculate the similarity score for. Defaults to an empty list.
        
        Returns:
            list: A list of tuples, where the first element is the file path and the second element is the similarity score."""
        s1 = []
        recalculate = False
        regex_real_file_path = fr"\.\/test\/{self.repoName}\\(.+)"
        function_bar = IncrementalBar(f"Generating semantic token via Algorithmic", max=sum(len(files) for _, _, files in os.walk(self.path_repos)))
        
        for root, _, files in os.walk(self.path_repos):
            for file in files:
                function_bar.next()
                if file.endswith('.py'):
                    filename = os.path.join(root, file)
                    if files_to_recalculate is not None:
                        recalculate = re.search(regex_real_file_path, filename).group(1).replace("\\", "/") in files_to_recalculate
                    transformed_text = self.__transform_code_into_text(filename, recalculate)
                    score = self.__text_similarity_scikit(transformed_text, text)
                    s1.append([filename, score[0][1]])

        function_bar.finish()
        
        for input in s1:
            input[0] = re.search(regex_real_file_path, input[0]).group(1).replace("\\", "/")
        return sorted(s1, key=lambda x: x[1], reverse=True)
    
    