"""
Cross-Modal Auditor Extension

Validates image-text alignment using CLIP model and NLP parsing.
Provides the audit_multimodal_sync() tool for multimodal hallucination detection.
"""

import os
import sys
import logging
import warnings
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

try:
    import torch
    import torch.nn.functional as F
    from PIL import Image
    from transformers import CLIPProcessor, CLIPModel
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.tag import pos_tag
    from nltk.corpus import stopwords
except ImportError as e:
    print(f"⚠️  Missing dependencies for Cross-Modal Auditor: {e}")
    print("Please install required packages: pip install torch torchvision transformers pillow nltk")


# Configure logging for the cross-modal auditor
logger = logging.getLogger('mirror_test.cross_modal_auditor')
logger.setLevel(logging.INFO)

# Create file handler for cross-modal audit events
audit_handler = logging.FileHandler('cross_modal_audit_events.log')
audit_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
audit_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(audit_handler)


@dataclass
class AuditResult:
    """Result of cross-modal synchronization audit."""
    sync_score: float
    hallucination_detected: bool
    severity: str
    detected_keywords: List[str]
    missing_keywords: List[str]
    image_features: Optional[np.ndarray] = None
    text_features: Optional[np.ndarray] = None
    timestamp: datetime = None


class CrossModalAuditor:
    """Audits image-text alignment using CLIP model and NLP parsing."""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize the Cross-Modal Auditor.
        
        Args:
            model_name: CLIP model to use for image-text matching.
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self._initialized = False
        
        # Initialize NLTK resources
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            print(f"⚠️  Warning: Could not download NLTK resources: {e}")
        
        self.stop_words = set(stopwords.words('english'))
        
    def _initialize_model(self) -> bool:
        """Initialize the CLIP model and processor."""
        if self._initialized:
            return True
            
        try:
            print(f"🔍 Loading CLIP model: {self.model_name}")
            print(f"📍 Device: {self.device}")
            
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            
            self.model.to(self.device)
            self.model.eval()
            
            self._initialized = True
            print("✅ CLIP model loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load CLIP model: {e}")
            logger.error(f"Model initialization failed: {e}")
            return False
    
    def _extract_keywords(self, prompt: str) -> Dict[str, List[str]]:
        """
        Extract key nouns and adjectives from prompt using NLP.
        
        Args:
            prompt: Text prompt to analyze.
            
        Returns:
            Dictionary with 'nouns' and 'adjectives' keys.
        """
        try:
            # Tokenize and tag parts of speech
            tokens = word_tokenize(prompt.lower())
            pos_tags = pos_tag(tokens)
            
            # Extract nouns and adjectives, filtering out stop words
            nouns = []
            adjectives = []
            
            for word, pos in pos_tags:
                # Skip stop words and very short words
                if word in self.stop_words or len(word) < 3:
                    continue
                
                # Nouns: NN, NNS, NNP, NNPS
                if pos.startswith('NN'):
                    nouns.append(word)
                # Adjectives: JJ, JJR, JJS
                elif pos.startswith('JJ'):
                    adjectives.append(word)
            
            return {
                'nouns': list(set(nouns)),  # Remove duplicates
                'adjectives': list(set(adjectives))
            }
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to extract keywords: {e}")
            logger.warning(f"Keyword extraction failed: {e}")
            return {'nouns': [], 'adjectives': []}
    
    def _preprocess_image(self, image_path: str) -> Optional[torch.Tensor]:
        """
        Preprocess image for CLIP model.
        
        Args:
            image_path: Path to image file.
            
        Returns:
            Preprocessed image tensor or None if failed.
        """
        try:
            # Load and validate image
            image = Image.open(image_path).convert("RGB")
            
            # Preprocess with CLIP processor
            inputs = self.processor(images=image, return_tensors="pt")
            return inputs['pixel_values'].to(self.device)
            
        except Exception as e:
            print(f"❌ Failed to process image {image_path}: {e}")
            logger.error(f"Image preprocessing failed: {e}")
            return None
    
    def _calculate_similarity(self, image_features: torch.Tensor, 
                            text_features: torch.Tensor) -> float:
        """
        Calculate cosine similarity between image and text features.
        
        Args:
            image_features: Image feature tensor.
            text_features: Text feature tensor.
            
        Returns:
            Similarity score between 0 and 100.
        """
        # Normalize features
        image_features = F.normalize(image_features, dim=-1)
        text_features = F.normalize(text_features, dim=-1)
        
        # Calculate cosine similarity
        similarity = torch.cosine_similarity(image_features, text_features, dim=-1)
        
        # Convert to percentage
        return float(similarity.item() * 100)
    
    def _generate_test_prompts(self, keywords: Dict[str, List[str]]) -> List[str]:
        """
        Generate test prompts from extracted keywords.
        
        Args:
            keywords: Dictionary with 'nouns' and 'adjectives'.
            
        Returns:
            List of test prompts.
        """
        test_prompts = []
        
        # Base prompt with all nouns
        if keywords['nouns']:
            base_prompt = f"A photo of {', '.join(keywords['nouns'])}"
            test_prompts.append(base_prompt)
        
        # Prompts with adjectives
        if keywords['adjectives'] and keywords['nouns']:
            adj_prompt = f"A {', '.join(keywords['adjectives'])} photo of {', '.join(keywords['nouns'])}"
            test_prompts.append(adj_prompt)
        
        # Individual noun prompts
        for noun in keywords['nouns']:
            test_prompts.append(f"A photo of {noun}")
        
        # Individual adjective prompts (contextual)
        for adj in keywords['adjectives']:
            test_prompts.append(f"A {adj} scene")
        
        return test_prompts
    
    def audit_multimodal_sync(self, image_path: str, prompt: str, 
                            threshold: float = 65.0) -> AuditResult:
        """
        Audit image-text synchronization using CLIP model.
        
        Args:
            image_path: Path to the image file.
            prompt: Text prompt describing the image.
            threshold: Sync score threshold for hallucination detection.
            
        Returns:
            AuditResult containing sync score and hallucination status.
        """
        # Initialize model if not already done
        if not self._initialized:
            if not self._initialize_model():
                return AuditResult(
                    sync_score=0.0,
                    hallucination_detected=True,
                    severity="HIGH",
                    detected_keywords=[],
                    missing_keywords=[],
                    timestamp=datetime.now()
                )
        
        print(f"🔍 Starting multimodal audit for: {image_path}")
        print(f"📝 Prompt: {prompt}")
        
        # Extract keywords from prompt
        keywords = self._extract_keywords(prompt)
        print(f"🔑 Extracted keywords - Nouns: {keywords['nouns']}, Adjectives: {keywords['adjectives']}")
        
        # Preprocess image
        image_tensor = self._preprocess_image(image_path)
        if image_tensor is None:
            return AuditResult(
                sync_score=0.0,
                hallucination_detected=True,
                severity="HIGH",
                detected_keywords=[],
                missing_keywords=keywords['nouns'] + keywords['adjectives'],
                timestamp=datetime.now()
            )
        
        # Generate test prompts
        test_prompts = self._generate_test_prompts(keywords)
        print(f"🧪 Generated {len(test_prompts)} test prompts")
        
        # Process image features once
        with torch.no_grad():
            image_features = self.model.get_image_features(image_tensor)
        
        # Calculate similarities for all test prompts
        similarities = []
        text_features_list = []
        
        for test_prompt in test_prompts:
            try:
                # Process text
                text_inputs = self.processor(text=test_prompt, return_tensors="pt", padding=True)
                text_inputs = {k: v.to(self.device) for k, v in text_inputs.items()}
                
                # Get text features
                text_features = self.model.get_text_features(**text_inputs)
                text_features_list.append(text_features.cpu().numpy())
                
                # Calculate similarity
                similarity = self._calculate_similarity(image_features, text_features)
                similarities.append(similarity)
                
                print(f"   Prompt: '{test_prompt}' -> Score: {similarity:.1f}%")
                
            except Exception as e:
                print(f"⚠️  Failed to process prompt '{test_prompt}': {e}")
                similarities.append(0.0)
                text_features_list.append(np.zeros((1, 512)))  # Placeholder
        
        # Calculate overall sync score (average of top 3 scores)
        if similarities:
            top_similarities = sorted(similarities, reverse=True)[:3]
            sync_score = np.mean(top_similarities)
        else:
            sync_score = 0.0
        
        # Determine hallucination status
        hallucination_detected = sync_score < threshold
        severity = "HIGH" if hallucination_detected else "LOW"
        
        # Log the result
        if hallucination_detected:
            message = f"[MULTIMODAL HALLUCINATION DETECTED] Image: {image_path}, Prompt: '{prompt}', Sync Score: {sync_score:.1f}%"
            logger.warning(message)
            print(f"🚨 {message}")
        else:
            message = f"[MULTIMODAL SYNC VERIFIED] Image: {image_path}, Prompt: '{prompt}', Sync Score: {sync_score:.1f}%"
            logger.info(message)
            print(f"✅ {message}")
        
        # Calculate average text features for return
        avg_text_features = np.mean(text_features_list, axis=0) if text_features_list else None
        
        return AuditResult(
            sync_score=round(sync_score, 2),
            hallucination_detected=hallucination_detected,
            severity=severity,
            detected_keywords=keywords['nouns'] + keywords['adjectives'],
            missing_keywords=[],
            image_features=image_features.cpu().numpy(),
            text_features=avg_text_features,
            timestamp=datetime.now()
        )


def audit_multimodal_sync(image_path: str, prompt: str, threshold: float = 65.0) -> Dict[str, Any]:
    """
    Main function to audit image-text synchronization.
    
    Args:
        image_path: Path to the image file.
        prompt: Text prompt describing the image.
        threshold: Sync score threshold for hallucination detection (default: 65%).
        
    Returns:
        Dictionary containing audit results.
    """
    auditor = CrossModalAuditor()
    result = auditor.audit_multimodal_sync(image_path, prompt, threshold)
    
    # Convert result to dictionary for return
    return {
        'sync_score': result.sync_score,
        'hallucination_detected': result.hallucination_detected,
        'severity': result.severity,
        'detected_keywords': result.detected_keywords,
        'missing_keywords': result.missing_keywords,
        'timestamp': result.timestamp.isoformat(),
        'status': 'MULTIMODAL HALLUCINATION DETECTED' if result.hallucination_detected else 'SYNC VERIFIED'
    }


# Export the main function for use as a tool
__all__ = ['audit_multimodal_sync', 'CrossModalAuditor', 'AuditResult']