"""
Unit Tests for Forensic Media & Steganography Plugin
===================================================
Tests ForensicMediaPlugin EXIF extraction, LSB steganography, and ELA analysis.
"""

from __future__ import annotations

import pytest

from extensions.ext_forensic_media.plugin import ForensicMediaPlugin


class TestForensicMediaPlugin:
    """Test ForensicMediaPlugin analysis features."""

    def test_analyze_media_forensics_all_checks(self):
        plugin = ForensicMediaPlugin()
        res = plugin.analyze_media_forensics(
            file_path="sample_evidence.jpg",
            checks=["exif", "steganography", "ela"],
        )

        assert res["status"] == "success"
        assert "exif" in res
        assert "steganography" in res
        assert "ela" in res
        assert res["exif"]["Make"] == "CameraCorp"
        assert res["steganography"]["lsb_anomaly_detected"] is False

    def test_analyze_media_forensics_partial_checks(self):
        plugin = ForensicMediaPlugin()
        res = plugin.analyze_media_forensics(
            file_path="evidence.png",
            checks=["exif"],
        )

        assert res["status"] == "success"
        assert "exif" in res
        assert "steganography" not in res
