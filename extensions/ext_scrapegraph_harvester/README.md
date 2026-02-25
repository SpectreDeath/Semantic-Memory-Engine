# ScrapeGraphAI Harvester Extension

This extension adds agentic web scraping and forensic data harvesting capabilities to the Semantic Memory Engine (SME) using ScrapeGraphAI.

## Features

### 1. SmartScraperGraph - "Memory Harvester"
Extract forensic evidence from any URL using agentic scraping logic. The tool converts web pages into structured memory nodes that are automatically stored in your SME database.

**Usage:**
```python
result = await scrape_and_remember(
    url="https://example.com",
    prompt="Extract all forensic evidence related to cybersecurity",
    model="ollama/llama3.2"
)
```

### 2. SearchGraph - "Deep Researcher"
Search the web for a topic and synthesize findings from multiple sources into structured memory nodes. Perfect for intelligence gathering and research.

**Usage:**
```python
result = await deep_research(
    query="latest cybersecurity threats 2024",
    results_count=10,
    model="ollama/llama3.2"
)
```

### 3. MarkdownifyGraph - "Evidence Standardizer"
Convert any URL to clean Markdown format for semantic memory indexing. Optimized for 80% faster processing compared to raw HTML.

**Usage:**
```python
result = await markdownify(
    url="https://example.com",
    model="ollama/llama3.2"
)
```

## Architecture

### VRAM Optimization (GTX 1660 Ti 6GB)
- Uses Llama-3.2 3B or Mistral 7B via Ollama for local inference
- Headless browser mode to save VRAM
- Limited concurrent requests (2 max)
- 4096 token context window

### Memory Integration
- Automatically stores scraped data in PostgreSQL Nexus
- Indexes content in ChromaDB for semantic search
- Signs all evidence with HSM for forensic integrity
- Calculates trust scores based on source reputation

### Security Features
- All processing happens locally (no data leaves your environment)
- Evidence signing via Hardware Security Module
- Trust scoring for source reliability
- Entity and relationship extraction for knowledge graph building

## Installation

1. Install dependencies:
```bash
pip install -r extensions/ext_scrapegraph_harvester/requirements.txt
```

2. Ensure Ollama is running with models:
```bash
docker run -d -p 11434:11434 ollama/ollama
docker exec sme_ollama ollama pull llama3.2
docker exec sme_ollama ollama pull nomic-embed-text
```

3. The extension will auto-load when SME starts.

## Configuration

The extension automatically configures itself for your hardware constraints. You can customize the model and settings:

```python
# In your SME configuration
SME_SCRAPEGRAPH_MODEL = "ollama/llama3.2"
SME_SCRAPEGRAPH_MAX_TOKENS = 4096
SME_SCRAPEGRAPH_CONCURRENT_REQUESTS = 2
```

## Usage Examples

### Forensic Investigation
```python
# Extract evidence from a suspicious website
result = await scrape_and_remember(
    url="https://suspicious-site.com",
    prompt="Extract all forensic evidence including IP addresses, domains, and suspicious content",
    model="ollama/llama3.2"
)
```

### Intelligence Gathering
```python
# Research a topic across multiple sources
result = await deep_research(
    query="latest ransomware techniques 2024",
    results_count=15,
    model="ollama/llama3.2"
)
```

### Content Standardization
```python
# Convert any page to clean Markdown
result = await markdownify(
    url="https://wikipedia.org",
    model="ollama/llama3.2"
)
```

## Output Structure

All tools return structured JSON with:

- **status**: success/error
- **url/query**: source information
- **model**: LLM model used
- **nodes_created**: number of memory nodes created
- **entities_extracted**: count of extracted entities
- **trust_score**: average trust score (0-1)
- **data**: tool-specific results

## Integration with SME

The extension integrates seamlessly with your existing SME architecture:

- **MCP Gateway**: Tools are automatically registered and exposed
- **Session Management**: All operations tracked in session history
- **Database Integration**: Results stored in PostgreSQL Nexus
- **ChromaDB**: Content indexed for semantic search
- **HSM**: Evidence signed for forensic integrity
- **Control Room**: Tools appear in your forensic toolkit

## Troubleshooting

### Common Issues

**Dependencies not found:**
```bash
pip install -r extensions/ext_scrapegraph_harvester/requirements.txt
```

**Ollama not running:**
```bash
docker ps | grep ollama
# If not running: docker start sme_ollama
```

**VRAM issues:**
- Reduce `max_tokens` in configuration
- Use smaller models (e.g., "ollama/llama2:7b" instead of "ollama/llama3.2")
- Enable headless mode (already enabled by default)

### Performance Tips

- Use smaller models for faster processing
- Limit concurrent requests for VRAM-constrained systems
- Use Markdownify for simple content extraction (faster than full scraping)
- Cache results for repeated queries

## Security Considerations

- All processing is local - no data leaves your environment
- Evidence is signed with HSM for chain of custody
- Trust scores help identify unreliable sources
- Entity extraction helps identify potential threats
- All data is stored in your secure SME database

## Support

This extension is part of the SME v2.3.4 architecture and follows the same security and performance standards as the core system.