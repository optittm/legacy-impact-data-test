import ast
import logging
import astunparse
import os
import re
import torch

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
    
    def init_repo(self, repoFullName: str):
        self.repoName = repoFullName.split("/")[-1]
        self.path_repos = f"./test/{self.repoName}"
        return self.path_repos
    
    def get_max_file_score_from_issue(self, text_issue: str):
        """Finds the file and maximum semantic similarity score for a given issue text.
        
        Parameters:
            text_issue (str): The text of the issue to find the most similar code for.
        
        Returns:
            Tuple[str, float]: The relative file path of the most similar code and the maximum semantic similarity score."""
        text = text_issue
        file = ''
        max_similitude = float('-inf')
        regex_real_file_path = fr"\.\/test\/{self.repoName}(.+)"
        self.functions_sources = []
        
        self.__embed_code()

        function_bar = IncrementalBar(f"Generating semantic token via LLM", max=len(self.functions_sources))
        for function_source in self.functions_sources:
            function_bar.next()
            if len(function_source[1]) > 24800:
                logging.info(f"a function in {function_source[0]} was skipped because it's too big !")
                continue
            try:
                input_ids = self.tokenizer(function_source[1], return_tensors="pt").input_ids.to(self.device)
                
                generated_ids = self.codeT5.generate(input_ids, max_length=20)
                function_source.append(self.tokenizer.decode(generated_ids[0], skip_special_tokens=True))

                sentences = [text, function_source[2]]
                
                #Compute embedding for both lists
                embedding_1= self.bert.encode(sentences[0], convert_to_tensor=True)
                embedding_2 = self.bert.encode(sentences[1], convert_to_tensor=True)
                
                if max_similitude < util.pytorch_cos_sim(embedding_1, embedding_2):
                    max_similitude = util.pytorch_cos_sim(embedding_1, embedding_2)
                    file = function_source[0]
                
                torch.cuda.empty_cache()
                
            except:
                file_functions = open("FunctionsToAvoid.txt", "a")
                file_functions.write(function_source[1])
                torch.cuda.empty_cache()
                os.system(".venv\\Scripts\\activate.bat && python main.py semantic-test-repo")

        function_bar.finish()
        match = re.search(regex_real_file_path, file)
        return match.group(1).replace("\\", "/"), max_similitude.item()
    
    def __embed_code(self):
        """Recursively walks through the repository directory and extracts the source code of all Python functions found in the files.
    
        The extracted function source code is stored in the `self.functions_sources` list, where each element is a list containing the file path and the function source code."""
        for root, dirs, files in os.walk(self.path_repos):
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