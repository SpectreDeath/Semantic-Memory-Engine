"""
🤖 The Sidecar Agent v2.1.0 — ForensicAgent (Pydantic-AI)

Purpose:
    A Pydantic-AI Agent wrapped in a ForensicAgent class with retry
    logic for local LLM inference failures. Returns a validated
    RhetoricalSignature object.

    v2.1.0 Finalization:
        • ForensicAgent class with RetryStrategy (3 retries, exponential backoff)
        • Updated identity-neutral system prompt (no proper nouns)
        • Retries on transient errors, NOT on ValidationError

Usage:
    import asyncio
    from src.ai.sidecar_agent import ForensicAgent, RhetoricalSignature

    agent = ForensicAgent()
    signature = asyncio.run(agent.analyze("some markdown text"))

    # Legacy API still works:
    from src.ai.sidecar_agent import analyze_evidence
    signature = asyncio.run(analyze_evidence("some markdown text"))

Constraints:
    • System prompt: no proper nouns of public figures
    • Targets local model to stay within 6GB VRAM budget
"""

import asyncio
import logging
import os
from typing import Optional

from pydantic import BaseModel, Field, ValidationError
from pydantic_ai import Agent

# Configure logging
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LM Studio / Local Model Configuration
# ---------------------------------------------------------------------------
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "openai:local-model")


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class RhetoricalSignature(BaseModel):
    """
    Validated output schema for rhetorical fingerprinting.

    Fields:
        alliteration_index : float (0.0–1.0)
            Ratio of alliterative phrase pairs to total phrase pairs.
        parallelism_score : int (≥ 0)
            Count of syntactically parallel structures detected.
        superlative_count : int (≥ 0)
            Number of superlative adjectives and adverbs found.
    """
    alliteration_index: float = Field(
        ge=0.0, le=1.0,
        description="Ratio of alliterative phrase pairs to total phrase pairs (0.0–1.0)"
    )
    parallelism_score: int = Field(
        ge=0,
        description="Count of syntactically parallel structures detected"
    )
    superlative_count: int = Field(
        ge=0,
        description="Number of superlative adjectives and adverbs found"
    )


# ---------------------------------------------------------------------------
# Retry Strategy
# ---------------------------------------------------------------------------

class RetryStrategy:
    """
    Exponential-backoff retry logic for transient local LLM failures.

    Retries on general Exceptions (connection errors, timeouts, malformed
    JSON from the model) but does NOT retry on ValidationError — those
    indicate the model output is structurally wrong, not a transient issue.

    Attributes:
        max_retries:  Maximum number of retry attempts.
        base_delay_s: Initial delay in seconds (doubles each retry).
    """

    def __init__(self, max_retries: int = 3, base_delay_s: float = 1.0) -> None:
        self.max_retries = max_retries
        self.base_delay_s = base_delay_s

    async def execute(self, coro_factory, *args, **kwargs):
        """
        Execute an async callable with retry logic.

        Args:
            coro_factory: A callable that returns an awaitable when called
                          with *args, **kwargs.

        Returns:
            The result of the successful coroutine call.

        Raises:
            ValidationError: Immediately (no retry) if the model output
                             fails Pydantic validation.
            Exception: After all retries are exhausted.
        """
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return await coro_factory(*args, **kwargs)
            except ValidationError:
                # Structural issue — retrying won't help
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.base_delay_s * (2 ** (attempt - 1))
                    logger.warning(
                        f"Attempt {attempt}/{self.max_retries} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_retries} attempts exhausted. "
                        f"Last error: {e}"
                    )

        raise last_exception  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Identity-Neutral System Prompt (Updated for v2.1.0)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a forensic rhetoric analyst operating within the SME Forensic Lab.

Analyze the provided text for stylistic markers. Identify rhythmic patterns,
structural repetitions, and superlative density. Do not speculate on the
identity of the author or include proper nouns of public figures.

Refer to the author ONLY as "The Subject" or "The Target."
Refer to the text source ONLY as "The Evidence."

Return ONLY valid JSON matching the required schema:
- alliteration_index: Count phrase pairs where consecutive major words
  share the same initial consonant sound. Divide by total phrase pairs.
  Return a float between 0.0 and 1.0.
- parallelism_score: Count instances of syntactically parallel structures
  (e.g., repeated clause patterns, anaphora, tricolons). Return an integer.
- superlative_count: Count superlative adjectives (e.g., "greatest",
  "most important", "best") and superlative adverbs. Return an integer.
"""


# ---------------------------------------------------------------------------
# ForensicAgent
# ---------------------------------------------------------------------------

class ForensicAgent:
    """
    Production-ready wrapper around the Pydantic-AI Agent.

    Features:
        • RetryStrategy for transient LLM inference failures
        • Identity-neutral system prompt
        • Singleton Pydantic-AI Agent (lazy-initialized)
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_s: float = 1.0,
    ) -> None:
        self._retry = RetryStrategy(
            max_retries=max_retries,
            base_delay_s=base_delay_s,
        )
        self._agent: Optional[Agent] = None
        logger.info(
            f"ForensicAgent initialized — retries={max_retries}, "
            f"base_delay={base_delay_s}s"
        )

    def _get_agent(self) -> Agent:
        """Lazy-init the Pydantic-AI agent singleton."""
        if self._agent is None:
            self._agent = Agent(
                model=LM_STUDIO_MODEL,
                result_type=RhetoricalSignature,
                system_prompt=SYSTEM_PROMPT,
                model_settings={
                    "temperature": 0.1,
                    "max_tokens": 256,
                },
            )
            logger.info(
                f"Pydantic-AI Agent built — model={LM_STUDIO_MODEL}, "
                f"base_url={LM_STUDIO_BASE_URL}"
            )
        return self._agent

    async def _run_agent(self, prompt: str) -> RhetoricalSignature:
        """Single attempt to run the agent."""
        agent = self._get_agent()
        result = await agent.run(prompt)
        return result.data

    async def analyze(self, markdown_text: str) -> RhetoricalSignature:
        """
        Analyze The Evidence and return a validated RhetoricalSignature.

        Uses RetryStrategy for transient LLM failures.

        Args:
            markdown_text: Cleaned Markdown from the Harvester.

        Returns:
            RhetoricalSignature with alliteration_index, parallelism_score,
            and superlative_count.

        Raises:
            ValueError: If markdown_text is empty.
            ValidationError: If the model output fails schema validation.
            Exception: After all retries exhausted on transient errors.
        """
        if not markdown_text or not markdown_text.strip():
            raise ValueError("The Evidence cannot be empty.")

        prompt = (
            "Analyze the following Evidence and extract the rhetorical signature "
            "of The Subject.\n\n"
            "--- BEGIN EVIDENCE ---\n"
            f"{markdown_text}\n"
            "--- END EVIDENCE ---"
        )

        logger.info(
            f"Submitting Evidence ({len(markdown_text):,} chars) to ForensicAgent"
        )

        signature = await self._retry.execute(self._run_agent, prompt)

        logger.info(
            f"Signature extracted — "
            f"alliteration={signature.alliteration_index:.3f}, "
            f"parallelism={signature.parallelism_score}, "
            f"superlatives={signature.superlative_count}"
        )

        return signature


# ---------------------------------------------------------------------------
# Legacy API (backward-compatible)
# ---------------------------------------------------------------------------

# Module-level singleton
_forensic_agent: Optional[ForensicAgent] = None


def get_agent() -> ForensicAgent:
    """Return the singleton ForensicAgent, creating it on first call."""
    global _forensic_agent
    if _forensic_agent is None:
        _forensic_agent = ForensicAgent()
    return _forensic_agent


async def analyze_evidence(markdown_text: str) -> RhetoricalSignature:
    """
    Legacy API — analyze The Evidence via the singleton ForensicAgent.

    Equivalent to:
        agent = ForensicAgent()
        await agent.analyze(markdown_text)
    """
    agent = get_agent()
    return await agent.analyze(markdown_text)
