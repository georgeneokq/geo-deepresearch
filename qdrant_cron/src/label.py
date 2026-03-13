import json
import os
from openai import AsyncOpenAI
from util.llm import call_llm, extract_json_from_llm_output
from util.logger import get_logger

logger = get_logger()

LABELLER_INSTRUCTIONS = """
You will be prepending a title to a text chunk, to optimize it for vector and keyword search.
Based on the document title and the chunk's surrounding text, output an appropriate title to prepend to it.
Include technical keywords in the label.
If the surrounding text does not provide enough context to give a specific label for that chunk, you may output a more generic label based on the document title.

Output in this JSON format:
{\"label\": \"your-label-here\"}
""".strip()

openai_client = AsyncOpenAI(
    api_key=os.environ.get("CHUNK_LABELLER_MODEL_API_KEY"),
    base_url=os.environ.get("CHUNK_LABELLER_MODEL_BASE_URL"),
)
openai_model = os.environ.get("CHUNK_LABELLER_MODEL", "qwen/qwen3.5-9b")


async def get_chunk_label(text: str, full_document_content: str, document_title: str):
    """
    Labels a chunk of text based on title and surrounding text in the document.
    Expects the text to be an exact substring, so as to extract the surrounding text.
    """
    try:
        substring_index = full_document_content.index(text)
    except ValueError:
        # Unexpected value error, return document title as fallback
        logger.error(
            f'Falling back to using document title as label due to unexpected ValueError: Substring not found for chunk "{text}".'
        )
        return document_title

    # Max surrounding character count, applied for both before and after
    # Total is hence x2 of the value specified.
    max_surrounding_character_count = 200
    text_before = full_document_content[
        max(0, substring_index - max_surrounding_character_count) : substring_index
    ]
    text_after = full_document_content[
        substring_index
        + len(text) : min(
            substring_index + len(text) + max_surrounding_character_count,
            len(full_document_content),
        )
    ]
    user_prompt = f"""
- Document title: {document_title}
- Text Before: \"{text_before}\"
- Text Chunk (label this): \"{text}\"
- Text After: \"{text_after}\"
""".strip()
    result = await call_llm(
        openai_client, openai_model, LABELLER_INSTRUCTIONS, user_prompt
    )

    if not result.content:
        logger.error(
            f'Falling back to using document title as label due to empty content from LLM call for chunk "{text}".'
        )
        return document_title

    parsed_json: dict = json.loads(extract_json_from_llm_output(result.content))
    label = parsed_json.get("label")

    if not isinstance(label, str):
        logger.error(
            f'Falling back to using document title as label due to failed extraction from LLM call for chunk "{text}".'
        )
        return document_title

    logger.debug(f"Chunk: {text[:150]}\nLabel: {label}")
    return label
