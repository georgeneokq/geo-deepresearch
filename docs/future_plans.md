# Planned Improvements

This document outlines planned enhancements and future development directions for the Geo DeepResearch system. The improvements are organized by priority and area of impact, ranging from immediate refinements to the internal document retrieval pipeline to longer-term architectural extensions.

## Dynamic Document Reading Criteria

The current condition for retrieving a complete internal document requires at least two chunks from a given file to have a similarity score above 0.4. This threshold works adequately for small documents under approximately 10 pages, but becomes insufficient for larger documents exceeding 100 pages. The existing criteria is too permissive in such cases, potentially triggering full document retrieval for lengthy files where only a small fraction of content is actually relevant to the query.

The planned improvement involves implementing dynamic thresholds that scale based on document characteristics. For larger documents, the system would require a higher minimum number of high-scoring chunks before triggering full document retrieval. This adaptive approach would reduce unnecessary processing of redundant content and improve overall retrieval efficiency. The threshold adjustment could consider factors such as total document length, chunk distribution patterns, and the variance in similarity scores across chunks from the same document.

## Table Extraction and Reconstruction

The system currently uses Docling for table extraction from documents, which performs well for simple tables contained within a single page. However, tables that span multiple pages present significant challenges. When a table continues onto subsequent pages, the extracted representation may have missing columns, and merged cells are not duplicated into each affected row or column. This fragmentation compromises the semantic integrity of tabular data and can lead to information loss during downstream processing.

Several approaches are being considered to address this limitation. One option involves post-processing extracted tables to detect and reconstruct split tables by analyzing column alignment and content patterns across page boundaries. However, this is a non-trivial task requiring sophisticated heuristics to correctly identify table continuations and merge them appropriately.

An alternative approach under consideration involves leveraging a lightweight Vision Language Model (VLM) to interpret complex table structures. The VLM would receive rendered table images as input and output properly formatted markdown tables with correct cell alignments and merged cell handling. This approach could potentially handle more complex table layouts but would introduce additional computational overhead and dependency on VLM inference capabilities.

## Agent Specialization Framework

The current implementation includes a Cyber Threat Intelligence specialist agent and a general-purpose fallback agent for all other query types. While this demonstrates the framework's capability for domain-specific research, the agent ecosystem is planned for expansion to cover additional domains.

A planned addition is a live asset price agent that would demonstrate the framework's extensibility to financial data retrieval. This agent would serve as a reference implementation for creating new specialized agents and validate that the agent factory pattern can accommodate diverse domain requirements without significant architectural changes.

### Custom Tool Integration for Specialists

Currently, specialist agents differentiate themselves primarily through predefined source lists that are browsed before allowing the LLM to engage in free-form browsing. This approach works for guiding research toward authoritative sources but does not fully leverage domain-specific capabilities. For financial data retrieval, for example, internet search alone is suboptimal compared to direct API access to services like Yahoo Finance.

The planned enhancement would allow agent subclasses to define custom tools and inject additional instructions into underlying LLM calls. This would enable specialists to access domain-specific APIs, databases, or processing functions that are not available to general agents. However, this enhancement introduces a trade-off between capability and implementation complexity. The current design prioritizes simplicity by maintaining a uniform tool set across all agents, which reduces cognitive load when understanding agent behavior and simplifies debugging.

To balance these concerns, the enhancement would be implemented as an optional override mechanism. Agent subclasses could optionally specify custom tools and system prompt modifications only when necessary, preserving the default behavior for agents that do not require specialized capabilities. This approach maintains backward compatibility while enabling advanced use cases.

## Source Credibility and Temporal Relevance

The system currently lacks explicit guidance for evaluating source credibility and temporal relevance. LLMs are not instructed to critically assess whether a source is authoritative, biased, or potentially unreliable. Similarly, there is no mechanism for determining whether information is outdated for time-sensitive queries.

The planned improvement involves adding explicit instructions to LLM prompts requiring strict evaluation of source credibility. The model would be guided to consider factors such as the publisher's reputation, author credentials, citation patterns, and potential conflicts of interest. For temporal relevance, the model would compare the publication date against the query context and the current datetime (which is already appended to all prompts for temporal awareness) to determine whether the information remains current.

This enhancement would improve research quality by filtering out unreliable or obsolete sources, though it may increase the likelihood of sources being rejected during the browse phase, potentially requiring additional search iterations to meet minimum source requirements.

## Chunk Reordering for Context Coherence

The metadata stored for ingested documents in Qdrant includes the chunk index, which represents the sequential position of each chunk within the original document. This field was included specifically to enable reordering of retrieved chunks to restore their original sequence. However, this capability is not currently utilized during retrieval.

The planned enhancement would leverage chunk indices to reorder retrieved chunks before presenting them to the summarization module. When multiple chunks from the same document are retrieved, they would be sorted by chunk index to restore the original document flow. This reordering would improve context coherence during summarization, as information would be presented in the sequence intended by the original author rather than in arbitrary similarity-score order.

This improvement requires minimal implementation effort since the necessary metadata is already available, and it could provide immediate benefits to summary quality, particularly for documents where sequential context is important for accurate interpretation.

## Image Content Extraction

The current system does not process images embedded in documents, which represents a significant potential information loss. Images in threat intelligence reports often contain critical information such as attack diagrams, infrastructure maps, malware architecture illustrations, and data flow charts that are not captured in text alone.

The planned improvement involves incorporating a lightweight Vision Language Model capable of converting images to descriptive text. When documents are processed during ingestion, embedded images would be extracted and passed through the VLM, which would generate textual descriptions capturing the semantic content of the visual elements. These descriptions would then be included in the document chunks at appropriate positions, ensuring that image-derived information is available during retrieval and summarization.

Implementation challenges include selecting a VLM that balances accuracy with computational efficiency, handling various image formats and resolutions, and determining optimal placement of generated descriptions within the document structure. Due to time constraints, this enhancement may not be completed by the presentation date, but it remains a high-priority item for future development.

## End-to-End Testing Enhancement

The current end-to-end testing validates that the system can execute the complete research pipeline and produce reports with the expected number of citations. However, the test does not validate the completeness or accuracy of the extracted information relative to ground truth.

The planned improvement involves enhancing E2E tests to assert that the number of indicators of compromise (IOCs) retrieved meets a minimum threshold relative to the known total available on the internet. The target threshold is set at 95% initially, acknowledging that achieving 100% recall is challenging due to factors such as search result pagination limits, source accessibility issues, and LLM extraction errors.

This enhancement requires establishing ground truth datasets for test queries, which presents its own challenges. The current development effort is focused on diagnosing why research agents fail to extract all available IOCs even when those IOCs appear in search results. Potential causes include premature termination of the research loop, insufficient browsing depth, or extraction errors during summarization. Once the root causes are identified and addressed, the 95% threshold can be incrementally increased toward the ultimate goal of near-complete information retrieval.
