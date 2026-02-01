# Lawnmower Man: User Guide

This guide provides instructions and reference for the SME Forensic Gateway.

## 🧬 System Manifest: Live Tool Registry

| Tool Name | Description | Parameters |
| :--- | :--- | :--- |
| `verify_system` | Check system health: CPU, RAM, database status, and data integrity |  |
| `semantic_search` | Search the knowledge base using semantic vector similarity | `query`, `limit` |
| `query_knowledge` | Query the knowledge graph for related concepts | `concept` |
| `save_memory` | Persist a new fact or insight to the knowledge base | `fact`, `source` |
| `get_memory_stats` | Get statistics about stored knowledge: facts, vectors, entries |  |
| `analyze_authorship` | Performs stylometric fingerprinting using Burrows' Delta (Manhattan distance) | `text_sample`, `suspect_vector_id` |
| `analyze_sentiment` | Detect emotions, sarcasm, and sentiment in text | `text` |
| `link_entities` | Extract and link entities to knowledge bases | `text` |
| `summarize_text` | Summarize text using extractive, abstractive, or query-focused modes | `text`, `mode`, `max_sentences` |
| `cluster_documents` | Cluster documents by semantic similarity | `documents`, `algorithm` |
| `build_knowledge_graph` | Build semantic graph from concepts and relationships | `concepts` |
| `verify_facts` | Verify claims against the knowledge base | `claim` |
| `analyze_nlp` | Deep NLP analysis: dependencies, coreference, semantic roles | `text` |
| `detect_networks` | Detect coordinated sockpuppet networks | `authors` |
| `resolve_concept` | Map ambiguous terms to specific knowledge graph nodes | `term` |
| `generate_intelligence_report` | Aggregate findings into a structured forensic report | `subject`, `findings` |
| `discover_overlap` | Find shared rhetorical signals between different authors | `author_ids` |
| `analyze_rolling_delta` | Temporal stylometric analysis of writing style evolution | `text`, `window_size` |
| `analyze_authorship_pro` | Advanced forensic matching using probability calibration | `text`, `comparison_id` |
| `deep_analyze` | Comprehensive forensic analysis combining multiple tools | `text` |
| `cross_author_comparison` | Compare multiple authors/texts to find commonalities | `texts` |
| `process_batch` | Execute a tool against multiple inputs in a single batch | `tool_name`, `inputs` |
| `get_session_info` | Get detailed information about a session | `session_id` |
| `update_scratchpad` | Store temporary facts or context in the session scratchpad | `key`, `value` |
| `list_available_tools` | List all available MCP tools exposed by the gateway |  |
| `login` | Authenticate with the gateway and receive a JWT token | `username`, `password` |
| `check_health` | Combined health check for the gateway and dependencies |  |
| `get_system_latency` | Measure internal tool call latency and system response |  |
| `entity_extractor` | Advanced entity cross-referencing against the 10GB ConceptNet knowledge graph | `text` |
| `get_influence_score` | Query the 10GB SQLite core to build a local ego-graph and return centrality | `entity_name` |
| `justify_claim` | Assigns an 'Epistemic Certainty Score' (CQ) based on source provenance | `claim`, `evidence_sources` |

*Last Updated: 2026-01-31*

## 🧬 System Manifest: Live Tool Registry
| Tool Name | Description | Parameters |
| :--- | :--- | :--- |
| `verify_system` | Check system health: CPU, RAM, database status, and data integrity |  |
| `semantic_search` | Search the knowledge base using semantic vector similarity | `query`, `limit` |
| `query_knowledge` | Query the knowledge graph for related concepts | `concept` |
| `save_memory` | Persist a new fact or insight to the knowledge base | `fact`, `source` |
| `get_memory_stats` | Get statistics about stored knowledge: facts, vectors, entries |  |
| `analyze_authorship` | Performs stylometric fingerprinting using Burrows' Delta (Manhattan distance) | `text_sample`, `suspect_vector_id` |
| `analyze_sentiment` | Detect emotions, sarcasm, and sentiment in text | `text` |
| `link_entities` | Extract and link entities to knowledge bases | `text` |
| `summarize_text` | Summarize text using extractive, abstractive, or query-focused modes | `text`, `mode`, `max_sentences` |
| `cluster_documents` | Cluster documents by semantic similarity | `documents`, `algorithm` |
| `build_knowledge_graph` | Build semantic graph from concepts and relationships | `concepts` |
| `verify_facts` | Verify claims against the knowledge base | `claim` |
| `analyze_nlp` | Deep NLP analysis: dependencies, coreference, semantic roles | `text` |
| `detect_networks` | Detect coordinated sockpuppet networks | `authors` |
| `resolve_concept` | Map ambiguous terms to specific knowledge graph nodes | `term` |
| `generate_intelligence_report` | Aggregate findings into a structured forensic report | `subject`, `findings` |
| `discover_overlap` | Find shared rhetorical signals between different authors | `author_ids` |
| `analyze_rolling_delta` | Temporal stylometric analysis of writing style evolution | `text`, `window_size` |
| `analyze_authorship_pro` | Advanced forensic matching using probability calibration | `text`, `comparison_id` |
| `deep_analyze` | Comprehensive forensic analysis combining multiple tools | `text` |
| `cross_author_comparison` | Compare multiple authors/texts to find commonalities | `texts` |
| `process_batch` | Execute a tool against multiple inputs in a single batch | `tool_name`, `inputs` |
| `get_session_info` | Get detailed information about a session | `session_id` |
| `update_scratchpad` | Store temporary facts or context in the session scratchpad | `key`, `value` |
| `list_available_tools` | List all available MCP tools exposed by the gateway |  |
| `login` | Authenticate with the gateway and receive a JWT token | `username`, `password` |
| `check_health` | Combined health check for the gateway and dependencies |  |
| `get_system_latency` | Measure internal tool call latency and system response |  |
| `entity_extractor` | Advanced entity cross-referencing against the 10GB ConceptNet knowledge graph | `text` |
| `get_influence_score` | Query the 10GB SQLite core to build a local ego-graph and return centrality | `entity_name` |
| `justify_claim` | Assigns an 'Epistemic Certainty Score' (CQ) based on source provenance | `claim`, `evidence_sources` |

*Last Updated: 2026-01-31*

## 🧬 System Manifest: Live Tool Registry
| Tool Name | Description | Parameters |
| :--- | :--- | :--- |
| `verify_system` | Check system health: CPU, RAM, database status, and data integrity |  |
| `semantic_search` | Search the knowledge base using semantic vector similarity | `query`, `limit` |
| `query_knowledge` | Query the knowledge graph for related concepts | `concept` |
| `save_memory` | Persist a new fact or insight to the knowledge base | `fact`, `source` |
| `get_memory_stats` | Get statistics about stored knowledge: facts, vectors, entries |  |
| `analyze_authorship` | Performs stylometric fingerprinting using Burrows' Delta (Manhattan distance) | `text_sample`, `suspect_vector_id` |
| `analyze_sentiment` | Detect emotions, sarcasm, and sentiment in text | `text` |
| `link_entities` | Extract and link entities to knowledge bases | `text` |
| `summarize_text` | Summarize text using extractive, abstractive, or query-focused modes | `text`, `mode`, `max_sentences` |
| `cluster_documents` | Cluster documents by semantic similarity | `documents`, `algorithm` |
| `build_knowledge_graph` | Build semantic graph from concepts and relationships | `concepts` |
| `verify_facts` | Verify claims against the knowledge base | `claim` |
| `analyze_nlp` | Deep NLP analysis: dependencies, coreference, semantic roles | `text` |
| `detect_networks` | Detect coordinated sockpuppet networks | `authors` |
| `resolve_concept` | Map ambiguous terms to specific knowledge graph nodes | `term` |
| `generate_intelligence_report` | Aggregate findings into a structured forensic report | `subject`, `findings` |
| `discover_overlap` | Find shared rhetorical signals between different authors | `author_ids` |
| `analyze_rolling_delta` | Temporal stylometric analysis of writing style evolution | `text`, `window_size` |
| `analyze_authorship_pro` | Advanced forensic matching using probability calibration | `text`, `comparison_id` |
| `deep_analyze` | Comprehensive forensic analysis combining multiple tools | `text` |
| `cross_author_comparison` | Compare multiple authors/texts to find commonalities | `texts` |
| `process_batch` | Execute a tool against multiple inputs in a single batch | `tool_name`, `inputs` |
| `get_session_info` | Get detailed information about a session | `session_id` |
| `update_scratchpad` | Store temporary facts or context in the session scratchpad | `key`, `value` |
| `list_available_tools` | List all available MCP tools exposed by the gateway |  |
| `login` | Authenticate with the gateway and receive a JWT token | `username`, `password` |
| `check_health` | Combined health check for the gateway and dependencies |  |
| `get_system_latency` | Measure internal tool call latency and system response |  |
| `entity_extractor` | Advanced entity cross-referencing against the 10GB ConceptNet knowledge graph | `text` |
| `get_influence_score` | Query the 10GB SQLite core to build a local ego-graph and return centrality | `entity_name` |
| `justify_claim` | Assigns an 'Epistemic Certainty Score' (CQ) based on source provenance | `claim`, `evidence_sources` |
| `generate_witness_statement` | No description provided | N/A |

*Last Updated: 2026-01-31*