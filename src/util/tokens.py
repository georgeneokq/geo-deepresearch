import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from tokenizer_manager import get_tokenizer

def count_tokens(input_text: str):
    """
    Uses the tokenizer to calculate tokens of given contents
    """
    # Load the tokenizer
    tokenizer = get_tokenizer(os.environ.get("TOKENIZER_DIR", "../tokenizer"))

    # Tokenize and count
    tokens = tokenizer.encode(input_text)
    
    # For debugging: Print tokenization strings
    # print("Tokens:")
    # print(tokenizer.convert_ids_to_tokens(tokens))

    return len(tokens)

if __name__ == "__main__":
    test_string = "Doesn't does not You are to, I am. Favr the people"
    print(f"Input: {test_string}")
    print(f"Token count: {count_tokens(test_string)}")
