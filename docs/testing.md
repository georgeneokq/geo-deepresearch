# Application Testing

The Geo DeepResearch application was tested using a combination of manual testing and automated testing across three distinct levels: unit tests, integration tests, and end-to-end (E2E) tests. The automated test suite is built using pytest with pytest-asyncio support for asynchronous test execution, and all tests are organized into separate directories according to their test level.

## Unit Testing

Unit tests focus on verifying the correctness of individual functions and components in isolation, without dependencies on external services. The unit test suite is located in the `tests/unit/` directory and is marked with the `@pytest.mark.unit` marker for selective execution.

The primary unit test validates the JSON extraction utility function `extract_json_from_llm_output` from the `geo_deepresearch.util.llm` module. This function is responsible for parsing JSON content from LLM responses, which may include markdown code block formatting. The test provides a sample LLM output containing a JSON object wrapped in markdown code fences with nested structures including strings and arrays. The test verifies that the function correctly extracts the raw JSON string by asserting that the extracted content can be successfully parsed by the standard JSON library into a dictionary object. This test ensures the system can reliably parse structured outputs from language models regardless of formatting variations in the response.

## Integration Testing

Integration tests verify the interaction between multiple components and include live LLM calls to test real model behavior. These tests are located in the `tests/integration/` directory and are marked with the `@pytest.mark.integration` marker. Integration tests depend on external API connections and are used to validate that components work correctly together with actual language model inference.

The integration test suite includes a test for citation count extraction from generated research reports. This test validates the `extract_citation_count` function from the `geo_deepresearch.util.testing` module, which uses an LLM as a judge to count the number of references in a final report. The test fixture provides a realistic sample report about APT42 cyber threat intelligence, containing multiple indicator of compromise (IOC) categories with citation markers and a references section with three URLs. The test invokes the extraction function asynchronously and asserts that the returned count equals three, matching the expected number of references in the sample report. This test ensures the system can accurately quantify the sources cited in generated reports, which is essential for validating research completeness and for automated quality checks during end-to-end testing.

All integration tests are instrumented with Langfuse observation decorators that trace test execution in the observability platform, enabling detailed analysis of LLM call performance, latency, and costs during testing.

## End-to-End Testing

End-to-end tests validate the complete research pipeline from query decomposition through final report generation. These tests are located in the `tests/e2e/` directory and are marked with the `@pytest.mark.e2e` marker. E2E tests exercise the full system with live LLM calls and external API integrations to verify that all components function correctly together in realistic scenarios.

The primary end-to-end test validates the system's ability to handle multiple cyber threat intelligence subagents running in parallel. The test begins by configuring debug-level logging to capture detailed execution traces. It defines a research topic focused on IOCs of APT42 and creates two decomposed subqueries: one for IOCs of APT42 and another for past incidents of APT42. Both subqueries are tagged with the cyber threat intelligence expertise category, which routes them to CTI-specialized research agents.

The test creates research agent instances for each subquery using the agent factory function `create_research_subagent`, which instantiates the appropriate agent class based on the expertise category. The agents are then executed in parallel through the `run_agents` orchestration function with a minimum source requirement of one. The test first asserts that both agents complete successfully and return results without raising exceptions.

After agent execution completes, the test invokes the final summarization module via `summarize_for_final_report`, which merges the individual agent summaries into a unified report with deduplicated citations. To validate the report quality, the test calculates the expected citation count by collecting all unique sources from the agent source lists into a set, then uses the LLM-based citation extraction utility to count the actual references in the generated report. The test asserts that the extracted citation count matches the expected count, verifying that the summarizer correctly preserved all sources without duplication or loss.

This end-to-end test validates multiple critical system capabilities simultaneously: query decomposition and routing, agent instantiation and execution, parallel research coordination, source tracking and deduplication, and final report generation with accurate citation management. The test is instrumented with Langfuse observation to provide complete traces of all LLM calls throughout the pipeline execution.

## Test Configuration and Execution

The test suite is configured through pytest settings in the `pyproject.toml` file. Asynchronous tests use the `auto` asyncio mode with function-scoped event loops. Custom pytest markers distinguish between test levels, enabling selective execution through pytest's marker expression syntax.

Tests can be run individually by test level using the following commands: unit tests via `pytest -m unit`, integration tests via `pytest -m integration`, and end-to-end tests via `pytest -m e2e`. Running the full test suite without markers executes all tests sequentially.

The testing infrastructure relies on several key dependencies including pytest version 9.0.2 or higher for the test framework and pytest-asyncio version 1.3.0 or higher for asynchronous test support. Langfuse integration provides observability during test execution, enabling performance analysis and debugging of LLM interactions.

## Manual Testing

In addition to automated tests, the system underwent manual testing during development to validate user-facing functionality and explore edge cases not covered by automated suites. Manual testing focused on verifying the FastAPI endpoint behavior through direct HTTP requests, validating research output quality across different query types and research modes, and testing error handling scenarios such as API failures and rate limit responses. The manual testing process was essential for identifying usability issues and validating that the system produces coherent, well-cited research reports across diverse topics.