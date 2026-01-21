#!/usr/bin/env python3
"""
Quick NLP Pipeline Demo
Tests core NLPPipeline functionality without requiring full NLTK data
"""

import sys
import os
# Fix encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from src.core.nlp_pipeline import NLPPipeline, NLPAnalysis
from src import ToolFactory

print("\n" + "="*60)
print("SimpleMem NLP Pipeline - Demo")
print("="*60)

# Test 1: Check if pipeline is available
print("\n[TEST 1] Initializing NLPPipeline...")
nlp = NLPPipeline()
print(f"[OK] Pipeline available: {nlp.is_available()}")

# Test 2: Test with mock data if analysis fails
print("\n[TEST 2] Testing analysis...")
text = "Machine learning enables computers to learn from data."
result = nlp.analyze(text)

if result is None:
    print("[WARN] Full analysis requires NLTK data. Testing partial functionality...")
    # Test lemmatizer
    from nltk.stem import WordNetLemmatizer
    lemmatizer = WordNetLemmatizer()
    print(f"[OK] Lemmatizer works: 'running' -> '{lemmatizer.lemmatize('running')}'")
    print(f"[OK] Lemmatizer works: 'studies' -> '{lemmatizer.lemmatize('studies')}'")
else:
    print(f"[OK] Analysis complete: {len(result.tokens)} tokens")
    print(f"[OK] Sentences: {len(result.sentences)}")
    print(f"[OK] Key terms: {result.key_terms}")
    print(f"[OK] Vocabulary: {len(result.vocabulary)} unique words")

# Test 3: Factory integration
print("\n[TEST 3] Testing ToolFactory integration...")
try:
    nlp_from_factory = ToolFactory.create_nlp_pipeline()
    print(f"[OK] Factory created NLPPipeline: {type(nlp_from_factory).__name__}")
except Exception as e:
    print(f"[FAIL] Factory failed: {e}")

# Test 4: Check module exports
print("\n[TEST 4] Checking module exports...")
from src import NLPPipeline as ExportedNLP
print(f"[OK] NLPPipeline exported from src: {ExportedNLP.__name__}")

# Test 5: Check data manager integration
print("\n[TEST 5] Testing DataManager integration...")
try:
    from src.core.data_manager import DataManager
    dm = DataManager()
    print(f"[OK] DataManager available: {dm.is_available()}")
except Exception as e:
    print(f"[FAIL] DataManager failed: {e}")

# Test 6: Semantic graph integration
print("\n[TEST 6] Testing SemanticGraph integration...")
try:
    from src.core.semantic_graph import SemanticGraph
    sg = SemanticGraph()
    print(f"[OK] SemanticGraph available: {sg.is_available()}")
except Exception as e:
    print(f"[FAIL] SemanticGraph failed: {e}")

print("\n" + "="*60)
print("Demo Complete!")
print("="*60)
print("\nNext Steps:")
print("1. Download NLTK data: python -m nltk.downloader punkt averaged_perceptron_tagger")
print("2. Run tests: pytest tests/test_nlp_pipeline.py -v")
print("3. See docs: docs/NLP_PIPELINE.md")
print()
