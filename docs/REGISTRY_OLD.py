"""
Complete Toolbox Documentation & Registry
All 5 categories with 15+ tools ready for deployment.
"""

# ============================================================================
# CATEGORY 1: SIMPLEMEM PIPELINE TOOLS (semantic_loom.py)
# ============================================================================

LOOM_TOOLS = {
    "distill_web_content": {
        "description": "Distills web search results into atomic facts with coreference resolution",
        "use_case": "Take WebSearcher output, extract facts, resolve pronouns",
        "params": {
            "content": "str - webpage text",
            "source_url": "str - origin URL"
        },
        "returns": "atomic_facts, entities_extracted, compression_metrics"
    },
    
    "resolve_coreferences": {
        "description": "Resolves pronouns and references to actual entity names",
        "use_case": "Change 'he said' to '[Subject Name] said'",
        "params": {
            "text": "str - text with pronouns"
        },
        "returns": "resolved_text, entities_found"
    },
    
    "extract_atomic_facts": {
        "description": "Breaks text into atomic facts (who-what-when-why)",
        "use_case": "Create granular facts for memory consolidation",
        "params": {
            "text": "str - source text"
        },
        "returns": "facts_list with confidence scores and entity types"
    },
    
    "compress_semantic_data": {
        "description": "Compresses facts with 30x token reduction through deduplication",
        "use_case": "Reduce context window bloat before model inference",
        "params": {
            "facts_json": "str/list - JSON facts array"
        },
        "returns": "compression_results with compression_factor"
    }
}

# ============================================================================
# CATEGORY 2: MEMORY CONSOLIDATION TOOLS (memory_synapse.py)
# ============================================================================

SYNAPSE_TOOLS = {
    "find_similar_memories": {
        "description": "Identifies clusters of similar memory entries",
        "use_case": "Find candidates for consolidation during idle time",
        "params": {
            "similarity_threshold": "float 0-1 - default 0.6"
        },
        "returns": "clusters_found with member lists"
    },
    
    "create_memory_concept": {
        "description": "Creates abstract concept from clustered entries",
        "use_case": "Merge 5 observations of User A into 'UserA_Profile'",
        "params": {
            "concept_name": "str - concept identifier",
            "member_files": "str/list - JSON array of file names",
            "definition": "str - optional concept description"
        },
        "returns": "concept_id, member_count, status"
    },
    
    "consolidate_during_idle": {
        "description": "Recursive memory consolidation - runs during idle",
        "use_case": "Background consolidation without blocking main ops",
        "params": {},
        "returns": "consolidation_results with concepts_created"
    },
    
    "build_behavioral_profile": {
        "description": "Builds behavioral profile from consolidated memories",
        "use_case": "Get sentiment trends and patterns for entity",
        "params": {
            "entity_name": "str - entity to profile",
            "days": "int - lookback window, default 30"
        },
        "returns": "sentiment_profile with avg metrics"
    }
}

# ============================================================================
# CATEGORY 3: ADAPTIVE RETRIEVAL TOOLS (adaptive_scout.py)
# ============================================================================

SCOUT_TOOLS = {
    "estimate_query_complexity": {
        "description": "Estimates complexity of query (0-10 scale)",
        "use_case": "Decide how deep to search before retrieval",
        "params": {
            "query": "str - user query"
        },
        "returns": "complexity_score, level, contributing_factors, recommended_depth"
    },
    
    "adaptive_retrieval": {
        "description": "Retrieves facts with depth adapted to query complexity",
        "use_case": "Simple query gets 3 facts, complex gets 25+",
        "params": {
            "query": "str - user query"
        },
        "returns": "complexity_analysis, retrieval_parameters, facts_retrieved, context_window_estimate"
    },
    
    "deep_search": {
        "description": "Deep search across all temporal data",
        "use_case": "Complex rhetorical analysis with pattern detection",
        "params": {
            "query": "str - search query",
            "focus_area": "str - optional entity or topic focus"
        },
        "returns": "sentiment_patterns, top_results with frequency analysis"
    }
}

# ============================================================================
# CATEGORY 4: DATA PROCESSING & ANALYSIS (data_processor.py)
# ============================================================================

PROCESSOR_TOOLS = {
    "list_available_lexicons": {
        "description": "Lists all available lexicon files",
        "use_case": "Discover semantic/moral foundation vocabularies",
        "params": {},
        "returns": "category_files, nfo_files, readme_files with sizes"
    },
    
    "load_lexicon_file": {
        "description": "Loads and indexes a lexicon file",
        "use_case": "Load moral foundations dictionary for analysis",
        "params": {
            "filename": "str - lexicon file name",
            "limit": "int - max words to load, default 1000"
        },
        "returns": "words_list with preview of first 100"
    },
    
    "build_lexicon_index": {
        "description": "Builds master index of lexicon files",
        "use_case": "Create searchable index of all lexicons",
        "params": {
            "filenames": "str - comma-separated or empty for all"
        },
        "returns": "indexed_files, total_entries, files dict"
    },
    
    "aggregate_sentiment_signals": {
        "description": "Aggregates sentiment signals from compiled_signals.json",
        "use_case": "Identify high-intensity signals in data",
        "params": {
            "days": "int - temporal window, default 30"
        },
        "returns": "total_signals, signal_categories, high_intensity_signals"
    },
    
    "merge_multi_source_data": {
        "description": "Merges data from multiple JSON files",
        "use_case": "Combine web search, watch_and_analyze outputs",
        "params": {
            "sources_json": "str/list - JSON array of file names"
        },
        "returns": "merged_data with all entries combined"
    },
    
    "batch_semantic_compression": {
        "description": "Performs batch compression on multiple files",
        "use_case": "Compress month of data for archival",
        "params": {
            "files_json": "str/list - JSON array of files",
            "output_file": "str - optional output file name"
        },
        "returns": "compression_stats with compression_ratio"
    }
}

# ============================================================================
# CATEGORY 5: MONITORING & DIAGNOSTICS (monitoring_diagnostics.py)
# ============================================================================

MONITORING_TOOLS = {
    "profile_system_performance": {
        "description": "Profiles CPU, memory, disk, GPU usage",
        "use_case": "Monitor 1660 Ti and system resources",
        "params": {},
        "returns": "cpu, memory, disk, process, gpu_info metrics"
    },
    
    "check_database_health": {
        "description": "Checks database health and integrity",
        "use_case": "Verify Centrifuge DB is not corrupted",
        "params": {},
        "returns": "tables, total_records, db_file_size_mb, integrity status"
    },
    
    "optimize_database_performance": {
        "description": "Optimizes DB: VACUUM, ANALYZE, PRAGMA optimize",
        "use_case": "Maintenance - run periodically",
        "params": {},
        "returns": "operations, status, timestamp"
    },
    
    "analyze_cache_efficiency": {
        "description": "Analyzes cache and retrieval efficiency",
        "use_case": "Assess how well memory is performing",
        "params": {},
        "returns": "cache_metrics, efficiency_score, recommendations"
    },
    
    "analyze_log_performance": {
        "description": "Analyzes log directory size and performance",
        "use_case": "Decide if logs need cleanup",
        "params": {},
        "returns": "total_log_size_mb, log_file_count, file details"
    }
}

# ============================================================================
# CATEGORY 6: INTEGRATION & ORCHESTRATION (pipeline_orchestrator.py)
# ============================================================================

ORCHESTRATOR_TOOLS = {
    "submit_batch_job": {
        "description": "Submits job to execution queue",
        "use_case": "Queue search_duckduckgo, analyze_rhetoric, etc",
        "params": {
            "job_id": "str - unique job identifier",
            "job_type": "str - 'search', 'analyze', 'compress', etc",
            "payload_json": "str/dict - job parameters",
            "max_retries": "int - default 3"
        },
        "returns": "job_id, status, submitted_at"
    },
    
    "get_job_status": {
        "description": "Gets status of submitted job",
        "use_case": "Check if background job completed",
        "params": {
            "job_id": "str - job identifier"
        },
        "returns": "job status, result, error_message if failed"
    },
    
    "get_pending_jobs": {
        "description": "Gets pending jobs ready for execution",
        "use_case": "Retrieve batch for processing",
        "params": {
            "limit": "int - max jobs to return, default 10"
        },
        "returns": "pending_jobs array with job_id, type, payload"
    },
    
    "create_pipeline": {
        "description": "Creates multi-step pipeline",
        "use_case": "Orchestrate: search -> distill -> consolidate -> retrieve",
        "params": {
            "pipeline_name": "str - pipeline identifier",
            "steps_json": "str/list - steps with type and params"
        },
        "returns": "pipeline object with job_ids for each step"
    },
    
    "execute_pipeline": {
        "description": "Executes a previously created pipeline",
        "use_case": "Run all steps in sequence",
        "params": {
            "pipeline_name": "str - pipeline to execute"
        },
        "returns": "execution status with step_results"
    },
    
    "handle_job_failure": {
        "description": "Handles job failure with retry decision",
        "use_case": "Intelligent error recovery",
        "params": {
            "job_id": "str - failed job",
            "error_message": "str - error details",
            "should_retry": "bool - retry decision"
        },
        "returns": "action, error_type, retry info if applicable"
    },
    
    "get_failed_jobs": {
        "description": "Retrieves all failed jobs",
        "use_case": "Review and troubleshoot failures",
        "params": {},
        "returns": "failed_jobs array with error details"
    }
}

# ============================================================================
# CATEGORY 7: RETRIEVAL & QUERY (retrieval_query.py)
# ============================================================================

RETRIEVAL_TOOLS = {
    "semantic_search": {
        "description": "Semantic search on stored facts",
        "use_case": "Find relevant facts by meaning similarity",
        "params": {
            "query": "str - search query",
            "top_k": "int - results to return, default 10"
        },
        "returns": "results ranked by similarity_score"
    },
    
    "entity_search": {
        "description": "Search all mentions of specific entity",
        "use_case": "Get entity profile with sentiment trends",
        "params": {
            "entity_name": "str - entity to search for"
        },
        "returns": "entity_profile with total_mentions, sentiment data"
    },
    
    "verify_sentiment_claim": {
        "description": "Verifies sentiment-related claims",
        "use_case": "Check if 'compound > 0.5' is true in data",
        "params": {
            "claim": "str - claim to verify, e.g., 'compound > 0.5'"
        },
        "returns": "verified bool, matching_records, percentage, confidence"
    },
    
    "verify_entity_pattern": {
        "description": "Verifies behavioral patterns for entity",
        "use_case": "Confirm 'consistently_negative' pattern",
        "params": {
            "entity": "str - entity name",
            "pattern": "str - 'consistently_negative', 'consistently_positive', 'volatile'"
        },
        "returns": "pattern_match bool, sentiment stats, confidence"
    },
    
    "optimize_context_window": {
        "description": "Optimizes context by selecting facts within token budget",
        "use_case": "Fit all relevant facts in 4k/8k/16k window",
        "params": {
            "facts_json": "str/list - JSON facts",
            "max_tokens": "int - token limit, default 4000"
        },
        "returns": "selected_facts, optimization_ratio"
    },
    
    "estimate_context_size": {
        "description": "Estimates token count for text",
        "use_case": "Check if text fits in model context",
        "params": {
            "text": "str - text to measure"
        },
        "returns": "estimated_tokens, fits_in_4k/8k/16k_window"
    },
    
    "build_query_response": {
        "description": "Builds optimized response structure",
        "use_case": "Structure response for 'analytical', 'rhetorical', or 'behavioral' queries",
        "params": {
            "query": "str - user query",
            "facts_json": "str/list - context facts",
            "response_type": "str - type of response"
        },
        "returns": "response_structure array, recommendations"
    }
}

# ============================================================================
# QUICK START GUIDE
# ============================================================================

QUICK_START = """
QUICK START: Using the Complete Toolbox
========================================

1. SEMANTIC DISTILLATION (The Loom)
   ├─ web_search() -> distill_web_content() -> extract_atomic_facts()
   └─ resolve_coreferences() for pronoun replacement

2. MEMORY CONSOLIDATION (The Synapse)
   ├─ find_similar_memories() -> create_memory_concept()
   ├─ consolidate_during_idle() (background process)
   └─ build_behavioral_profile() (to see results)

3. ADAPTIVE RETRIEVAL (The Scout)
   ├─ estimate_query_complexity() (0-10 scale)
   ├─ adaptive_retrieval() (auto-depth decision)
   └─ deep_search() (for complex queries)

4. DATA PROCESSING
   ├─ list_available_lexicons() + load_lexicon_file()
   ├─ aggregate_sentiment_signals()
   ├─ merge_multi_source_data()
   └─ batch_semantic_compression()

5. MONITORING & DIAGNOSTICS
   ├─ profile_system_performance() (CPU/GPU/Memory)
   ├─ check_database_health() (Centrifuge integrity)
   ├─ analyze_cache_efficiency() (retrieval speed)
   └─ optimize_database_performance() (maintenance)

6. PIPELINE ORCHESTRATION
   ├─ create_pipeline() -> execute_pipeline()
   ├─ submit_batch_job() -> get_job_status()
   ├─ handle_job_failure() (intelligent retry)
   └─ get_pending_jobs() + get_failed_jobs()

7. RETRIEVAL & QUERY
   ├─ semantic_search() + entity_search()
   ├─ verify_sentiment_claim() + verify_entity_pattern()
   ├─ optimize_context_window() (token efficiency)
   └─ build_query_response() (structured output)

TYPICAL WORKFLOW:
1. search_duckduckgo(query)
2. distill_web_content(results)
3. submit_batch_job('analyze_1', 'distill', {...})
4. consolidate_during_idle() [background]
5. adaptive_retrieval(user_query)
6. optimize_context_window(facts)
7. verify_sentiment_claim(claim)
8. build_query_response(query, facts, 'analytical')

AVAILABLE LANGUAGE MODELS:
- WhiteRabbitNeo (7b-coder) for code analysis
- Sentiment analysis via VADER engine
- Rhetoric analysis via custom lexicons
"""

if __name__ == "__main__":
    print(QUICK_START)
    print("\n" + "="*70)
    print(f"Total Tools: {len(LOOM_TOOLS) + len(SYNAPSE_TOOLS) + len(SCOUT_TOOLS) + len(PROCESSOR_TOOLS) + len(MONITORING_TOOLS) + len(ORCHESTRATOR_TOOLS) + len(RETRIEVAL_TOOLS)}")
    print("="*70)
