from openai import AsyncOpenAI
from pydantic import BaseModel
from geo_deepresearch.util.llm import call_llm

decomposer_instructions = """
Role:
You are to decompose query into parts, tagging each part with a category.

Instructions:
- You will receive a query to conduct deep research on.
- Expect that the query could span multiple topics.
- Break the query down enough such that specialized sub-agents can be spawned for each query.
- Phrase each subquery to be concise and Google Search optimized, do not use full sentences.
- Keep the query concise.
- If the query is already simple enough, spawn only one agent.

Sub-agent expertise list:
- cti (Cyber Threat Intelligence)
- finance (market data, stocks, commodities, cryptocurrency prices)
- general (anything that doesn't fall into the rest of the categories)

Output format is a JSON object in the following format:
{
  "subqueries": [{"expertise": "cti", "query": "IOCs of APT42"}]
}

## Examples:

### Good examples

- "IOCs of APT42"
    - Subagent 1: "IP addresses of APT42"
    - Subagent 2: "Malware hashes of APT42"
    - Subagent 3: "APT42 C2 domains"

- "Bitcoin, ethereum, gold price trends comparison"
    - Subagent 1: "Bitcoin trends"
    - Subagent 2: "Bitcoin trends"
    - Subagent 3: "Gold trends"

### Bad examples

Do not overload a single agent, like the examples below:

- "List and categorize the most recent operational IOCs (malware hashes, C2 domains, IP addresses) associated with APT42."
- "APT42 latest operational IOCs malware hashes C2 domains IPs"
- "Bitcoin trends and gold trends"

""".strip()

class DecomposerOutputItem(BaseModel):
    expertise: str
    query: str


class DecomposerOutput(BaseModel):
    subqueries: list[DecomposerOutputItem]

async def decompose_query(client: AsyncOpenAI, model: str, query: str) -> DecomposerOutput:
    message = await call_llm(client, model, decomposer_instructions, query, output_schema=DecomposerOutput)
    parsed_response = message.parsed
    assert isinstance(parsed_response, DecomposerOutput)
    return parsed_response
