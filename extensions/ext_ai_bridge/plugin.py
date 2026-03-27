import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.AIBridge")

try:
    from src.ai.provider import LLMProviderManager
except ImportError:
    LLMProviderManager = None

try:
    from src.ai.sidecar import SidecarAgent
except ImportError:
    SidecarAgent = None

try:
    from src.ai.unified_provider import UnifiedProvider
except ImportError:
    UnifiedProvider = None

try:
    from src.ai.external_ai_integration import ExternalAIConnector
except (ImportError, NameError):
    ExternalAIConnector = None

try:
    from src.ai.enterprise_ai import EnterpriseAI
except ImportError:
    EnterpriseAI = None

try:
    from src.ai.pydantic_ai_agent import PydanticAIAgent
except ImportError:
    PydanticAIAgent = None

try:
    from src.ai.smolagents_forensics import SmolAgentsForensics
except ImportError:
    SmolAgentsForensics = None

try:
    from src.ai.agent_logic import AgentLogicExecutor
except ImportError:
    AgentLogicExecutor = None

try:
    from src.ai.brain_worker import BrainWorkerManager
except ImportError:
    BrainWorkerManager = None

try:
    from src.ai.bridge_rpc import AIBridgeRPC
except ImportError:
    AIBridgeRPC = None

try:
    from src.ai.bridge import AsyncAIBridge
except ImportError:
    AsyncAIBridge = None


class AIBridgeExtension(BasePlugin):
    """
    AI Bridge Integration Extension for SME.
    Provides LLM provider management, sidecar agent execution, unified provider, external AI connector, enterprise AI integration, pydantic agent, smolagents, agent logic, brain worker, and AI bridge RPC.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.provider_manager = LLMProviderManager() if LLMProviderManager else None
        self.sidecar = SidecarAgent() if SidecarAgent else None
        self.unified = UnifiedProvider() if UnifiedProvider else None
        self.external_ai = ExternalAIConnector() if ExternalAIConnector else None
        self.enterprise_ai = EnterpriseAI() if EnterpriseAI else None
        self.pydantic_agent = PydanticAIAgent() if PydanticAIAgent else None
        self.smolagents = SmolAgentsForensics() if SmolAgentsForensics else None
        self.agent_logic = AgentLogicExecutor() if AgentLogicExecutor else None
        self.brain_worker = BrainWorkerManager() if BrainWorkerManager else None
        self.bridge_rpc = AIBridgeRPC() if AIBridgeRPC else None
        self.async_bridge = AsyncAIBridge() if AsyncAIBridge else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] AI Bridge Integration extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.manage_providers,
            self.execute_sidecar,
            self.unified_call,
            self.external_ai_call,
            self.enterprise_ai_call,
            self.pydantic_agent_run,
            self.smolagents_run,
            self.execute_agent_logic,
            self.manage_brain_workers,
            self.bridge_rpc_call,
            self.async_bridge_call,
        ]

    async def manage_providers(self, action: str, provider: str, config: dict | None = None) -> str:
        """Manage LLM providers (add, remove, update, list)."""
        if not self.provider_manager:
            return json.dumps({"error": "LLMProviderManager not available"})
        try:
            result = self.provider_manager.manage(action, provider, config)
            return json.dumps({"action": action, "provider": provider, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def execute_sidecar(self, task: str, context: dict | None = None) -> str:
        """Execute task via sidecar agent."""
        if not self.sidecar:
            return json.dumps({"error": "SidecarAgent not available"})
        try:
            result = self.sidecar.execute(task, context)
            return json.dumps({"task": task, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def unified_call(self, prompt: str, provider: str = "auto") -> str:
        """Call unified AI provider interface."""
        if not self.unified:
            return json.dumps({"error": "UnifiedProvider not available"})
        try:
            result = self.unified.call(prompt, provider)
            return json.dumps({"prompt": prompt, "provider": provider, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def external_ai_call(self, service: str, request: dict) -> str:
        """Call external AI service."""
        if not self.external_ai:
            return json.dumps({"error": "ExternalAIConnector not available"})
        try:
            result = self.external_ai.call(service, request)
            return json.dumps({"service": service, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def enterprise_ai_call(self, operation: str, params: dict) -> str:
        """Call enterprise AI integration."""
        if not self.enterprise_ai:
            return json.dumps({"error": "EnterpriseAI not available"})
        try:
            result = self.enterprise_ai.call(operation, params)
            return json.dumps({"operation": operation, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def pydantic_agent_run(self, task: str, schema: dict) -> str:
        """Run pydantic AI agent with type-safe schema."""
        if not self.pydantic_agent:
            return json.dumps({"error": "PydanticAIAgent not available"})
        try:
            result = self.pydantic_agent.run(task, schema)
            return json.dumps({"task": task, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def smolagents_run(self, task: str, tools: list[str] | None = None) -> str:
        """Run smolagents with specified tools."""
        if not self.smolagents:
            return json.dumps({"error": "SmolAgentsForensics not available"})
        try:
            result = self.smolagents.run(task, tools)
            return json.dumps({"task": task, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def execute_agent_logic(self, logic: str, input_data: dict) -> str:
        """Execute agent reasoning logic."""
        if not self.agent_logic:
            return json.dumps({"error": "AgentLogicExecutor not available"})
        try:
            result = self.agent_logic.execute(logic, input_data)
            return json.dumps({"logic": logic, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def manage_brain_workers(
        self, action: str, worker_id: str | None = None, config: dict | None = None
    ) -> str:
        """Manage distributed brain workers."""
        if not self.brain_worker:
            return json.dumps({"error": "BrainWorkerManager not available"})
        try:
            result = self.brain_worker.manage(action, worker_id, config)
            return json.dumps({"action": action, "worker_id": worker_id, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def bridge_rpc_call(self, method: str, params: dict) -> str:
        """Make AI bridge JSON-RPC call."""
        if not self.bridge_rpc:
            return json.dumps({"error": "AIBridgeRPC not available"})
        try:
            result = self.bridge_rpc.call(method, params)
            return json.dumps({"method": method, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def async_bridge_call(self, prompt: str, timeout: int = 30) -> str:
        """Make async AI bridge call."""
        if not self.async_bridge:
            return json.dumps({"error": "AsyncAIBridge not available"})
        try:
            result = self.async_bridge.call(prompt, timeout)
            return json.dumps({"prompt": prompt, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return AIBridgeExtension(manifest, nexus_api)
