# Introduction

## Background and motivation


This capstone project began with an evaluation of open-source deep research solutions over the past year. During this period, numerous open-source deep research systems emerged, many boasting high scores on benchmarks such as DeepResearch Bench, Humanity's Last Exam, and BrowseComp—placing second or even surpassing major commercial offerings like ChatGPT, Gemini, and DeepSeek.

Despite their strong benchmark performance, practical evaluation across cryptocurrency research, live asset price retrieval, indicator of compromise (IOC) list retrieval, and advanced persistent threat (APT) incident retrieval revealed significant limitations. Common issues included poor source credibility assessment (selecting blog posts over authoritative sources when better alternatives existed), lack of temporal awareness, and context overflow due to inadequate context management.

This made me realised that while benchmarks are important, they are not the only indicator of a great solution. This motivated me to tackle the issues above with my own solution instead of trying to modify existing ones, especially because the source code of the open source solutions I assessed were not created with integration with other systems in mind; for example, I had to analyze source code to find and extract out the parts for end to end automated research, decouple them from benchmarking code, and implement my own API server to expose the functionality to integrate with my own systems.


## Evaluation of Existing Solutions

As context for this project, I evaluated three open-source deep research solutions. To protect company confidentiality, they are referred to as Solution A, Solution B, and Solution C, listed in chronological order of evaluation.

| Solution | Description |
|----------|-------------|
| Solution A | The original deep research solution |
| Solution B | A deep research solution using a fine-tuned model (~30 billion parameters) trained for deep research tool-calling behavior |
| Solution C | A newer deep research solution using a fine-tuned model with a smaller base (~8 billion parameters) trained for deep research tool-calling behavior |

A later section details my original solution that achieves superior results using only a 4 billion parameter model compared to Solution C.

## Geo DeepResearch System

Building on insights from these evaluations, I developed Geo DeepResearch, a novel, opinionated multi-agent deep research system. The system automatically decomposes complex queries into specialized subtasks, each handled by domain-expert subagents. It conducts parallel research across internet sources and internal document repositories, then merges results into a unified, citation-backed report. On top of internet research, it contains components that support optimized ingestion and querying of internal documents, currently with a focus on PDF documents.

### Key Innovations

**Enhanced Retrieval Augmented Generation (RAG):** The system integrates RAG capabilities to ingest and query internal documents for sensitive or proprietary data through Qdrant vector database integration. Instead of just ingesting chunks, I have also attached metadata to enable retrieval of text surrounding that chunk, included a "chunk labeller" which increases vector retrieval accuracy by prefixing a label output by a past context-aware LLM, where the LLM decides a label not just based on the current processing chunk, but also surrounding context and past labels to detect continuation of previous chunks.

**Efficient Small-Model Performance:** The system enables smaller models to perform competitively through careful prompt engineering and aggressive context compaction via summarization. Rather than processing large raw documents, the LLMs work only with summaries relevant to the research topic. The pipeline is decomposed into small, sequential tasks that reduce cognitive load on individual model calls.

**Progressive Model Optimization:** Development progressed through multiple model scales:

| Model | Context Window | VRAM |
|-------|----------------|------|
| Cloud-based LLM (Gemini) | 1,000,000 tokens | N/A |
| Self-hosted 30B parameter (Q4 quantized) | 100,000 tokens | ~22 GB |
| Self-hosted 8B parameter fine-tuned (FP16) | 30,000 tokens | ~19 GB |
| Self-hosted 4B parameter (Q4 quantized) | 30,000 tokens | ~5 GB |

While model evolution contributed to improved capabilities, anti-hallucination behavior and effective operation within small context windows were achieved primarily through prompt engineering and context management strategies rather than relying solely on model capacity.

After creating my own deep research solution, I have succeeded in running a fully self-hosted deep research solution on my own laptop which has only 6VRAM GPU, in contrast to previously evaluated open source solutions which required either cloud LLMs or more powerful machines available in company office. It is also remarkably fast for a model self-hosted on a small laptop while remaining highly accurate.

**Temporal Awareness:** All LLM calls automatically append the current datetime to the system prompt, ensuring the model has explicit context about when research is conducted. This is critical for time-sensitive queries and distinguishing between historical and current information.

**Dynamic Token Budgeting:** The system implements sophisticated token management with dynamic budgeting across research rounds, preventing context overflow while maximizing information extraction.

**Concurrency Control:** When multiple agents run in parallel, caching and locking mechanisms prevent duplicate work, with configurable sequential or parallel execution modes.

## Current Status and Applications

Geo DeepResearch is now the most reliable solution developed through this project, providing extensive yet concise, grounded responses through deep research, ready to power the Genie Threat Hunting Automation Platform's reconnaissance and planning phase.

The architecture is designed for extensibility to other research domains, including general scientific research and live asset price research, as detailed in later sections.

Though, the open source deep research scene is very hot; at the point I started development of my solution, there were many deep research solutions that I have not evaluated, but as I experienced that an opioninated framework which is developed with specific models and strategies in mind can outperform other solutions, I proceeded with implementing my own solution without evaluating the many other solutions available out there.