"""
Data Manager - Centralized NLTK Data & Corpus Management

Provides unified access to NLTK corpora, lexicons, and language resources.
Handles automatic downloading, caching, and availability checks.

Features:
- Auto-discover and download required corpora
- Persistent cache with smart retrieval
- Integration with configuration system
- Health checking for data integrity
- Multi-corpus batch operations

Usage:
    from src.core.data_manager import DataManager
    
    dm = DataManager()
    dm.ensure_required_data()  # Auto-download if missing
    
    # Get corpus
    lemmas = dm.get_wordnet_lemmas("intelligence")
    
    # List available data
    available = dm.list_available_resources()
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import json

try:
    import nltk
    from nltk.downloader import Downloader
    from nltk.corpus import wordnet, stopwords, punkt
except ImportError:
    nltk = None
    Downloader = None

from src.core.config import Config

logger = logging.getLogger(__name__)


@dataclass
class CorpusInfo:
    """Information about a corpus/lexicon."""
    name: str
    identifier: str
    description: str
    size_mb: float
    installed: bool
    required: bool = False


class DataManager:
    """
    Centralized management of NLTK data and linguistic resources.
    
    Handles corpus discovery, installation, and caching for all
    linguistic analysis in SimpleMem.
    """
    
    # Core required resources for SimpleMem functionality
    REQUIRED_RESOURCES = {
        'wordnet': 'WordNet lexical database',
        'punkt': 'Punkt tokenizer',
        'averaged_perceptron_tagger': 'POS tagger',
        'stopwords': 'Common stopwords list',
        'wordnet_ic': 'Information content for WordNet',
        'omw-1.4': 'Open Multilingual Wordnet',
    }
    
    # Optional resources for enhanced functionality
    OPTIONAL_RESOURCES = {
        'verbnet': 'VerbNet lexicon',
        'framenet': 'FrameNet lexicon',
        'propbank': 'PropBank corpus',
        'conll2000': 'CoNLL chunking corpus',
        'brown': 'Brown corpus',
        'universal_tagset': 'Universal POS tagset',
    }
    
    def __init__(self):
        """Initialize DataManager."""
        if nltk is None:
            logger.error("NLTK not available. Install with: pip install nltk")
            self._available = False
            return
        
        self._available = True
        self.config = Config()
        self.downloader = Downloader() if Downloader else None
        self._data_dir = self._get_data_directory()
        self._cache: Dict[str, any] = {}
        self._resource_cache: Dict[str, CorpusInfo] = {}
        
        logger.info(f"DataManager initialized with data directory: {self._data_dir}")
    
    def is_available(self) -> bool:
        """Check if DataManager is available."""
        return self._available
    
    def ensure_required_data(self, verbose: bool = True) -> bool:
        """
        Ensure all required NLTK data is installed.
        
        Downloads and installs required corpora if not present.
        
        Args:
            verbose: Print download progress
        
        Returns:
            True if all required data available, False if issues
        """
        if not self._available:
            logger.error("DataManager not available")
            return False
        
        if verbose:
            logger.info("🔍 Checking required NLTK data...")
        
        all_present = True
        missing = []
        
        for resource_id, description in self.REQUIRED_RESOURCES.items():
            if not self._check_resource(resource_id):
                missing.append(resource_id)
                all_present = False
                if verbose:
                    logger.warning(f"  ❌ Missing: {resource_id} - {description}")
        
        if missing:
            if verbose:
                logger.info(f"📥 Downloading {len(missing)} missing resources...")
            
            for resource_id in missing:
                try:
                    nltk.download(resource_id, quiet=not verbose)
                    if verbose:
                        logger.info(f"  ✅ Downloaded: {resource_id}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to download {resource_id}: {e}")
                    all_present = False
        
        if verbose and all_present:
            logger.info("✅ All required NLTK data is available")
        
        return all_present
    
    def install_optional_resources(self, resources: Optional[List[str]] = None) -> bool:
        """
        Install optional resources for enhanced functionality.
        
        Args:
            resources: Specific resources to install, or None for all
        
        Returns:
            True if all requested resources installed successfully
        """
        if not self._available:
            return False
        
        to_install = resources or list(self.OPTIONAL_RESOURCES.keys())
        success = True
        
        logger.info(f"📥 Installing {len(to_install)} optional resources...")
        
        for resource_id in to_install:
            try:
                nltk.download(resource_id, quiet=True)
                logger.info(f"  ✅ Installed: {resource_id}")
            except Exception as e:
                logger.warning(f"  ⚠️ Could not install {resource_id}: {e}")
                success = False
        
        return success
    
    def get_wordnet_lemmas(self, word: str) -> List[str]:
        """
        Get all lemmas for a word from WordNet.
        
        Args:
            word: The word to look up
        
        Returns:
            List of lemmas
        """
        if not self._available:
            return []
        
        try:
            return [lemma.name() for synset in wordnet.synsets(word) 
                    for lemma in synset.lemmas()]
        except Exception as e:
            logger.error(f"Error getting lemmas for '{word}': {e}")
            return []
    
    def get_stopwords(self, language: str = 'english') -> Set[str]:
        """
        Get stopwords for a language.
        
        Args:
            language: Language code (default: english)
        
        Returns:
            Set of stopwords
        """
        if not self._available:
            return set()
        
        cache_key = f"stopwords_{language}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            stop_set = set(stopwords.words(language))
            self._cache[cache_key] = stop_set
            return stop_set
        except Exception as e:
            logger.error(f"Error getting stopwords for '{language}': {e}")
            return set()
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text using Punkt tokenizer.
        
        Args:
            text: Text to tokenize
        
        Returns:
            List of tokens
        """
        if not self._available:
            return text.split()
        
        try:
            from nltk.tokenize import word_tokenize
            return word_tokenize(text)
        except Exception as e:
            logger.error(f"Error tokenizing text: {e}")
            return text.split()
    
    def sentence_tokenize(self, text: str) -> List[str]:
        """
        Split text into sentences using Punkt.
        
        Args:
            text: Text to split
        
        Returns:
            List of sentences
        """
        if not self._available:
            return text.split('.')
        
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except Exception as e:
            logger.error(f"Error sentence tokenizing: {e}")
            return text.split('.')
    
    def list_available_resources(self) -> Dict[str, List[CorpusInfo]]:
        """
        List all available NLTK resources.
        
        Returns:
            Dictionary with 'required', 'optional', 'other' resource lists
        """
        if not self._available:
            return {}
        
        required_info = [
            CorpusInfo(
                name=desc,
                identifier=res_id,
                description=desc,
                size_mb=0.0,  # Would be fetched from NLTK
                installed=self._check_resource(res_id),
                required=True
            )
            for res_id, desc in self.REQUIRED_RESOURCES.items()
        ]
        
        optional_info = [
            CorpusInfo(
                name=desc,
                identifier=res_id,
                description=desc,
                size_mb=0.0,
                installed=self._check_resource(res_id),
                required=False
            )
            for res_id, desc in self.OPTIONAL_RESOURCES.items()
        ]
        
        return {
            'required': required_info,
            'optional': optional_info,
        }
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all required resources.
        
        Returns:
            Dictionary mapping resource IDs to health status
        """
        if not self._available:
            return {}
        
        health = {}
        for resource_id in self.REQUIRED_RESOURCES.keys():
            health[resource_id] = self._check_resource(resource_id)
        
        return health
    
    def print_status(self):
        """Print status of all resources."""
        if not self._available:
            print("❌ DataManager not available")
            return
        
        print("\n" + "="*70)
        print("📊 NLTK Data Manager Status")
        print("="*70)
        
        print("\n✅ Required Resources:")
        for resource_id, desc in self.REQUIRED_RESOURCES.items():
            status = "✅" if self._check_resource(resource_id) else "❌"
            print(f"  {status} {resource_id:30} - {desc}")
        
        print("\n⭐ Optional Resources:")
        for resource_id, desc in self.OPTIONAL_RESOURCES.items():
            status = "✅" if self._check_resource(resource_id) else "⭐"
            print(f"  {status} {resource_id:30} - {desc}")
        
        print("\n" + "="*70 + "\n")
    
    def clear_cache(self):
        """Clear internal cache."""
        self._cache.clear()
        self._resource_cache.clear()
        logger.info("DataManager cache cleared")
    
    # Private helper methods
    
    def _check_resource(self, resource_id: str) -> bool:
        """Check if a resource is installed."""
        if not self._available:
            return False
        
        try:
            # Try to load the resource
            if resource_id == 'wordnet':
                _ = wordnet.synsets('test')
            elif resource_id == 'stopwords':
                _ = stopwords.words('english')
            elif resource_id == 'punkt':
                from nltk.tokenize import word_tokenize
                _ = word_tokenize('test')
            else:
                # Generic check via downloader
                if self.downloader:
                    return self.downloader.is_installed(resource_id)
            
            return True
        except Exception:
            return False
    
    def _get_data_directory(self) -> Path:
        """Get NLTK data directory."""
        if nltk:
            # Check configured path first
            try:
                data_dir = self.config.get_safe('nltk.data_dir')
                if data_dir:
                    return Path(data_dir)
            except Exception:
                pass
            
            # Fall back to NLTK defaults
            if nltk.data.path:
                return Path(nltk.data.path[0])
        
        # Final fallback
        return Path.home() / 'nltk_data'
