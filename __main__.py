"""
SimpleMem Laboratory CLI Entry Point

Provides a command-line interface to discover and run available tools.
Usage:
    python -m src [command] [options]
    python __main__.py list
    python __main__.py run [tool-name] [args]
"""

import sys
import argparse
from typing import Dict, Callable
from pathlib import Path

# Import core tool classes
from src.scribe.engine import ScribeEngine
from src.query.scout_integration import Scout
from src.query.engine import SemanticSearchEngine
from src.synapse.synapse import MemoryConsolidator
from src.visualization.dashboard import RhetoricAnalyzer
from src.core.centrifuge import Centrifuge
from src.monitoring.diagnostics import SystemMonitor
from src.analysis.knowledge_graph import KnowledgeGraph
from src.analysis.intelligence_reports import IntelligenceReports
from src.analysis.overlap_discovery import OverlapDiscovery
from src.core.dashboard_cmd import DashboardOrchestrator

# Tool registry
TOOLS: Dict[str, Dict[str, any]] = {
    "scribe": {
        "name": "Scribe Authorship Engine",
        "description": "Forensic authorship analysis and attribution",
        "class": ScribeEngine,
        "short": "scribe",
    },
    "scout": {
        "name": "Scout Adaptive Query System",
        "description": "Intelligent knowledge gap detection and adaptive retrieval",
        "class": Scout,
        "short": "scout",
    },
    "search": {
        "name": "Semantic Search Engine",
        "description": "Vector-based semantic search across memory",
        "class": SemanticSearchEngine,
        "short": "search",
    },
    "synapse": {
        "name": "Memory Consolidator (Synapse)",
        "description": "Memory consolidation and behavioral profiling",
        "class": MemoryConsolidator,
        "short": "synapse",
    },
    "rhetoric": {
        "name": "Rhetoric Analyzer (Beacon)",
        "description": "Rhetoric and sentiment analysis visualization",
        "class": RhetoricAnalyzer,
        "short": "beacon",
    },
    "centrifuge": {
        "name": "Centrifuge Database",
        "description": "Semantic database management and storage",
        "class": Centrifuge,
        "short": "db",
    },
    "monitor": {
        "name": "System Monitor",
        "description": "System health and performance diagnostics",
        "class": SystemMonitor,
        "short": "monitor",
    },
    "graph": {
        "name": "Knowledge Graph Engine",
        "description": "Semantic network and entity relationship visualization",
        "class": KnowledgeGraph,
        "short": "graph",
    },
    "report": {
        "name": "Intelligence Reports",
        "description": "Narrative synthesis and automated document briefings",
        "class": IntelligenceReports,
        "short": "brief",
    },
    "connections": {
        "name": "Overlap Discovery",
        "description": "Cross-document semantic connection detection",
        "class": OverlapDiscovery,
        "short": "links",
    },
    "dashboard": {
        "name": "Control Room Dashboard",
        "description": "Premium real-time laboratory management interface",
        "class": DashboardOrchestrator,
        "short": "ui",
    },
}


def list_tools():
    """Display all available tools and their descriptions."""
    print("\n🧪 SimpleMem Laboratory - Available Tools\n")
    print("-" * 70)
    for tool_key, tool_info in TOOLS.items():
        print(f"  {tool_key:15} | {tool_info['name']}")
        print(f"  {' ':15} | {tool_info['description']}")
        print()


def show_help():
    """Display help message."""
    print("""
🧪 SimpleMem Laboratory CLI
============================

Usage: python -m src [command] [options]

Commands:
  list              List all available tools
  info [tool]       Show detailed info about a tool
  run [tool]        Launch a tool (experimental)
  graph [text]      Build and show knowledge graph
  report [text]     Generate intelligence briefing
  links [context]   Find semantic connections
  dashboard         Launch the Control Room UI
  version           Show version information
  help              Show this help message

Examples:
  python -m src list
  python -m src info scribe
  python -m src run scout

For tool-specific options, try:
  python -m src info [tool-name]

Documentation:
  - README.md          : Main documentation
  - docs/START_HERE.md : Getting started guide
  - config/config.yaml : Configuration settings
""")


def show_version():
    """Display version information."""
    print("""
SimpleMem Laboratory v2.0
Refactored Architecture with Semantic Memory
Powered by ChromaDB, Centrifuge, and MCP Framework
""")


def show_tool_info(tool_name: str):
    """Show detailed information about a specific tool."""
    if tool_name not in TOOLS:
        print(f"❌ Tool '{tool_name}' not found.")
        print("\nAvailable tools:")
        for key in TOOLS.keys():
            print(f"  - {key}")
        return
    
    tool = TOOLS[tool_name]
    print(f"\n📋 {tool['name']}")
    print("=" * 70)
    print(f"Description: {tool['description']}")
    print(f"Short name:  {tool['short']}")
    print(f"Module:      {tool['class'].__module__}.{tool['class'].__name__}")
    print("\nDocstring:")
    if tool['class'].__doc__:
        print(tool['class'].__doc__)
    else:
        print("  (No documentation available)")
    print()


def run_tool(tool_name: str, args: list = None):
    """Run a tool (experimental - depends on tool's main interface)."""
    if tool_name not in TOOLS:
        print(f"❌ Tool '{tool_name}' not found.")
        return
    
    tool_class = TOOLS[tool_name]['class']
    print(f"🚀 Launching {TOOLS[tool_name]['name']}...")
    print(f"   From: {tool_class.__module__}")
    
    try:
        # Try to instantiate and run if the tool supports it
        instance = tool_class()
        if hasattr(instance, 'main'):
            instance.main(args or [])
        else:
            print(f"   Tool is loaded but requires programmatic usage.")
            print(f"   See documentation: docs/{tool_name.upper()}_*.md")
    except Exception as e:
        print(f"❌ Error running tool: {e}")
        print("   Try: python -m src info [tool-name]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SimpleMem Laboratory CLI",
        add_help=True,
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["list", "info", "run", "version", "help"],
        help="Command to execute",
    )
    parser.add_argument(
        "tool",
        nargs="?",
        help="Tool name (for 'info' and 'run' commands)",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments for the tool",
    )
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_tools()
    elif args.command == "info":
        if not args.tool:
            print("❌ Please specify a tool name")
            list_tools()
        else:
            show_tool_info(args.tool)
    elif args.command == "run":
        if not args.tool:
            print("❌ Please specify a tool name")
            list_tools()
        else:
            run_tool(args.tool, args.args)
    elif args.command == "version":
        show_version()
    elif args.command == "dashboard":
        from src.core.dashboard_cmd import main as launch_dashboard
        launch_dashboard()
    elif args.command == "graph":
        if not args.tool: # Reuse tool arg for text in these commands
             print("❌ Please provide text for graph generation")
        else:
            from src import ToolFactory
            kg = ToolFactory.create_knowledge_graph()
            kg.build_from_text(args.tool)
            print(kg.to_mermaid())
    elif args.command == "report":
        if not args.tool:
             print("❌ Please provide text for report generation")
        else:
            from src import ToolFactory
            ir = ToolFactory.create_intelligence_reports()
            report = ir.generate_briefing(args.tool)
            print(ir.to_markdown(report))
    elif args.command == "links":
        if not args.tool:
             print("❌ Please provide context ID for discovery")
        else:
            from src import ToolFactory
            od = ToolFactory.create_overlap_discovery()
            links = od.find_connections(args.tool)
            print(f"\n🔍 Found {len(links)} semantic connections for '{args.tool}':")
            for link in links:
                print(f"  - {link.target_context} (Similarity: {link.similarity_score:.2f})")
                print(f"    Key Themes: {', '.join(link.overlapping_concepts)}")
    else:  # help
        show_help()


if __name__ == "__main__":
    main()
