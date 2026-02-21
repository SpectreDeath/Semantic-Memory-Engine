"""
External AI Services Integration

Provides integration with external AI services like OpenAI, Anthropic, 
Google AI, and other LLM providers for enhanced extension capabilities.
"""

import asyncio
import logging
import json
import time
import requests
import aiohttp
from typing import Dict, Any, List, Optional, Callable, Union, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import hashlib
import hmac
import base64
from pathlib import Path

logger = logging.getLogger("SME.ExternalAI")

class AIProvider(Enum):
    """Supported AI service providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_AI = "google_ai"
    AZURE_OPENAI = "azure_openai"
    LOCAL_OLLAMA = "local_ollama"
    CUSTOM = "custom"

@dataclass
class AIRequest:
    """AI service request data structure."""
    provider: AIProvider
    model: str
    prompt: str
    max_tokens: int
    temperature: float
    system_prompt: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AIResponse:
    """AI service response data structure."""
    provider: AIProvider
    model: str
    content: str
    usage: Dict[str, int]
    latency: float
    timestamp: datetime
    request_id: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AIProviderConfig:
    """Configuration for an AI service provider."""
    provider: AIProvider
    api_key: str
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    default_model: str = "gpt-3.5-turbo"
    max_retries: int = 3
    timeout: int = 30
    rate_limit_requests: int = 60
    rate_limit_window: int = 60
    enabled: bool = True

class AIProviderInterface(ABC):
    """Abstract interface for AI service providers."""
    
    @abstractmethod
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using the AI service."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the AI service is healthy."""
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for the provider."""
        pass

class OpenAIProvider(AIProviderInterface):
    """OpenAI API provider implementation."""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.session = None
        self.request_count = 0
        self.last_reset = time.time()
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'errors': 0
        }
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using OpenAI API."""
        start_time = time.time()
        
        try:
            # Rate limiting
            await self._check_rate_limit()
            
            # Prepare request
            headers = {
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json'
            }
            
            messages = []
            if request.system_prompt:
                messages.append({'role': 'system', 'content': request.system_prompt})
            
            messages.append({'role': 'user', 'content': request.prompt})
            
            payload = {
                'model': request.model or self.config.default_model,
                'messages': messages,
                'max_tokens': request.max_tokens,
                'temperature': request.temperature,
                'user': request.user_context.get('user_id', 'sme_extension') if request.user_context else 'sme_extension'
            }
            
            # Make request
            url = f"{self.config.base_url or 'https://api.openai.com/v1'}/chat/completions"
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(url, headers=headers, json=payload, timeout=self.config.timeout) as response:
                if response.status != 200:
                    raise Exception(f"OpenAI API error: {response.status} - {await response.text()}")
                
                data = await response.json()
                
                # Parse response
                content = data['choices'][0]['message']['content']
                usage = data.get('usage', {})
                
                # Calculate cost (approximate)
                cost = self._calculate_cost(usage, request.model or self.config.default_model)
                
                # Update stats
                self._update_stats(usage, cost)
                
                latency = time.time() - start_time
                
                return AIResponse(
                    provider=AIProvider.OPENAI,
                    model=request.model or self.config.default_model,
                    content=content,
                    usage=usage,
                    latency=latency,
                    timestamp=datetime.now(),
                    request_id=data.get('id', ''),
                    metadata={'cost': cost, 'prompt_tokens': usage.get('prompt_tokens', 0)}
                )
                
        except Exception as e:
            self.usage_stats['errors'] += 1
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is healthy."""
        try:
            headers = {'Authorization': f'Bearer {self.config.api_key}'}
            url = f"{self.config.base_url or 'https://api.openai.com/v1'}/models"
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            'provider': 'OpenAI',
            'total_requests': self.usage_stats['total_requests'],
            'total_tokens': self.usage_stats['total_tokens'],
            'total_cost': self.usage_stats['total_cost'],
            'errors': self.usage_stats['errors'],
            'request_count': self.request_count,
            'last_reset': self.last_reset
        }
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.last_reset > self.config.rate_limit_window:
            self.request_count = 0
            self.last_reset = current_time
        
        # Check if we've hit the limit
        if self.request_count >= self.config.rate_limit_requests:
            wait_time = self.config.rate_limit_window - (current_time - self.last_reset)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.last_reset = time.time()
        
        self.request_count += 1
    
    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate approximate cost based on usage."""
        # OpenAI pricing (approximate)
        pricing = {
            'gpt-3.5-turbo': {'prompt': 0.0015, 'completion': 0.002},
            'gpt-4': {'prompt': 0.03, 'completion': 0.06},
            'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03}
        }
        
        model_pricing = pricing.get(model, pricing['gpt-3.5-turbo'])
        
        prompt_cost = (usage.get('prompt_tokens', 0) / 1000) * model_pricing['prompt']
        completion_cost = (usage.get('completion_tokens', 0) / 1000) * model_pricing['completion']
        
        return prompt_cost + completion_cost
    
    def _update_stats(self, usage: Dict[str, int], cost: float):
        """Update usage statistics."""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_tokens'] += usage.get('total_tokens', 0)
        self.usage_stats['total_cost'] += cost

class AnthropicProvider(AIProviderInterface):
    """Anthropic Claude API provider implementation."""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.session = None
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'errors': 0
        }
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using Anthropic Claude API."""
        start_time = time.time()
        
        try:
            # Prepare request
            headers = {
                'x-api-key': self.config.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            payload = {
                'model': request.model or self.config.default_model,
                'max_tokens': request.max_tokens,
                'temperature': request.temperature,
                'messages': [
                    {'role': 'user', 'content': request.prompt}
                ]
            }
            
            if request.system_prompt:
                payload['system'] = request.system_prompt
            
            # Make request
            url = f"{self.config.base_url or 'https://api.anthropic.com'}/v1/messages"
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.post(url, headers=headers, json=payload, timeout=self.config.timeout) as response:
                if response.status != 200:
                    raise Exception(f"Anthropic API error: {response.status} - {await response.text()}")
                
                data = await response.json()
                
                # Parse response
                content = data['content'][0]['text']
                usage = data.get('usage', {})
                
                # Calculate cost
                cost = self._calculate_cost(usage, request.model or self.config.default_model)
                
                # Update stats
                self._update_stats(usage, cost)
                
                latency = time.time() - start_time
                
                return AIResponse(
                    provider=AIProvider.ANTHROPIC,
                    model=request.model or self.config.default_model,
                    content=content,
                    usage=usage,
                    latency=latency,
                    timestamp=datetime.now(),
                    request_id=data.get('id', ''),
                    metadata={'cost': cost}
                )
                
        except Exception as e:
            self.usage_stats['errors'] += 1
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Anthropic API is healthy."""
        try:
            headers = {
                'x-api-key': self.config.api_key,
                'anthropic-version': '2023-06-01'
            }
            url = f"{self.config.base_url or 'https://api.anthropic.com'}/v1/models"
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Anthropic health check failed: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            'provider': 'Anthropic',
            'total_requests': self.usage_stats['total_requests'],
            'total_tokens': self.usage_stats['total_tokens'],
            'total_cost': self.usage_stats['total_cost'],
            'errors': self.usage_stats['errors']
        }
    
    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate approximate cost based on usage."""
        # Anthropic pricing (approximate)
        pricing = {
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
            'claude-3-opus': {'input': 0.015, 'output': 0.075}
        }
        
        model_pricing = pricing.get(model, pricing['claude-3-sonnet'])
        
        input_cost = (usage.get('input_tokens', 0) / 1000) * model_pricing['input']
        output_cost = (usage.get('output_tokens', 0) / 1000) * model_pricing['output']
        
        return input_cost + output_cost
    
    def _update_stats(self, usage: Dict[str, int], cost: float):
        """Update usage statistics."""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_tokens'] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
        self.usage_stats['total_cost'] += cost

class LocalOllamaProvider(AIProviderInterface):
    """Local Ollama provider implementation."""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'errors': 0
        }
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using local Ollama."""
        start_time = time.time()
        
        try:
            # Prepare request
            payload = {
                'model': request.model or self.config.default_model,
                'prompt': request.prompt,
                'stream': False,
                'options': {
                    'temperature': request.temperature,
                    'num_ctx': request.max_tokens
                }
            }
            
            if request.system_prompt:
                payload['system'] = request.system_prompt
            
            # Make request
            url = f"{self.config.base_url or 'http://localhost:11434'}/api/generate"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=self.config.timeout) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status} - {await response.text()}")
                    
                    data = await response.json()
                    
                    # Parse response
                    content = data.get('response', '')
                    eval_count = data.get('eval_count', 0)
                    prompt_eval_count = data.get('prompt_eval_count', 0)
                    
                    usage = {
                        'prompt_tokens': prompt_eval_count,
                        'completion_tokens': eval_count,
                        'total_tokens': prompt_eval_count + eval_count
                    }
                    
                    # Update stats (no cost for local)
                    self._update_stats(usage)
                    
                    latency = time.time() - start_time
                    
                    return AIResponse(
                        provider=AIProvider.LOCAL_OLLAMA,
                        model=request.model or self.config.default_model,
                        content=content,
                        usage=usage,
                        latency=latency,
                        timestamp=datetime.now(),
                        request_id=f"ollama_{int(time.time())}",
                        metadata={'model_loaded': data.get('model', '')}
                    )
                    
        except Exception as e:
            self.usage_stats['errors'] += 1
            logger.error(f"Ollama API error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy."""
        try:
            url = f"{self.config.base_url or 'http://localhost:11434'}/api/tags"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            'provider': 'Local Ollama',
            'total_requests': self.usage_stats['total_requests'],
            'total_tokens': self.usage_stats['total_tokens'],
            'total_cost': 0.0,  # Local, no cost
            'errors': self.usage_stats['errors']
        }
    
    def _update_stats(self, usage: Dict[str, int]):
        """Update usage statistics."""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_tokens'] += usage.get('total_tokens', 0)

class ExternalAIIntegration:
    """
    External AI Services Integration Manager.
    """
    
    def __init__(self):
        self.providers: Dict[AIProvider, AIProviderInterface] = {}
        self.configs: Dict[AIProvider, AIProviderConfig] = {}
        self.default_provider: Optional[AIProvider] = None
        self.fallback_providers: List[AIProvider] = []
        self.request_history: List[AIResponse] = []
        self.cost_tracking = {
            'total_cost': 0.0,
            'daily_cost': defaultdict(float),
            'monthly_cost': defaultdict(float)
        }
        
        logger.info("External AI Integration initialized")
    
    def add_provider(self, config: AIProviderConfig):
        """Add an AI service provider."""
        if config.provider in self.providers:
            logger.warning(f"Provider {config.provider.value} already exists, replacing...")
        
        # Create provider instance
        if config.provider == AIProvider.OPENAI:
            provider = OpenAIProvider(config)
        elif config.provider == AIProvider.ANTHROPIC:
            provider = AnthropicProvider(config)
        elif config.provider == AIProvider.LOCAL_OLLAMA:
            provider = LocalOllamaProvider(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        self.providers[config.provider] = provider
        self.configs[config.provider] = config
        
        # Set default provider if not set
        if not self.default_provider and config.enabled:
            self.default_provider = config.provider
        
        logger.info(f"Added provider: {config.provider.value}")
    
    def set_default_provider(self, provider: AIProvider):
        """Set the default AI provider."""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider.value} not configured")
        
        self.default_provider = provider
        logger.info(f"Set default provider: {provider.value}")
    
    def add_fallback_provider(self, provider: AIProvider):
        """Add a fallback provider."""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider.value} not configured")
        
        if provider not in self.fallback_providers:
            self.fallback_providers.append(provider)
            logger.info(f"Added fallback provider: {provider.value}")
    
    async def generate_text(self, prompt: str, model: Optional[str] = None, 
                          temperature: float = 0.7, max_tokens: int = 1000,
                          system_prompt: Optional[str] = None,
                          user_context: Optional[Dict[str, Any]] = None,
                          preferred_provider: Optional[AIProvider] = None) -> AIResponse:
        """Generate text using the best available AI provider."""
        
        # Determine provider to use
        providers_to_try = []
        
        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)
        
        if self.default_provider and self.default_provider not in providers_to_try:
            providers_to_try.append(self.default_provider)
        
        providers_to_try.extend([p for p in self.fallback_providers if p not in providers_to_try])
        
        # Try each provider until one succeeds
        last_error = None
        
        for provider_type in providers_to_try:
            provider = self.providers[provider_type]
            config = self.configs[provider_type]
            
            if not config.enabled:
                continue
            
            try:
                # Health check
                if not await provider.health_check():
                    logger.warning(f"Provider {provider_type.value} is not healthy")
                    continue
                
                # Generate text
                request = AIRequest(
                    provider=provider_type,
                    model=model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                    user_context=user_context,
                    metadata={'preferred_provider': preferred_provider.value if preferred_provider else None}
                )
                
                response = await provider.generate_text(request)
                
                # Track cost
                if hasattr(response.metadata, 'cost'):
                    self._track_cost(response.metadata['cost'], response.timestamp)
                
                # Add to history
                self.request_history.append(response)
                
                # Keep only last 1000 requests
                if len(self.request_history) > 1000:
                    self.request_history = self.request_history[-1000:]
                
                logger.info(f"Successfully generated text using {provider_type.value}")
                return response
                
            except Exception as e:
                last_error = e
                logger.error(f"Provider {provider_type.value} failed: {e}")
                continue
        
        # If we get here, all providers failed
        raise Exception(f"All AI providers failed. Last error: {last_error}")
    
    async def batch_generate(self, requests: List[AIRequest]) -> List[AIResponse]:
        """Generate text for multiple requests efficiently."""
        responses = []
        
        for request in requests:
            try:
                response = await self.generate_text(
                    prompt=request.prompt,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    system_prompt=request.system_prompt,
                    user_context=request.user_context,
                    preferred_provider=request.provider
                )
                responses.append(response)
            except Exception as e:
                logger.error(f"Batch request failed: {e}")
                responses.append(AIResponse(
                    provider=request.provider,
                    model=request.model or self.configs[request.provider].default_model,
                    content=f"Error: {str(e)}",
                    usage={'error': True},
                    latency=0.0,
                    timestamp=datetime.now(),
                    request_id=f"error_{int(time.time())}"
                ))
        
        return responses
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers."""
        stats = {}
        
        for provider_type, provider in self.providers.items():
            config = self.configs[provider_type]
            stats[provider_type.value] = {
                'enabled': config.enabled,
                'default_model': config.default_model,
                'usage_stats': provider.get_usage_stats()
            }
        
        return {
            'default_provider': self.default_provider.value if self.default_provider else None,
            'fallback_providers': [p.value for p in self.fallback_providers],
            'provider_stats': stats,
            'cost_tracking': self.cost_tracking,
            'total_requests': len(self.request_history)
        }
    
    def get_cost_report(self, period: str = 'daily') -> Dict[str, Any]:
        """Get cost report for a specific period."""
        if period == 'daily':
            return dict(self.cost_tracking['daily_cost'])
        elif period == 'monthly':
            return dict(self.cost_tracking['monthly_cost'])
        else:
            return {
                'total_cost': self.cost_tracking['total_cost'],
                'daily_cost': dict(self.cost_tracking['daily_cost']),
                'monthly_cost': dict(self.cost_tracking['monthly_cost'])
            }
    
    def _track_cost(self, cost: float, timestamp: datetime):
        """Track AI service costs."""
        self.cost_tracking['total_cost'] += cost
        
        # Daily tracking
        day_key = timestamp.strftime('%Y-%m-%d')
        self.cost_tracking['daily_cost'][day_key] += cost
        
        # Monthly tracking
        month_key = timestamp.strftime('%Y-%m')
        self.cost_tracking['monthly_cost'][month_key] += cost
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        results = {}
        
        for provider_type, provider in self.providers.items():
            try:
                results[provider_type.value] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {provider_type.value}: {e}")
                results[provider_type.value] = False
        
        return results
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration."""
        return {
            'default_provider': self.default_provider.value if self.default_provider else None,
            'fallback_providers': [p.value for p in self.fallback_providers],
            'providers': {
                p.value: {
                    'api_key': '***' if config.api_key else None,  # Don't expose API keys
                    'base_url': config.base_url,
                    'default_model': config.default_model,
                    'enabled': config.enabled
                }
                for p, config in self.configs.items()
            },
            'cost_tracking': self.cost_tracking,
            'request_count': len(self.request_history)
        }


# Global External AI Integration instance
external_ai = ExternalAIIntegration()


def get_external_ai() -> ExternalAIIntegration:
    """Get the global External AI Integration instance."""
    return external_ai