"""
OCR Engine for SME OCR Service.
PaddleOCR wrapper with automatic GPU/CPU detection.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Global OCR engine instance (lazy initialization)
_ocr_engine: Optional["PaddleOcrEngine"] = None


class PaddleOcrEngine:
    """
    PaddleOCR engine wrapper with GPU detection and memory management.

    Key design decisions:
    - Uses PP-OCRv4 mobile models for efficiency (6GB VRAM constraint)
    - Automatic GPU/CPU fallback based on availability
    - Environment variable override for testing (PADDLE_OCR_USE_GPU=0|1)
    - Singleton pattern to avoid reloading models
    """

    def __init__(self, use_gpu: Optional[bool] = None):
        """
        Initialize OCR engine.

        Args:
            use_gpu: Force GPU (True) or CPU (False) mode.
                     If None, auto-detect based on CUDA availability.
        """
        self._engine = None
        self._use_gpu = False
        self._engine_version = "unknown"

        # Determine GPU usage
        if use_gpu is not None:
            self._use_gpu = use_gpu
            logger.info(f"GPU mode forced: {use_gpu}")
        else:
            # Check environment variable first
            env_override = os.getenv("PADDLE_OCR_USE_GPU")
            if env_override is not None:
                self._use_gpu = env_override.lower() in ("1", "true", "yes")
                logger.info(f"GPU mode from env: {self._use_gpu}")
            else:
                # Auto-detect
                self._use_gpu = self._detect_gpu()
                logger.info(f"GPU auto-detected: {self._use_gpu}")

        self._init_engine()

    def _detect_gpu(self) -> bool:
        """
        Detect if GPU is available for PaddleOCR.

        Returns:
            True if GPU is available and usable.
        """
        try:
            # Try to import paddle and check CUDA
            import paddle

            if paddle.is_compiled_with_cuda():
                try:
                    # Try to initialize CUDA
                    paddle.device.cuda.init()
                    device_count = paddle.device.cuda.device_count()
                    if device_count > 0:
                        logger.info(
                            f"GPU detected: {device_count} CUDA device(s) available"
                        )
                        return True
                except Exception as e:
                    logger.warning(f"CUDA available but initialization failed: {e}")
                    return False

            logger.info("PaddlePaddle compiled without CUDA - using CPU")
            return False

        except ImportError:
            logger.warning("PaddlePaddle not installed - will use CPU mode")
            return False

    def _init_engine(self) -> None:
        """Initialize the PaddleOCR engine."""
        try:
            from paddleocr import PaddleOCR

            # Use PP-OCRv4 mobile models for efficiency
            # These are smaller (~10MB each) vs server models (~100MB)
            # Good enough for most documents, leaves VRAM for batch processing

            # det_model_dir and rec_model_dir can be customized
            # Using defaults which download from PaddleOCR's model hub

            self._engine = PaddleOCR(
                use_angle_cls=True,  # Enable direction classification
                lang='en',          # English language
                use_gpu=self._use_gpu,
                show_log=False,     # Reduce log noise
                # Memory optimization settings
                det_db_thresh=0.3,
                det_db_box_thresh=0.5,
                rec_batch_num=16,   # Batch size for recognition
            )

            # Get engine version
            try:
                import paddleocr
                self._engine_version = paddleocr.__version__
            except Exception:
                self._engine_version = "2.8.x"  # Approximate

            logger.info(
                f"PaddleOCR initialized: GPU={self._use_gpu}, "
                f"version={self._engine_version}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def process_image(self, image_bytes: bytes) -> list:
        """
        Process a single image and return OCR results.

        Args:
            image_bytes: Image content as bytes (PNG, JPEG, etc.)

        Returns:
            PaddleOCR result structure.
        """
        import numpy as np
        from PIL import Image

        # Convert bytes to numpy array for PaddleOCR
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)

        # Run OCR
        result = self._engine.ocr(image_array, cls=True)

        # Clear GPU cache after processing
        if self._use_gpu:
            try:
                import paddle
                paddle.device.cuda.empty_cache()
            except Exception:
                pass

        return result

    @property
    def use_gpu(self) -> bool:
        """Whether GPU is being used."""
        return self._use_gpu

    @property
    def engine_version(self) -> str:
        """PaddleOCR version string."""
        return self._engine_version


def get_ocr_engine() -> PaddleOcrEngine:
    """
    Get the singleton OCR engine instance.

    Returns:
        Initialized PaddleOcrEngine instance.
    """
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = PaddleOcrEngine()
    return _ocr_engine


def reset_ocr_engine() -> None:
    """Reset the OCR engine (useful for testing or GPU mode changes)."""
    global _ocr_engine
    _ocr_engine = None


# Need to import io for BytesIO
import io
