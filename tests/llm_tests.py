import pytest
import json
from geo_deepresearch.util.llm import extract_json_from_llm_output

@pytest.fixture
def llm_output_json():
    return """
```json
{
    "key1": "value1",
    "key2": [
        "value2",
        "value3"
    ]
}
```
    """.strip()


def test_extract_json(llm_output_json):
    extracted_json = extract_json_from_llm_output(llm_output_json)
    print(extracted_json)
    parsed = json.loads(extracted_json)
    assert isinstance(parsed, dict)
