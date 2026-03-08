from pydantic import BaseModel
from geo_deepresearch.util.llm import (
    call_llm,
    openai_default_client,
    openai_default_model,
)

class CitationCountExtractionResult(BaseModel):
    num_citations: int

async def extract_citation_count(report: str):
    # LLM to extract out the number of sources referenced inside the final report
    source_count_extraction_prompt = """
Given a report, return the number of references at the end of the report.
Return only JSON in this format: {"num_citations": 5}
""".strip()

    result = await call_llm(
        openai_default_client,
        openai_default_model,
        source_count_extraction_prompt,
        report,
        output_schema=CitationCountExtractionResult,
        temperature=0
    )

    if not isinstance(result.parsed, CitationCountExtractionResult):
        # Unexpected; if this happens it is not necessarily program bug
        raise RuntimeError("LLM as a judge for citation counting failed.")
    
    return result.parsed.num_citations
