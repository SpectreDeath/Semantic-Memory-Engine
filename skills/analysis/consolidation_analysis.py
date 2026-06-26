"""
Skills Consolidation Analysis
==============================

Analyzes the skills registry to identify duplicates and overlapping skills.
Used to plan consolidation of 89 skills into a focused set.

Categories identified:
1. **Consolidatable**: Skills with overlapping functionality
2. **Unique**: Skills with no overlap
3. **Duplicated**: Same source file or nearly identical purpose
"""

import json
from pathlib import Path

def load_registry():
    """Load the skills registry."""
    registry_path = Path(__file__).parent / 'registry.json'
    with open(registry_path, 'r') as f:
        return json.load(f)

def analyze_duplicates(registry):
    """Identify duplicate and overlapping skills."""
    
    # Group by source_file to find skills from same file
    by_source = {}
    for skill in registry:
        source = skill.get('source_file', '')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(skill['name'])
    
    # Groups with multiple skills from same source
    duplicates_by_source = {k: v for k, v in by_source.items() if len(v) > 1}
    
    # Manual analysis of overlapping skills
    overlap_groups = [
        {
            "group": "Stylometry/Writing Analysis",
            "skills": [
                "stylometry-engine",  # src/scribe/engine.py - Core
                "stylometric-analysis",  # src/scribe/stylo_wrapper.py - Uses Stylo
                "stylo-integration",  # src/scribe/stylo_wrapper.py - Same as above!
                # CONSOLIDATE INTO: stylometry-engine (keep as core)
            ],
            "action": "Merge into 'stylometry-engine'"
        },
        {
            "group": "Context Analysis",
            "skills": [
                "context-identification",  # src/utils/context_sniffer.py
                "context-sniffer",  # src/utils/context_sniffer.py - SAME SOURCE!
                # CONSOLIDATE INTO: context-sniffer
            ],
            "action": "Merge into 'context-sniffer'"
        },
        {
            "group": "AI Bridge/Communication",
            "skills": [
                "ai-bridge-rpc",  # src/ai/bridge_rpc.py - JSON-RPC
                "async-ai-bridge",  # src/ai/bridge.py - Async bridge
                # These have different implementations but same purpose
            ],
            "action": "Merge into 'ai-bridge'"
        },
        {
            "group": "Semantic Overlap/Comparison",
            "skills": [
                "overlap-discovery",  # src/analysis/overlap_discovery.py
                "semantic-overlap-detection",  # src/analysis/overlap_discovery.py - SAME SOURCE!
                # CONSOLIDATE INTO: overlap-discovery
            ],
            "action": "Merge into 'overlap-discovery'"
        },
        {
            "group": "Data Ingestion",
            "skills": [
                "harvester-web-ingestion",  # src/harvester/
                "scrapegraph-harvesting",  # extensions/ext_scrapegraph_harvester/
                "web-researcher",  # src/gathering/web_researcher.py
                "cloud-fetching",  # src/gathering/cloud_fetcher.py
                "rss-bridge",  # src/gathering/rss_bridge.py
                "scholar-api",  # src/gathering/scholar_api.py
                # These are different sources but could be grouped
            ],
            "action": "Keep separate but group logically"
        },
        {
            "group": "Analysis Core",
            "skills": [
                "analysis-engine",  # src/analysis/engine.py - Coordinator
                "analysis-core",  # extensions/ext_analysis_core/ - Extension
                # Similar purpose
            ],
            "action": "Check if redundant"
        },
        {
            "group": "Query/Discovery",
            "skills": [
                "query-engine",  # src/query/engine.py
                "scout-discovery",  # src/query/scout.py
                "query-verification",  # src/query/verifier.py
                "concept-resolution",  # src/query/concept_resolver.py
                # All query-related but different functions
            ],
            "action": "Group under 'query-system'"
        },
        {
            "group": "Data/Database Management",
            "skills": [
                "data-storage",  # extensions/ext_data_storage/
                "centrifuge-storage",  # src/core/centrifuge.py
                "semantic-database",  # src/core/semantic_db.py
                # Similar purpose
            ],
            "action": "Check overlap"
        },
        {
            "group": "Monitoring/Diagnostics",
            "skills": [
                "performance-monitoring",  # src/utils/performance.py
                "system-health-scan",  # extensions/ext_stetho_scan/
                "diagnostics",  # src/monitoring/diagnostics.py
                "monitoring",  # extensions/ext_monitoring/
            ],
            "action": "Merge into 'system-diagnostics'"
        },
        {
            "group": "Logging",
            "skills": [
                "log-analysis",  # src/utils/log_utils.py
                "logging-system",  # extensions/ext_logging/plugin.py
            ],
            "action": "Merge into 'logging-system'"
        },
        {
            "group": "Stylometric Comparison",
            "skills": [
                "rolling-delta-analysis",  # src/scribe/rolling_delta.py
                "contrastive-analysis",  # src/scribe/contrastive_analyzer.py
                # Similar but different analysis types
            ],
            "action": "Keep separate"
        },
        {
            "group": "Document Comparison",
            "skills": [
                "document-clustering",  # src/core/document_clusterer.py
                "document-comparison",  # src/analysis/comparisons.py
            ],
            "action": "Different purposes, keep separate"
        },
        {
            "group": "NLP System",
            "skills": [
                "nlp-processing",  # src/core/nlp_pipeline.py
                "nlp-core",  # extensions/ext_nlp_core/
            ],
            "action": "Merge into 'nlp-system'"
        },
        {
            "group": "AI Provider",
            "skills": [
                "llm-provider-management",  # src/ai/provider.py
                "unified-provider",  # src/ai/unified_provider.py
                # Likely overlapping
            ],
            "action": "Merge into 'llm-provider'"
        },
        {
            "group": "Intelligence Reporting",
            "skills": [
                "intelligence-reporting",  # src/analysis/intelligence_reports.py
                "dark-data-discovery",  # extensions/ext_nur/
            ],
            "action": "Different purposes, keep separate"
        },
        {
            "group": "Security/AI Detection",
            "skills": [
                "adversarial-pattern-detection",  # extensions/ext_adversarial_breaker/
                "adversarial-simulation",  # extensions/ext_adversarial_tester/
                "synthetic-source-detection",  # extensions/ext_synthetic_source_auditor/
                # All AI detection related
            ],
            "action": "Different functions, keep separate"
        },
        {
            "group": "Semantic Analysis",
            "skills": [
                "semantic-auditor",  # extensions/ext_semantic_auditor/
                "data-correlation",  # src/analysis/correlator.py
            ],
            "action": "Different purposes"
        },
        {
            "group": "Entity Processing",
            "skills": [
                "entity-linking",  # src/core/entity_linker.py
                "entity-redaction",  # src/utils/entity_filter.py
            ],
            "action": "Different purposes"
        },
        {
            "group": "Validation/Auditing",
            "skills": [
                "validation-framework",  # src/core/validation.py
                "logic-consistency-verification",  # extensions/ext_logic_auditor/
                "data-auditing",  # src/utils/auditor.py
                "database-auditing",  # src/utils/check_db.py
            ],
            "action": "Group but keep separate"
        }
    ]
    
    # Calculate exact duplicates by source file
    exact_duplicates = {}
    for source, skills in duplicates_by_source.items():
        if len(skills) > 1:
            exact_duplicates[source] = skills
    
    return {
        "exact_duplicates": exact_duplicates,
        "overlap_groups": overlap_groups,
        "total_skills": len(registry),
        "consolidation_candidates": len(overlap_groups),
    }

def main():
    registry = load_registry()
    analysis = analyze_duplicates(registry)
    
    print("=" * 60)
    print("SKILLS CONSOLIDATION ANALYSIS")
    print("=" * 60)
    print(f"\nTotal Skills: {analysis['total_skills']}")
    print(f"Consolidation Groups: {analysis['consolidation_candidates']}")
    
    print("\n--- Exact Duplicates (Same Source File) ---")
    for source, skills in analysis['exact_duplicates'].items():
        print(f"\n  {source}: {skills}")
    
    print("\n--- Recommended Consolidations ---")
    for group in analysis['overlap_groups']:
        print(f"\n  Group: {group['group']}")
        print(f"    Skills: {group['skills']}")
        print(f"    Action: {group['action']}")

if __name__ == "__main__":
    main()