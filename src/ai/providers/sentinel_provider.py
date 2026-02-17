import os
import logging
from typing import Any, Dict, Optional
from src.ai.provider import SME_AI_Provider
from src.core.config import get_config

logger = logging.getLogger("SentinelProvider")

class SentinelProvider(SME_AI_Provider):
    """
    Hardware-Aware AI Provider for the GTX 1660 Ti.
    Uses llama-cpp-python to manage GGUF models and LoRA adapters.
    """

    def __init__(self):
        self.config = get_config()
        self.model = None
        self.current_lora = None
        self._init_model()

    def _init_model(self):
        """Initialize the base GGUF model with optimized 1660 Ti settings."""
        try:
            from llama_cpp import Llama

            model_path = self.config.get_path("hardware.base_model")
            if not model_path.exists():
                logger.warning(f"Base model not found at {model_path}. sentinel_provider degraded.")
                return

            # Optimized for 6GB VRAM
            # n_gpu_layers=-1 attempts to put all on GPU
            # We'll start aggressive and let Sentinel throttle us if needed.
            self.model = Llama(
                model_path=str(model_path),
                n_gpu_layers=32,
                n_ctx=4096,
                verbose=False
            )
            logger.info(f"Sentinel (GGUF) initialized with {model_path.name}")
        except Exception as e:
            logger.error(f"Failed to load llama-cpp: {e}")

    def run(self, flow_name: str, input_data: Any) -> str:
        """Execute a forensic tool call using the loaded model."""
        if not self.model:
            return "Error: Sentinel Model not loaded."

        # Simple completion for now, simulating tool-use
        prompt = f"### System: Forensic Assistant\n### Input: {input_data}\n### Response:"
        output = self.model(
            prompt,
            max_tokens=512,
            stop=["###"],
            echo=False
        )
        return output["choices"][0]["text"].strip()

    def switch_lens(self, lens_name: str, scale: float = 1.0):
        """
        Sub-second LoRA scaling.
        lens_name corresponds to a .bin file in models/adapters/
        """
        if not self.model:
            return

        lora_path = os.path.join(self.config.get("hardware.lora_dir"), f"{lens_name}.bin")
        if not os.path.exists(lora_path):
            logger.error(f"Lens (LoRA) not found: {lora_path}")
            return

        try:
            # Some llama-cpp-python versions allow additive scaling
            # We set current scale to 0.0 (off) and new to 1.0 (on)
            # If using set_lora logic:
            if hasattr(self.model, "set_lora"):
                # Disable existing LoRA if any
                if self.current_lora:
                    old_path = os.path.join(self.config.get("hardware.lora_dir"), f"{self.current_lora}.bin")
                    self.model.set_lora(old_path, 0.0)

                self.model.set_lora(lora_path, scale)
            else:
                # Fallback to standard apply (full replacement)
                self.model.apply_lora_adapter(lora_path)

            self.current_lora = lens_name
            logger.info(f"Sentinel shifted lens to: {lens_name} (scale={scale})")
        except Exception as e:
            logger.error(f"LoRA shift failed: {e}")

    def offload_to_ram(self):
        """
        Hardware-triggered layer offloading.
        Moves layers from VRAM to System RAM to prevent CUDA OOM.
        """
        if not self.model:
            return

        logger.warning("Sentinel: Moving model layers to System RAM to preserve VRAM.")
        # Currently, llama-cpp doesn't support live layer shifting without reload.
        # We perform a fast reload with reduced GPU layers.
        # Milestone 2 Optimization: Re-init with half GPU layers.
        try:
            model_path = self.config.get_path("hardware.base_model")
            self.model = None # Release VRAM
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            from llama_cpp import Llama
            self.model = Llama(
                model_path=str(model_path),
                n_gpu_layers=10, # Reduced from 32
                n_ctx=4096,
                verbose=False
            )
            # Re-apply LoRA if active
            if self.current_lora:
                self.switch_lens(self.current_lora)
        except Exception as e:
            logger.error(f"Offload re-init failed: {e}")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "provider": "sentinel",
            "backend": "llama-cpp",
            "active_lens": self.current_lora,
            "vram_strategy": "gguf-dynamic"
        }