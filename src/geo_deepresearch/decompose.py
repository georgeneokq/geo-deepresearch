from openai import AsyncOpenAI
from pydantic import BaseModel
from geo_deepresearch.util.llm import call_llm

decomposer_instructions = """
Role:
You are to decompose query into parts, tagging each part with a category.

Instructions:
You will receive a query to conduct deep research on.
Expect that the query could span multiple topics.
Break the query down enough such that specialized sub-agents can be spawned for each query.
You may create new sub-queries as needed even if not explicitly specified.
For example, if asked to perform analysis of a company's stock, you may choose to spawn not only "finance" subagent for stock price analysis, but also a subagent with expertise "news" to research on macroeconomic news.

Sub-agent expertise list:
- cti (Cyber Threat Intelligence)
- finance (market data, stocks, commodities, cryptocurrency prices)
- general (anything that doesn't fall into the rest of the categories)

Output format is a JSON object in the following format:
{
  "subqueries": [{"expertise": "cti", "query": "IOCs of APT42"}]
}

""".strip()

class DecomposerOutputItem(BaseModel):
    expertise: str
    query: str


class DecomposerOutput(BaseModel):
    subqueries: list[DecomposerOutputItem]

async def decompose_query(client: AsyncOpenAI, model: str, query: str) -> DecomposerOutput:
    message = await call_llm(client, model, decomposer_instructions, query, temperature=0.2, output_schema=DecomposerOutput)
    parsed_response = message.parsed
    assert isinstance(parsed_response, DecomposerOutput)
    return parsed_response
