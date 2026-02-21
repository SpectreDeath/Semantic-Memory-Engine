"""
Unified AI Provider - Centralized AI access with smart routing

This module provides a unified interface for all AI providers with:
- Automatic provider fallback
- Response caching
- Cost tracking
- Latency optimization
- Streaming support
"""

import os
import asyncio
import hashlib
import time
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("sme.unified_ai")

# Try to import providers
try:
    import aiohttp
except ImportError:
    aiohttp = None


class ProviderType(Enum):
    """Supported AI provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LANGFLOW = "langflow"
    SENTINEL = "sentinel"
    MOCK = "mock"


@dataclass
class AIRequest:
    """Standardized AI request."""
    prompt: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: Optional[str] = None
    provider: Optional[ProviderType] = None
    stream: bool = False


@dataclass
class AIResponse:
    """Standardized AI response."""
    content: str
    provider: str
    model: str
    latency_ms: float
    tokens_used: int = 0
    cached: bool = False
    cost_usd: float = 0.0


class ResponseCache:
    """Simple in-memory cache for AI responses."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, AIResponse] = {}
        self.max_size = max_size
    
    def _hash_request(self, request: AIRequest) -> str:
        """Generate cache key from request."""
        key_data = f"{request.prompt}:{request.model}:{request.temperature}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, request: AIRequest) -> Optional[AIResponse]:
        """Get cached response if available."""
        key = self._hash_request(request)
        return self.cache.get(key)
    
    def set(self, request: AIRequest, response: AIResponse):
        """Cache a response."""
        key = self._hash_request(request)
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[key] = response


class UnifiedAIProvider:
    """
    Unified AI Provider with automatic failover and smart routing.
    
    Features:
    - Automatic provider fallback
    - Response caching
    - Cost tracking
    - Latency optimization
    - Streaming support
    """
    
    def __init__(
        self,
        default_provider: ProviderType = ProviderType.OLLAMA,
        enable_cache: bool = True,
        cache_size: int = 1000
    ):
        self.default_provider = default_provider
        self.enable_cache = enable_cache
        self.cache = ResponseCache(cache_size) if enable_cache else None
        
        # Provider configurations from environment
        self.providers: Dict[ProviderType, Dict[str, Any]] = {}
        self._init_providers()
        
        # Tracking
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "total_cost": 0.0,
            "by_provider": defaultdict(int),
            "errors": defaultdict(int)
        }
        
        logger.info(f"UnifiedAI initialized with default: {default_provider.value}")
    
    def _init_providers(self):
        """Initialize provider configurations from environment."""
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            self.providers[ProviderType.OPENAI] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "default_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            }
        
        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            self.providers[ProviderType.ANTHROPIC] = {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
                "default_model": os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
            }
        
        # Ollama (local)
        self.providers[ProviderType.OLLAMA] = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "default_model": os.getenv("OLLAMA_MODEL", "llama3.2")
        }
        
        # Langflow
        self.providers[ProviderType.LANGFLOW] = {
            "base_url": os.getenv("LANGFLOW_BASE_URL", "http://localhost:7860"),
            "flow_id": os.getenv("LANGFLOW_FLOW_ID", "")
        }
        
        logger.info(f"Configured providers: {list(self.providers.keys())}")
    
    async def generate(
        self,
        request: AIRequest,
        prefer_providers: Optional[List[ProviderType]] = None
    ) -> AIResponse:
        """
        Generate AI response with automatic failover.
        
        Args:
            request: The AI request
            prefer_providers: Preferred providers in order (falls back to defaults)
        
        Returns:
            AIResponse with content and metadata
        """
        self.stats["total_requests"] += 1
        
        # Check cache
        if self.cache and not request.stream:
            cached = self.cache.get(request)
            if cached:
                self.stats["cache_hits"] += 1
                logger.debug("Cache hit!")
                return cached
        
        # Build provider order
        providers_to_try = []
        
        # Add preferred providers
        if prefer_providers:
            providers_to_try.extend(prefer_providers)
        
        # Add default provider
        if request.provider and request.provider not in providers_to_try:
            providers_to_try.append(request.provider)
        elif self.default_provider not in providers_to_try:
            providers_to_try.append(self.default_provider)
        
        # Add all other available providers as fallback
        for p in self.providers:
            if p not in providers_to_try:
                providers_to_try.append(p)
        
        # Try each provider
        last_error = None
        for provider_type in providers_to_try:
            if provider_type not in self.providers:
                continue
            
            try:
                response = await self._call_provider(provider_type, request)
                self.stats["by_provider"][provider_type.value] += 1
                
                # Cache if not streaming
                if self.cache and not request.stream:
                    self.cache.set(request, response)
                
                return response
                
            except Exception as e:
                last_error = e
                self.stats["errors"][provider_type.value] += 1
                logger.warning(f"Provider {provider_type.value} failed: {e}")
                continue
        
        # All providers failed
        raise Exception(f"All AI providers failed. Last error: {last_error}")
    
    async def _call_provider(
        self,
        provider: ProviderType,
        request: AIRequest
    ) -> AIResponse:
        """Call a specific provider."""
        
        start_time = time.time()
        
        if provider == ProviderType.OPENAI:
            return await self._call_openai(request, start_time)
        elif provider == ProviderType.ANTHROPIC:
            return await self._call_anthropic(request, start_time)
        elif provider == ProviderType.OLLAMA:
            return await self._call_ollama(request, start_time)
        elif provider == ProviderType.LANGFLOW:
            return await self._call_langflow(request, start_time)
        elif provider == ProviderType.MOCK:
            return await self._call_mock(request, start_time)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_openai(self, request: AIRequest, start_time: float) -> AIResponse:
        """Call OpenAI API."""
        config = self.providers[ProviderType.OPENAI]
        
        if not aiohttp:
            raise ImportError("aiohttp required for OpenAI")
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": request.model or config["default_model"],
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        url = f"{config['base_url']}/chat/completions"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"OpenAI error {resp.status}: {text}")
                
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                
                # Calculate cost
                cost = self._calculate_openai_cost(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                    payload["model"]
                )
                
                self.stats["total_cost"] += cost
                
                return AIResponse(
                    content=content,
                    provider="openai",
                    model=payload["model"],
                    latency_ms=(time.time() - start_time) * 1000,
                    tokens_used=usage.get("total_tokens", 0),
                    cost_usd=cost
                )
    
    async def _call_anthropic(self, request: AIRequest, start_time: float) -> AIResponse:
        """Call Anthropic Claude API."""
        config = self.providers[ProviderType.ANTHROPIC]
        
        if not aiohttp:
            raise ImportError("aiohttp required for Anthropic")
        
        headers = {
            "x-api-key": config["api_key"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "user", "content": request.prompt}]
        
        payload = {
            "model": request.model or config["default_model"],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages
        }
        
        if request.system_prompt:
            payload["system"] = request.system_prompt
        
        url = f"{config['base_url']}/v1/messages"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Anthropic error {resp.status}: {text}")
                
                data = await resp.json()
                content = data["content"][0]["text"]
                usage = data.get("usage", {})
                
                cost = self._calculate_anthropic_cost(
                    usage.get("input_tokens", 0),
                    usage.get("output_tokens", 0),
                    payload["model"]
                )
                
                self.stats["total_cost"] += cost
                
                return AIResponse(
                    content=content,
                    provider="anthropic",
                    model=payload["model"],
                    latency_ms=(time.time() - start_time) * 1000,
                    tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                    cost_usd=cost
                )
    
    async def _call_ollama(self, request: AIRequest, start_time: float) -> AIResponse:
        """Call local Ollama."""
        config = self.providers[ProviderType.OLLAMA]
        
        if not aiohttp:
            raise ImportError("aiohttp required for Ollama")
        
        payload = {
            "model": request.model or config["default_model"],
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_ctx": request.max_tokens
            }
        }
        
        if request.system_prompt:
            payload["system"] = request.system_prompt
        
        url = f"{config['base_url']}/api/generate"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Ollama error {resp.status}: {text}")
                
                data = await resp.json()
                content = data.get("response", "")
                
                return AIResponse(
                    content=content,
                    provider="ollama",
                    model=payload["model"],
                    latency_ms=(time.time() - start_time) * 1000,
                    tokens_used=data.get("eval_count", 0),
                    cost_usd=0.0  # Local, no cost
                )
    
    async def _call_langflow(self, request: AIRequest, start_time: float) -> AIResponse:
        """Call Langflow API."""
        config = self.providers[ProviderType.LANGFLOW]
        
        if not aiohttp:
            raise ImportError("aiohttp required for Langflow")
        
        payload = {
            "input_value": request.prompt,
            "output_type": "text",
            "input_type": "chat"
        }
        
        if config.get("flow_id"):
            url = f"{config['base_url']}/api/v1/run/{config['flow_id']}"
        else:
            url = f"{config['base_url']}/api/v1/predict"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Langflow error {resp.status}: {text}")
                
                data = await resp.json()
                # Langflow response format varies
                content = data.get("outputs", [{}])[0].get("outputs", [{}])[0].get("results", {}).get("text", {}).get("text", str(data))
                
                return AIResponse(
                    content=content,
                    provider="langflow",
                    model="langflow",
                    latency_ms=(time.time() - start_time) * 1000,
                    cost_usd=0.0
                )
    
    async def _call_mock(self, request: AIRequest, start_time: float) -> AIResponse:
        """Mock provider for testing."""
        await asyncio.sleep(0.1)  # Simulate latency
        
        return AIResponse(
            content=f"Mock response to: {request.prompt[:50]}...",
            provider="mock",
            model="mock-model",
            latency_ms=100.0,
            cost_usd=0.0
        )
    
    def _calculate_openai_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Calculate OpenAI API cost."""
        pricing = {
            "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
            "gpt-4o": {"prompt": 0.0025, "completion": 0.01},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002}
        }
        
        p = pricing.get(model, pricing["gpt-4o-mini"])
        return (prompt_tokens / 1000 * p["prompt"]) + (completion_tokens / 1000 * p["completion"])
    
    def _calculate_anthropic_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate Anthropic API cost."""
        pricing = {
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075}
        }
        
        p = pricing.get(model, pricing["claude-3-haiku-20240307"])
        return (input_tokens / 1000 * p["input"]) + (output_tokens / 1000 * p["output"])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        return {
            "total_requests": self.stats["total_requests"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": self.stats["cache_hits"] / max(1, self.stats["total_requests"]),
            "total_cost": self.stats["total_cost"],
            "by_provider": dict(self.stats["by_provider"]),
            "errors": dict(self.stats["errors"])
        }
    
    def clear_cache(self):
        """Clear the response cache."""
        if self.cache:
            self.cache.cache.clear()
            logger.info("Cache cleared")


# Global instance
_unified_ai: Optional[UnifiedAIProvider] = None


def get_unified_ai() -> UnifiedAIProvider:
    """Get the global UnifiedAIProvider instance."""
    global _unified_ai
    if _unified_ai is None:
        _unified_ai = UnifiedAIProvider()
    return _unified_ai


# Convenience function
async def generate(prompt: str, **kwargs) -> AIResponse:
    """Quick generate function."""
    return await get_unified_ai().generate(AIRequest(prompt=prompt, **kwargs))
