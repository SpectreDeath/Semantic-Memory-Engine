import sqlite3

import pytest

from src.scribe.engine import ScribeEngine


def test_extract_linguistic_fingerprint_counts_core_features(tmp_path):
    engine = ScribeEngine(
        db_path=str(tmp_path / "scribe.sqlite"),
        centrifuge_path=str(tmp_path / "centrifuge.sqlite"),
    )

    fingerprint = engine.extract_linguistic_fingerprint(
        "Alpha beta gamma. Alpha runs quickly, but beta rests.",
        author_id="sample",
    )

    assert fingerprint.author_id == "sample"
    assert fingerprint.text_sample_count == 9
    assert fingerprint.micro_features["word_count"] == 9.0
    assert fingerprint.micro_features["sentence_count"] == 2.0
    assert fingerprint.micro_features["sentence_end_per_1000_words"] == pytest.approx(2000 / 9)
    assert fingerprint.micro_features["comma_to_sentence_end_ratio"] == 0.5
    assert fingerprint.passive_voice_ratio == 0.0
    assert fingerprint.active_voice_ratio > 0.0


def test_extract_micro_features_detects_long_clause_chain(tmp_path):
    engine = ScribeEngine(
        db_path=str(tmp_path / "scribe.sqlite"),
        centrifuge_path=str(tmp_path / "centrifuge.sqlite"),
    )

    text = (
        "The law shall apply broadly, and the agency may enforce duties, "
        "and courts will review claims, and officials must document reasons."
    )
    fingerprint = engine.extract_linguistic_fingerprint(text)

    assert fingerprint.micro_features["word_count"] == 21.0
    assert fingerprint.micro_features["comma_to_sentence_end_ratio"] == 3.0
    assert fingerprint.micro_features["long_chained_construction_per_1000_words"] > 0.0


def test_save_author_profile_uses_temporary_database(tmp_path):
    db_path = tmp_path / "scribe.sqlite"
    engine = ScribeEngine(db_path=str(db_path), centrifuge_path=str(tmp_path / "centrifuge.sqlite"))
    fingerprint = engine.extract_linguistic_fingerprint("Alpha beta gamma.", author_id="profile")

    engine.save_author_profile(fingerprint, "Profile Author")

    assert db_path.exists()
    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM author_profiles").fetchone()[0]
    assert count == 1
