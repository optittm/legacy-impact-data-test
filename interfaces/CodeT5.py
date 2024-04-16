import ast
import astunparse
import os
import re

from interfaces.SemanticTest import SemanticTest
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModel, AutoTokenizer
from progress.bar import IncrementalBar

class CodeT5(SemanticTest):
    
    def __init__(self, repoFullName):
        self.repoFullName = repoFullName
        self.repoName = self.repoFullName.split("/")[-1]
        self.path_repos = f"./test/{self.repoName}"
        
        checkpoint = "Salesforce/codet5p-220m-bimodal"
        self.device = "cpu" #or "cuda"
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)
        self.codeT5 = AutoModel.from_pretrained(checkpoint, trust_remote_code=True).to(self.device)
        self.bert = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def test_issue(self, text_issue):
        text = text_issue
        file = ''
        max_similitude = float('-inf')
        regex_real_file_path = fr"\.\/test\/{self.repoName}\\(.+)"
        self.functions_sources = []
        
        self.__embed_code()
        
        function_bar = IncrementalBar(f"Generating semantic token ", max=len(self.functions_sources))
        for function_source in self.functions_sources:
            function_bar.next()
            input_ids = self.tokenizer(function_source[1], return_tensors="pt").input_ids.to(self.device)
            
            generated_ids = self.codeT5.generate(input_ids, max_length=20)
            function_source.append(self.tokenizer.decode(generated_ids[0], skip_special_tokens=True))
        
        function_bar.finish()
        function_bar2 = IncrementalBar(f"Computing semantic similarity ", max=len(self.functions_sources))
        
        for function_source in self.functions_sources:
            function_bar2.next()
            sentences = [text, function_source[2]]
            
            #Compute embedding for both lists
            embedding_1= self.bert.encode(sentences[0], convert_to_tensor=True)
            embedding_2 = self.bert.encode(sentences[1], convert_to_tensor=True)
            
            if max_similitude < util.pytorch_cos_sim(embedding_1, embedding_2):
                max_similitude = util.pytorch_cos_sim(embedding_1, embedding_2)
                file = function_source[0]
        
        function_bar2.finish()
        match = re.search(regex_real_file_path, file)
        return match.group(1).replace("\\", "/"), max_similitude.item()
        # print(f"Le fichier qui match le plus est {match.group(1)} avec une sim cos de {max_similitude}")
    
    def create_test_repo(self, shaBase):
        if not os.path.exists(self.path_repos):
            if not os.path.exists("./test"):
                os.mkdir("./test")
            os.system(f"cd ./test && git clone https://github.com/{self.repoFullName}")
        
        os.system(f"cd {self.path_repos} && git checkout {shaBase}")
    
    def __embed_code(self):
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
        if isinstance(node, ast.FunctionDef):
            return astunparse.unparse(node)