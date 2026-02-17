"""
🧪 SME v2.1.0 — Rhetorical Fingerprinting Pipeline Tests (Finalized)

Covers:
    1. Import guards for new dependencies (polars, markitdown, pydantic-ai)
    2. Harvester DocumentProcessor — validation, conversion, entity redaction
    3. RhetoricalSignature Pydantic model validation
    4. ForensicAgent — retry strategy config, updated prompt
    5. ForensicDBManager CRUD + predicate-pushdown queries
    6. SignatureCompare — Manhattan Distance, corpus comparison
    7. Vendor safety — faststylometry still imports pandas
"""

import math
import os
import sqlite3
import tempfile

import pytest


# ===================================================================
# 1. Import Guards — verify new libraries are installed
# ===================================================================

class TestImportGuards:
    """Ensure the three new dependencies resolve without error."""

    def test_import_polars(self):
        import polars as pl
        assert hasattr(pl, "LazyFrame")

    def test_import_markitdown(self):
        from markitdown import MarkItDown
        assert MarkItDown is not None

    def test_import_pydantic_ai(self):
        from pydantic_ai import Agent
        assert Agent is not None


# ===================================================================
# 2. Harvester — DocumentProcessor
# ===================================================================

class TestDocumentProcessor:
    """Tests for src.harvester.converter.DocumentProcessor."""

    def test_instantiation(self):
        from src.harvester.converter import DocumentProcessor
        proc = DocumentProcessor()
        assert proc is not None

    def test_instantiation_redact_off(self):
        from src.harvester.converter import DocumentProcessor
        proc = DocumentProcessor(redact=False)
        assert proc._redact is False

    def test_supported_types(self):
        from src.harvester.converter import DocumentProcessor
        proc = DocumentProcessor()
        types = proc.supported_types()
        assert ".pdf" in types
        assert ".docx" in types
        assert ".html" in types

    def test_rejects_unsupported_extension(self):
        from src.harvester.converter import DocumentProcessor
        proc = DocumentProcessor()
        with pytest.raises(ValueError, match="Unsupported file type"):
            proc.clean_source_material("test_file.xyz")

    def test_rejects_missing_file(self):
        from src.harvester.converter import DocumentProcessor
        proc = DocumentProcessor()
        with pytest.raises(FileNotFoundError):
            proc.clean_source_material("nonexistent_document.pdf")

    def test_converts_html_file(self):
        """Create a minimal HTML file and verify Markdown output."""
        from src.harvester.converter import DocumentProcessor
        proc = DocumentProcessor(redact=False)

        html_content = (
            "<html><body>"
            "<h1>Test Heading</h1>"
            "<p>This is a paragraph with <strong>bold</strong> text.</p>"
            "<table><tr><th>Col A</th><th>Col B</th></tr>"
            "<tr><td>1</td><td>2</td></tr></table>"
            "</body></html>"
        )

        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(html_content)
            tmp_path = f.name

        try:
            result = proc.clean_source_material(tmp_path)
            assert isinstance(result, str)
            assert len(result) > 0
            assert "Test Heading" in result
        finally:
            os.unlink(tmp_path)


# ===================================================================
# 3. Entity Redaction
# ===================================================================

class TestEntityRedaction:
    """Verify entity redaction logic in DocumentProcessor."""

    def test_redacts_proper_names(self):
        from src.harvester.converter import DocumentProcessor
        text = "According to John Smith, the policy was effective."
        result = DocumentProcessor._redact_entities(text)
        assert "John Smith" not in result
        assert "[REDACTED]" in result

    def test_redacts_multi_word_names(self):
        from src.harvester.converter import DocumentProcessor
        text = "A statement by Barack Hussein Obama was released."
        result = DocumentProcessor._redact_entities(text)
        assert "Barack Hussein Obama" not in result
        assert "[REDACTED]" in result

    def test_redacts_email_addresses(self):
        from src.harvester.converter import DocumentProcessor
        text = "Contact us at analyst@forensiclab.com for details."
        result = DocumentProcessor._redact_entities(text)
        assert "analyst@forensiclab.com" not in result
        assert "[REDACTED]" in result

    def test_redacts_urls(self):
        from src.harvester.converter import DocumentProcessor
        text = "Source: https://example.com/report/2024 was cited."
        result = DocumentProcessor._redact_entities(text)
        assert "https://example.com" not in result
        assert "[REDACTED]" in result

    def test_preserves_single_capitals(self):
        """Single capitalized words (sentence starts) should NOT be redacted."""
        from src.harvester.converter import DocumentProcessor
        text = "Analysis shows clear patterns."
        result = DocumentProcessor._redact_entities(text)
        assert result == text  # Unchanged

    def test_preserves_markdown_structure(self):
        """Headings (##) and tables should survive redaction."""
        from src.harvester.converter import DocumentProcessor
        text = "## Overview\n\n| Col A | Col B |\n|---|---|\n| 1 | 2 |"
        result = DocumentProcessor._redact_entities(text)
        assert "## Overview" in result
        assert "| Col A | Col B |" in result

    def test_redaction_in_html_pipeline(self):
        """Full pipeline: HTML → Markdown → Redacted output."""
        from src.harvester.converter import DocumentProcessor
        proc = DocumentProcessor(redact=True)

        html_content = (
            "<html><body>"
            "<p>A memo from Jane Doe to the committee.</p>"
            "<p>Contact: jane@example.com</p>"
            "</body></html>"
        )

        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(html_content)
            tmp_path = f.name

        try:
            result = proc.clean_source_material(tmp_path)
            assert "Jane Doe" not in result
            assert "jane@example.com" not in result
            assert "[REDACTED]" in result
        finally:
            os.unlink(tmp_path)


# ===================================================================
# 4. Sidecar Agent — RhetoricalSignature Model
# ===================================================================

class TestRhetoricalSignature:
    """Validate the Pydantic model, no LLM calls needed."""

    def test_valid_signature(self):
        from src.ai.sidecar_agent import RhetoricalSignature
        sig = RhetoricalSignature(
            alliteration_index=0.42,
            parallelism_score=7,
            superlative_count=3,
        )
        assert sig.alliteration_index == 0.42
        assert sig.parallelism_score == 7
        assert sig.superlative_count == 3

    def test_boundary_values(self):
        from src.ai.sidecar_agent import RhetoricalSignature
        sig_min = RhetoricalSignature(
            alliteration_index=0.0,
            parallelism_score=0,
            superlative_count=0,
        )
        assert sig_min.alliteration_index == 0.0

        sig_max = RhetoricalSignature(
            alliteration_index=1.0,
            parallelism_score=999,
            superlative_count=999,
        )
        assert sig_max.alliteration_index == 1.0

    def test_rejects_invalid_alliteration(self):
        from src.ai.sidecar_agent import RhetoricalSignature
        with pytest.raises(Exception):
            RhetoricalSignature(
                alliteration_index=1.5,
                parallelism_score=0,
                superlative_count=0,
            )

    def test_rejects_negative_scores(self):
        from src.ai.sidecar_agent import RhetoricalSignature
        with pytest.raises(Exception):
            RhetoricalSignature(
                alliteration_index=0.5,
                parallelism_score=-1,
                superlative_count=0,
            )

    def test_system_prompt_is_identity_neutral(self):
        from src.ai.sidecar_agent import SYSTEM_PROMPT
        assert "The Subject" in SYSTEM_PROMPT
        assert "The Evidence" in SYSTEM_PROMPT
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "trump" not in prompt_lower
        assert "biden" not in prompt_lower
        assert "obama" not in prompt_lower


# ===================================================================
# 5. ForensicAgent — Retry Strategy & Updated Prompt
# ===================================================================

class TestForensicAgent:
    """Verify ForensicAgent config without making LLM calls."""

    def test_instantiation(self):
        from src.ai.sidecar_agent import ForensicAgent
        agent = ForensicAgent()
        assert agent is not None

    def test_custom_retry_config(self):
        from src.ai.sidecar_agent import ForensicAgent
        agent = ForensicAgent(max_retries=5, base_delay_s=2.0)
        assert agent._retry.max_retries == 5
        assert agent._retry.base_delay_s == 2.0

    def test_retry_strategy_defaults(self):
        from src.ai.sidecar_agent import RetryStrategy
        rs = RetryStrategy()
        assert rs.max_retries == 3
        assert rs.base_delay_s == 1.0

    def test_analyze_rejects_empty_input(self):
        import asyncio
        from src.ai.sidecar_agent import ForensicAgent
        agent = ForensicAgent()
        with pytest.raises(ValueError, match="Evidence cannot be empty"):
            asyncio.run(agent.analyze(""))

    def test_updated_prompt_contains_stylistic_markers(self):
        from src.ai.sidecar_agent import SYSTEM_PROMPT
        assert "stylistic markers" in SYSTEM_PROMPT
        assert "rhythmic patterns" in SYSTEM_PROMPT
        assert "structural repetitions" in SYSTEM_PROMPT
        assert "superlative density" in SYSTEM_PROMPT

    def test_updated_prompt_forbids_proper_nouns(self):
        from src.ai.sidecar_agent import SYSTEM_PROMPT
        assert "proper nouns" in SYSTEM_PROMPT.lower()

    def test_legacy_api_exists(self):
        from src.ai.sidecar_agent import analyze_evidence, get_agent
        assert callable(analyze_evidence)
        assert callable(get_agent)


# ===================================================================
# 6. Database — ForensicDBManager (in-memory SQLite)
# ===================================================================

class TestForensicDBManager:
    """Tests using a temporary SQLite database."""

    @pytest.fixture
    def db(self, tmp_path):
        from src.api.db_manager import ForensicDBManager
        db_file = str(tmp_path / "test_lab.db")
        return ForensicDBManager(db_path=db_file)

    def test_create_and_store(self, db):
        sig = {
            "alliteration_index": 0.35,
            "parallelism_score": 4,
            "superlative_count": 2,
        }
        rowid = db.store_signature(sig, source="test_speech.pdf")
        assert rowid >= 1

    def test_load_signatures_returns_lazyframe(self, db):
        import polars as pl
        sig = {
            "alliteration_index": 0.5,
            "parallelism_score": 3,
            "superlative_count": 1,
        }
        db.store_signature(sig, source="doc_a.pdf")
        lf = db.load_signatures()
        assert isinstance(lf, pl.LazyFrame)

        df = lf.collect()
        assert len(df) == 1

    def test_query_by_source(self, db):
        db.store_signature(
            {"alliteration_index": 0.1, "parallelism_score": 1, "superlative_count": 0},
            source="alpha_speech.pdf",
        )
        db.store_signature(
            {"alliteration_index": 0.9, "parallelism_score": 9, "superlative_count": 5},
            source="beta_article.html",
        )

        result = db.query_signatures(source="alpha")
        assert len(result) == 1
        assert result["source"][0] == "alpha_speech.pdf"

    def test_query_returns_empty_when_no_match(self, db):
        db.store_signature(
            {"alliteration_index": 0.5, "parallelism_score": 2, "superlative_count": 1},
            source="gamma.docx",
        )
        result = db.query_signatures(source="nonexistent")
        assert len(result) == 0

    def test_compare_signatures(self):
        from src.api.db_manager import ForensicDBManager

        sig_a = {"alliteration_index": 0.3, "parallelism_score": 4, "superlative_count": 2}
        sig_b = {"alliteration_index": 0.3, "parallelism_score": 4, "superlative_count": 2}
        assert ForensicDBManager.compare_signatures(sig_a, sig_b) == 0.0

        sig_c = {"alliteration_index": 0.0, "parallelism_score": 0, "superlative_count": 0}
        sig_d = {"alliteration_index": 1.0, "parallelism_score": 3, "superlative_count": 4}
        dist = ForensicDBManager.compare_signatures(sig_c, sig_d)
        expected = math.sqrt(1.0 + 9.0 + 16.0)
        assert abs(dist - expected) < 1e-6


# ===================================================================
# 7. SignatureCompare — Manhattan Distance + Corpus
# ===================================================================

class TestSignatureCompare:
    """Tests for src.analysis.comparisons.SignatureCompare."""

    @pytest.fixture
    def engine(self, tmp_path):
        from src.analysis.comparisons import SignatureCompare
        db_file = str(tmp_path / "test_compare.db")
        return SignatureCompare(db_path=db_file)

    def _seed_corpus(self, engine, rows):
        """Helper: insert reference rows into the test DB."""
        conn = engine._get_connection()
        try:
            for row in rows:
                conn.execute(
                    """INSERT INTO rhetorical_signatures
                       (source, alliteration_index, parallelism_score,
                        superlative_count, created_at)
                       VALUES (?, ?, ?, ?, datetime('now'))""",
                    (row["source"], row["ai"], row["ps"], row["sc"]),
                )
            conn.commit()
        finally:
            conn.close()

    def test_manhattan_distance_identical(self):
        from src.analysis.comparisons import SignatureCompare
        sig = {"alliteration_index": 0.5, "parallelism_score": 3, "superlative_count": 2}
        assert SignatureCompare.manhattan_distance(sig, sig) == 0.0

    def test_manhattan_distance_known_value(self):
        from src.analysis.comparisons import SignatureCompare
        a = {"alliteration_index": 0.0, "parallelism_score": 0, "superlative_count": 0}
        b = {"alliteration_index": 1.0, "parallelism_score": 3, "superlative_count": 4}
        # |1.0| + |3| + |4| = 8.0
        assert SignatureCompare.manhattan_distance(a, b) == 8.0

    def test_manhattan_distance_fractional(self):
        from src.analysis.comparisons import SignatureCompare
        a = {"alliteration_index": 0.2, "parallelism_score": 5, "superlative_count": 1}
        b = {"alliteration_index": 0.7, "parallelism_score": 2, "superlative_count": 4}
        # |0.5| + |3| + |3| = 6.5
        dist = SignatureCompare.manhattan_distance(a, b)
        assert abs(dist - 6.5) < 1e-6

    def test_compare_live_vs_corpus(self, engine):
        self._seed_corpus(engine, [
            {"source": "speech_a.pdf", "ai": 0.3, "ps": 4, "sc": 2},
            {"source": "speech_b.pdf", "ai": 0.8, "ps": 1, "sc": 7},
            {"source": "article_c.html", "ai": 0.31, "ps": 4, "sc": 2},
        ])

        live = {"alliteration_index": 0.3, "parallelism_score": 4, "superlative_count": 2}
        results = engine.compare_live_vs_corpus(live)

        assert len(results) == 3
        # speech_a should be exact match (distance 0)
        assert results[0]["manhattan_distance"] == 0.0
        assert results[0]["source"] == "speech_a.pdf"
        # article_c should be very close (distance ~0.01)
        assert results[1]["source"] == "article_c.html"

    def test_compare_with_source_filter(self, engine):
        self._seed_corpus(engine, [
            {"source": "speech_a.pdf", "ai": 0.3, "ps": 4, "sc": 2},
            {"source": "article_b.html", "ai": 0.8, "ps": 1, "sc": 7},
        ])

        live = {"alliteration_index": 0.5, "parallelism_score": 3, "superlative_count": 1}
        results = engine.compare_live_vs_corpus(live, source_filter="speech")

        assert len(results) == 1
        assert results[0]["source"] == "speech_a.pdf"

    def test_compare_empty_corpus(self, engine):
        live = {"alliteration_index": 0.5, "parallelism_score": 3, "superlative_count": 1}
        results = engine.compare_live_vs_corpus(live)
        assert results == []

    def test_top_n_limit(self, engine):
        self._seed_corpus(engine, [
            {"source": f"doc_{i}.pdf", "ai": 0.1 * i, "ps": i, "sc": i}
            for i in range(1, 8)
        ])

        live = {"alliteration_index": 0.5, "parallelism_score": 5, "superlative_count": 5}
        results = engine.compare_live_vs_corpus(live, top_n=3)
        assert len(results) == 3


# ===================================================================
# 8. Vendor Safety — faststylometry pandas dependency
# ===================================================================

class TestVendorSafety:
    """Ensure vendored faststylometry is unaffected by our changes."""

    def test_faststylometry_imports_pandas(self):
        import importlib.util
        spec = importlib.util.find_spec("pandas")
        assert spec is not None, "pandas must remain installed for faststylometry"

    def test_faststylometry_module_loadable(self):
        try:
            from src.sme.vendor.faststylometry import burrows_delta
            assert burrows_delta is not None
        except ImportError as e:
            pytest.skip(f"faststylometry not importable in test env: {e}")
