import asyncio
import random
from typing import Optional
from openai import AsyncOpenAI
from geo_deepresearch.util.llm import call_llm, openai_default_client, openai_default_model

from geo_deepresearch.util.logging import get_logger

logger = get_logger()

async def summarize_for_final_report(
        main_query: str,
        subqueries: list[str],
        summaries: list[str],
        openai_client: Optional[AsyncOpenAI] = None,
        openai_model: Optional[str] = None
    ) -> str:
    """
    Reduces multiple reports into one main report.
    """
    if not openai_client:
        openai_client = openai_default_client

    if not openai_model:
        openai_model = openai_default_model

    num_summaries = len(summaries)

    # If no summaries after filtering, everything errored.
    if not num_summaries:
        return "Failed to complete research."
    elif num_summaries == 1:
        # If only one agent was spawned, return that as the result
        summary = summaries[0]
        return summary
    else:
        # Agent to analyze all answers from subagents, combine contents and citation list with deduplication.
        # To prevent context overflow, we pass in 2 summaries at a time, accumulating a main summary
        # and eventually reduce it to a single summary.

        # Use the first item in the arrays as the start
        first_subquery = subqueries[0]
        first_summary = summaries[0]

        main_report = f"# {main_query}\n\n##{first_subquery}\n\n{first_summary}"
        for attempt in range(1, len(summaries)):
            summary = summaries[attempt]
            subquery = subqueries[attempt]

            final_summarizer_instructions = f"""
You are a summarizer agent for the following topic: \"{main_query}\"
The user will send you the main report, followed by the sub-report. Merge the sub-report into the main report.
Re-index all citations. The final output must have a single, continuous numerical reference list (e.g., [1] through [N]) that matches the provided reports.
Ensure the statements are linked to the new citation numbers correctly.
""".strip()
            main_report_message = f"{main_report}"
            sub_report_message = f"## {subquery}\n\n{summary}"
            user_messages = [main_report_message, sub_report_message]

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = await call_llm(
                        openai_client,
                        openai_default_model,
                        final_summarizer_instructions,
                        user_messages,
                    )
                    if not result.content:
                        raise RuntimeError("LLM output is empty.")

                    main_report = result.content
                    break
                except Exception as e:
                    # Skip current sub-report if failed.
                    logger.warning(f"Attempt {attempt + 1} failed for sub-report {attempt}: {e}")
                    logger.debug("Retrying 1 more time due to summarization failure")

                    if attempt == max_retries - 1:
                        # If we just failed our last attempt, log error
                        logger.error(f"Exhausted all retries for sub-report {attempt}. Skipping.")
                
                # Exponential backoff with a little bit of random jitter (0 to 1000ms)
                wait_time = (2 ** attempt) + random.random()
                
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)

            logger.debug(f"Updated summary:\n{main_report}")

        return main_report
