"""
SME JSON-RPC Bridge
Bridge between VS Code Extension Host and SME Python Backend.
"""

import sys
import json
import logging
import asyncio
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SME-Bridge")

class AsyncSMEBridge:
    """Handles JSON-RPC requests from the VS Code frontend asynchronously."""
    
    def __init__(self):
        # Initialize SME components
        try:
            from src.core.data_manager import DataManager
            from src.core.semantic_db import SemanticMemory
            self.data_manager = DataManager()
            self.memory = SemanticMemory()
        except ImportError as e:
            logger.warning(f"Could not load core modules: {e}. Running in degraded mock mode.")
            self.data_manager = None
            self.memory = None

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single JSON-RPC request asynchronously."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.info(f"Received request: {method}")

        try:
            if method == "get_memory_nodes":
                result = await self.get_memory_nodes(params)
            elif method == "read_directory":
                result = await self.read_directory(params)
            elif method == "read_file":
                result = await self.read_file(params)
            elif method == "search_memory":
                result = await self.search_memory(params)
            elif method == "index_project":
                result = await self.index_project(params)
            elif method == "analyze_document":
                result = await self.analyze_document(params)
            elif method == "get_semantic_graph":
                result = await self.get_semantic_graph(params)
            elif method == "log_telemetry":
                result = await self.log_telemetry(params)
            else:
                return self.error_response(request_id, -32601, "Method not found")

            return self.success_response(request_id, result)
        except Exception as e:
            logger.exception(f"Error handling {method}")
            return self.error_response(request_id, -32000, str(e))

    async def get_memory_nodes(self, params: Dict) -> Any:
        if self.memory:
            # Use real memory nodes by extracting from chromadb.
            # In a real implementation this would fetch actual context objects.
            try:
                results = self.memory.collection.get()
                nodes = []
                for i, id_ in enumerate(results["ids"]):
                    nodes.append({"id": id_, "label": f"Node {id_}", "type": "document"})
                return nodes
            except Exception as e:
                logger.error(f"Error fetching memory nodes: {e}")
        
        # Fallback to mock
        return [
            {"id": "ctx_001", "label": "Project Odyssey: Orchestration", "type": "context"},
            {"id": "doc_442", "label": "Incident Report: VRAM Spike", "type": "document"},
            {"id": "fpt_991", "label": "Stylometric Profile: Suspect_Alpha", "type": "fingerprint"},
            {"id": "auth_01", "label": "Author: spectre", "type": "context"}
        ]

    async def search_memory(self, params: Dict) -> Any:
        query = params.get("query", "")
        if self.memory and query:
            try:
                # Perform a threaded or async friendly call
                loop = asyncio.get_running_loop()
                results = await loop.run_in_executor(
                    None, 
                    lambda: self.memory.search_with_semantic_expansion(query, n_results=5)
                )
                
                matches = []
                if "ids" in results and results["ids"]:
                    for idx, doc_id in enumerate(results["ids"][0]):
                        doc_text = results["documents"][0][idx] if "documents" in results else ""
                        matches.append({"id": doc_id, "text": doc_text})
                
                if matches:
                    return matches
            except Exception as e:
                logger.error(f"Error searching memory: {e}")
                
        # Fallback to mock
        return [{"id": "match_1", "text": f"Found semantic alignment for '{query}' in Cluster: Forensics"}]

    async def index_project(self, params: Dict) -> Any:
        path = params.get("path", ".")
        # Simulate some asynchronous work. We could trigger a real file walk and indexing here.
        await asyncio.sleep(0.5)
        return {"status": "success", "message": f"Successfully indexed {path} into SME Vector Store."}

    async def analyze_document(self, params: Dict) -> Any:
        path = params.get("path", "unknown")
        # Mocking forensic outliers (burstiness, entropy) for testing UI decorations
        return {
            "markers": [
                {"line": 5, "type": "high_burstiness", "score": 0.92, "message": "Low entropy burst detected. Possible synthetic smoothing."},
                {"line": 12, "type": "styling_outlier", "score": 0.85, "message": "Stylometric shift: Rhetorical pattern mismatch from baseline."},
                {"line": 25, "type": "high_entropy", "score": 0.12, "message": "Extremely low entropy. High probability of boilerplate or masking."}
            ],
            "global_score": 0.74,
            "verdict": "SUSPICIOUS"
        }

    async def get_semantic_graph(self, params: Dict) -> Any:
        # Returning mock nodes and links for D3.js visualization. Real implementation
        # would interact with self.memory.semantic_graph but D3 expects generic graph formats
        return {
            "nodes": [
                {"id": "ctx_001", "label": "Odyssey", "group": 1, "size": 20},
                {"id": "doc_442", "label": "VRAM Spike", "group": 2, "size": 15},
                {"id": "fpt_991", "label": "Suspect_Alpha", "group": 3, "size": 15},
                {"id": "auth_01", "label": "spectre", "group": 1, "size": 25},
                {"id": "ent_01", "label": "Ollama", "group": 4, "size": 10},
                {"id": "ent_02", "label": "GTX-1660-Ti", "group": 4, "size": 10},
            ],
            "links": [
                {"source": "ctx_001", "target": "auth_01", "value": 5},
                {"source": "ctx_001", "target": "doc_442", "value": 2},
                {"source": "doc_442", "target": "ent_02", "value": 3},
                {"source": "fpt_991", "target": "auth_01", "value": 1},
                {"source": "auth_01", "target": "ent_01", "value": 4},
            ]
        }

    async def read_directory(self, params: Dict) -> Any:
        # Mapping semantic directory mapping
        path = params.get("path", "/")
        if path == "/":
            return [
                ["Contexts", 2],
                ["Documents", 2],
                ["Fingerprints", 2],
                ["Author Profiles", 2]
            ]
        
        cluster = path.split("/")[1]
        return [
            [f"{cluster}_summary_v1.json", 1],
            [f"{cluster}_raw_evidence.md", 1],
            ["archive", 2]
        ]

    async def read_file(self, params: Dict) -> Any:
        path = params.get("path", "unknown")
        # Returning structured content that looks "forensic"
        return {
            "content": json.dumps({
                "node_id": path,
                "classification": "RESTRICTED",
                "extracted_entities": ["spectre", "Ollama", "GTX-1660-Ti"],
                "confidence_score": 0.98,
                "summary": "This semantic node represents a core memory fragment of the SME Odyssey modernization."
            }, indent=2)
        }

    async def log_telemetry(self, params: Dict) -> Any:
        # Pseudo-code to write to Nexus or simply log it.
        action = params.get("action", "unknown")
        logger.info(f"TELEMETRY: User action captured -> {action}, params: {params}")
        # In the future, this will connect to self.nexus.execute("INSERT INTO telemetry ...")
        return {"status": "success", "logged": True}

    def success_response(self, request_id: Any, result: Any) -> Dict:
        return {"jsonrpc": "2.0", "result": result, "id": request_id}

    def error_response(self, request_id: Any, code: int, message: str) -> Dict:
        return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": request_id}

async def process_messages(bridge: AsyncSMEBridge):
    """Reads JSON-RPC messages from stdin asynchronously."""
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    logger.info("SME Bridge started")

    while True:
        line = await reader.readline()
        if not line:
            break
        
        try:
            request = json.loads(line.decode('utf-8'))
            
            # Fire and forget request handling so we don't block reading
            asyncio.create_task(handle_and_respond(bridge, request))
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse line: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

async def handle_and_respond(bridge: AsyncSMEBridge, request: Dict):
    loop = asyncio.get_running_loop()
    try:
        response = await bridge.handle_request(request)
        response_str = json.dumps(response) + "\\n"
        # Write to stdout synchronosuly via run_in_executor to avoid blocking the loop
        await loop.run_in_executor(None, sys.stdout.write, response_str)
        await loop.run_in_executor(None, sys.stdout.flush)
    except Exception as e:
         logger.error(f"Error handling request and responding: {e}")


async def main():
    bridge = AsyncSMEBridge()
    await process_messages(bridge)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
