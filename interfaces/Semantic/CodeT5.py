import ast
import logging
import astunparse
import os
import re
import torch

from interfaces.Semantic.SemanticTest import SemanticTest
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
    
    def init_repo(self, repoFullName: str, embedding):
        """Initializes the repository path and other related attributes for the CodeT5 class.
        
        Args:
            repoFullName (str): The full name of the repository in the format "owner/repo".
            embedding (Embedding): The embedding object to be used for the repository.
        
        Returns:
            str: The path to the repository directory."""
        self.repoName = repoFullName.split("/")[-1]
        self.path_repos = f"./test/{self.repoName}"
        self.regex_real_file_path = fr"\.\/test\/{self.repoName}\\(.+)"
        self.regex_function_name = r"def\s+(\w+)"
        self.embedding_db = embedding
        return self.path_repos
    
    def get_max_file_score_from_issue(self, text_issue: str, recompute_files = None):
        """Finds the file and maximum semantic similarity score for a given issue text.
        
        Parameters:
            text_issue (str): The text of the issue to find the most similar code for.
        
        Returns:
            Tuple[str, float]: The relative file path of the most similar code and the maximum semantic similarity score."""
        self.__embed_code(recompute_files)
        return self.__compute_similarity(text_issue)
    
    def __separate_functions(self):
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
    
    def __embed_code(self, recompute_files = None):
        """Embeds the source code of all Python functions found in the repository directory into a vector representation.
        
        This method recursively walks through the repository directory and extracts the source code of all Python functions. It then generates an embedding for each function using a pre-trained language model (CodeT5) and stores the embeddings in a database.
        
        If the `recompute_files` parameter is provided, the method will recompute the embeddings for the specified files. Otherwise, it will only compute embeddings for files that do not have an existing embedding in the database.
        
        The generated embeddings are stored in the `self.embedding_db` attribute, which can be used to retrieve the embeddings later."""
        if recompute_files is None:
            recompute_files = []
        self.functions_sources = []
        
        self.__separate_functions()

        for function_source in self.functions_sources:
            file_path = re.search(self.regex_real_file_path, function_source[0]).group(1).replace("\\", "/")
            function_name = re.search(self.regex_function_name, function_source[1]).group(1)
            
            if file_path in recompute_files or self.embedding_db.get_embedding(file_path, function_name) is None:
                input_ids = self.tokenizer(function_source[1], return_tensors="pt").input_ids.to(self.device)
                
                if len(input_ids[0]) > self.tokenizer.model_max_length:
                    function_segments = self.__separate_loops(function_source[1])
                    if function_segments == [] :
                        continue
                    i = 0
                    for segment in function_segments:
                        i += 1
                        self.functions_sources.append([function_source[0], "def " + str(function_name) + str(i) + str(segment)])
                    continue

                generated_ids = self.codeT5.generate(input_ids, max_length=20)
                function_source.append(self.tokenizer.decode(generated_ids[0], skip_special_tokens=True))

                code_embedding = self.bert.encode(function_source[2], convert_to_tensor=True, show_progress_bar=False)
                self.embedding_db.save_embedding(file_path, function_name, code_embedding)

    def __compute_similarity(self, text_issue: str):
        """Computes the similarity between a given text issue and the source code of all functions in the repository.
        
        This method iterates through the list of function sources, retrieves the corresponding code embeddings from the database,
        and computes the cosine similarity between the issue embedding and the code embedding.
        The results are sorted in descending order by similarity and returned.
        
        Args:
            text_issue (str): The text of the issue for which to compute the similarity.
        
        Returns:
            list: A list of tuples, where each tuple contains the file path and the similarity score for a function."""
        result_similarity = []
        function_bar = IncrementalBar(f"Generating semantic token via LLM", max=len(self.functions_sources))
        
        for function_source in self.functions_sources:
            function_bar.next()
            file_path = re.search(self.regex_real_file_path, function_source[0]).group(1).replace("\\", "/")
            function_name = re.search(self.regex_function_name, function_source[1]).group(1)
            issue_embedding = self.bert.encode(text_issue, convert_to_tensor=True, show_progress_bar=False)
            
            try:
                code_embedding = self.embedding_db.get_embedding(file_path, function_name)
                if code_embedding is not None:
                    similarity = util.pytorch_cos_sim(issue_embedding, code_embedding).item()
                    result_similarity.append([file_path, similarity])
                    
                    torch.cuda.empty_cache()
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                torch.cuda.empty_cache()
        
        function_bar.finish()
        return sorted(result_similarity, key=lambda x: x[1], reverse=True)
    
    def __separate_loops(self, function: str):
        try:
            tree = ast.parse(function)
        except:
            logging.error(f"Error parsing {function}")
            return []

        class LoopVisitor(ast.NodeVisitor):
            def __init__(self):
                self.loops = []
                self.nested_loops = set()
            
            def visit_For(self, node):
                self.loops.append(node)
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.loops.append(node)
                self.generic_visit(node)
            
            def visit(self, node):
                if isinstance(node, (ast.For, ast.While)):
                    parent = getattr(node, 'parent', None)
                    if parent and isinstance(parent, (ast.For, ast.While, ast.Try)):
                        self.nested_loops.add(node)
                super().visit(node)
        
        def set_parents(node, parent=None):
            for child in ast.iter_child_nodes(node):
                child.parent = parent
                set_parents(child, child)
        
        set_parents(tree)
        visitor = LoopVisitor()
        visitor.visit(tree)
        top_level_loops = [loop for loop in visitor.loops if loop not in visitor.nested_loops]
        func_def = tree.body[0]
        source_lines = function.splitlines()
        segments = []
        prev_end_lineno = func_def.lineno - 1
        
        for loop in top_level_loops:
            start_lineno = loop.lineno - 1
            end_lineno = loop.end_lineno
            segments.append("\n".join(source_lines[prev_end_lineno:start_lineno]))
            segments.append("\n".join(source_lines[start_lineno:end_lineno]))
            prev_end_lineno = end_lineno
        
        segments.append("\n".join(source_lines[prev_end_lineno:]))
        segments = [segment for segment in segments if segment.strip()]
        return segments
    
    