import argparse
import os
from transformers import AutoTokenizer

def download_tokenizer():
    parser = argparse.ArgumentParser(description="Download Hugging Face tokenizer files into a local ./tokenizers/ directory.")
    
    # Required: The model ID from Hugging Face
    parser.add_argument(
        "model", 
        type=str, 
        help="Hugging Face model ID (e.g., 'zai-org/GLM-4.7-Flash')"
    )
    
    # Optional: The output subfolder name
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        help="Specific subfolder name. Defaults to the model name."
    )

    args = parser.parse_args()

    # 1. Setup the parent directory
    base_dir = "./tokenizers"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # 2. Determine the subfolder name
    # We replace '/' with '_' to prevent accidental nested folders from model IDs
    if args.output:
        subfolder_name = args.output
    else:
        subfolder_name = args.model.replace("/", "_")

    target_path = os.path.join(base_dir, subfolder_name)

    print(f"--- Downloading tokenizer for '{args.model}' ---")

    try:
        # 3. Fetch the tokenizer
        # This only pulls the config/vocab files (MBs), not the model weights (GBs)
        tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)

        # 4. Save to the target path
        tokenizer.save_pretrained(target_path)
        
        # 5. Summary
        files = os.listdir(target_path)
        print(f"\n[Success] Tokenizer saved to: {target_path}")
        print(f"Files: {', '.join(files)}")

    except Exception as e:
        print(f"\n[Error] Failed to download tokenizer.")
        print(f"Details: {e}")

if __name__ == "__main__":
    download_tokenizer()