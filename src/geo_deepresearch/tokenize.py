import os

os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from geo_deepresearch.tokenizer_manager import get_tokenizer
from geo_deepresearch.util.logging import get_logger

logger = get_logger()

def count_tokens(input_text: str):
    """
    Uses the tokenizer to calculate tokens of given contents
    """
    # Load the tokenizer
    tokenizer = get_tokenizer(os.environ.get("TOKENIZER_DIR", "../tokenizer"))

    # Tokenize and count
    tokens = tokenizer.encode(input_text)

    return len(tokens)


def preload_tokenizer():
    from geo_deepresearch.tokenizer_manager import get_tokenizer

    tokenizer_dir = os.environ.get("TOKENIZER_DIR", "../tokenizer")
    logger.info(f"Preloading tokenizer from {tokenizer_dir}...")
    get_tokenizer(os.environ.get("TOKENIZER_DIR", "../tokenizer"))


if __name__ == "__main__":
    test_string = "Doesn't does not You are to, I am. Favr the people"
    print(f"Input: {test_string}")
    print(f"Token count: {count_tokens(test_string)}")
