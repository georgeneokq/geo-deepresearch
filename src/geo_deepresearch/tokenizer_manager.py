import os
from transformers import AutoTokenizer

# Global dictionary to hold loaded instances
_instances = {}

def get_tokenizer(tokenizer_folder: str):
    """
    Returns a cached tokenizer instance. 
    Loads from disk only if it's the first time being called.
    """
    if tokenizer_folder not in _instances:
        tokenizer_dir = os.path.abspath(os.environ.get("TOKENIZER_DIR", "../tokenizer"))
        
        print(f"--- Loading {tokenizer_folder} into memory... ---")
        _instances[tokenizer_folder] = AutoTokenizer.from_pretrained(
            tokenizer_dir,
            local_files_only=True,
            trust_remote_code=True
        )
    return _instances[tokenizer_folder]