# Geo DeepResearch

My own deep research implementation.

## Download tokenizer

This deep research system uses tokenizer for optimization.
Download the tokenizer files using `scripts/download_tokenizer.py`.
It uses the transformers library, you can use `uv` package manager to prevent polluting your system environment.

```bash
uv run --with transformers scripts/download_tokenizer.py zai-org/GLM-4.7-Flash
```

After it is installed, move the entire folder containing the tokenizer files into the root directory, and rename it to `tokenizer`.

The folder name `tokenizer` can be customized in .env file if you wish to use a different path.

## Run

```bash
cd src
uv run --env-file ../.env main.py
```
