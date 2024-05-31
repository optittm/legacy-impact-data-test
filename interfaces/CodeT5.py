import ast
import logging
import astunparse
import os
import re
import torch
import sqlite3
import pickle

from interfaces.SemanticTest import SemanticTest
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModel, AutoTokenizer
from progress.bar import IncrementalBar

class CodeT5(SemanticTest):
    
    def __init__(self):
        checkpoint = "Salesforce/codet5p-220m-bimodal"
        self.device = os.getenv("DEVICE")
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
        self.codeT5 = AutoModel.from_pretrained(checkpoint, trust_remote_code=True).to(self.device)
        self.bert = SentenceTransformer(os.getenv('SENTENCE_TRANSFORMER'))
        self.functions_sources = []
        self.conn = sqlite3.connect('gitEmbeddings.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS embeddings (
            file_path TEXT PRIMARY KEY,
            embedding BLOB
            )''')
        self.conn.commit()
    
    def init_repo(self, repoFullName: str):
        self.repoName = repoFullName.split("/")[-1]
        self.path_repos = f"./test/{self.repoName}"
        self.regex_real_file_path = fr"\.\/test\/{self.repoName}\\(.+)"
        return self.path_repos
    
    def get_max_file_score_from_issue(self, text_issue: str, recompute_files = None):
        """Finds the file and maximum semantic similarity score for a given issue text.
        
        Parameters:
            text_issue (str): The text of the issue to find the most similar code for.
        
        Returns:
            Tuple[str, float]: The relative file path of the most similar code and the maximum semantic similarity score."""
        self.__embed_and_store_code(recompute_files)
        return self.__compute_similarity(text_issue)
    
    def __embed_code(self):
        """Recursively walks through the repository directory and extracts the source code of all Python functions found in the files.
    
        The extracted function source code is stored in the `self.functions_sources` list, where each element is a list containing the file path and the function source code."""
        for root, _, files in os.walk(self.path_repos):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    
                    parsed_tree = ast.parse(file_content)
                    functions = [
                        self.__extract_function_source(node)
                        for node in ast.walk(parsed_tree)
                        if isinstance(node, ast.FunctionDef)
                    ]
                    
                    if functions:
                        for function in functions:
                            self.functions_sources.append([
                                file_path,
                                function
                            ])
    
    def __extract_function_source(self, node):
        """Extracts the source code of a Python function from an AST node.
        
        Args:
            node (ast.FunctionDef): The AST node representing the function definition.
        
        Returns:
            str: The source code of the function."""
        if isinstance(node, ast.FunctionDef):
            return astunparse.unparse(node)
    
    def __embed_and_store_code(self, recompute_files = None):
        if recompute_files is None:
            recompute_files = []
        
        self.__embed_code()

        for function_source in self.functions_sources:
            file_path = re.search(self.regex_real_file_path, function_source[0]).group(1).replace("\\", "/")
            
            if file_path in recompute_files or self.__get_embedding_from_db(file_path) is None:
                input_ids = self.tokenizer(function_source[1], return_tensors="pt").input_ids.to(self.device)
                generated_ids = self.codeT5.generate(input_ids, max_length=20)
                function_source.append(self.tokenizer.decode(generated_ids[0], skip_special_tokens=True))
                
                embedding = self.bert.encode(function_source[2], convert_to_tensor=True)
                self.__save_embedding_to_db(file_path, embedding)
    
    def __compute_similarity(self, text_issue: str):
        file = ''
        max_similitude = float('-inf')
        function_bar = IncrementalBar(f"Generating semantic token via LLM", max=len(self.functions_sources))
        
        for function_source in self.functions_sources:
            function_bar.next()
            file_path = re.search(self.regex_real_file_path, function_source[0]).group(1).replace("\\", "/")
            
            try:
                embedding_2 = self.__get_embedding_from_db(file_path)
                if embedding_2 is not None:
                    embedding_1 = self.bert.encode(text_issue, convert_to_tensor=True)

                    similarity = util.pytorch_cos_sim(embedding_1, embedding_2).item()
                    if max_similitude < similarity:
                        max_similitude = similarity
                        file = file_path

                    torch.cuda.empty_cache()
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                torch.cuda.empty_cache()
        
        function_bar.finish()
        return file, max_similitude
    
    def __get_embedding_from_db(self, file_path):
        self.c.execute('SELECT embedding FROM embeddings WHERE file_path = ?', (file_path,))
        row = self.c.fetchone()
        if row:
            return pickle.loads(row[0])
        return None

    def __save_embedding_to_db(self, file_path, embedding):
        self.c.execute('INSERT OR REPLACE INTO embeddings (file_path, embedding) VALUES (?, ?)', (file_path, pickle.dumps(embedding)))
        self.conn.commit()
    
    def clean(self):
        self.conn.close()
        os.remove("./gitEmbeddings.db")
    
    