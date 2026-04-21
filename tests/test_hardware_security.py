"""
Tests for gateway/hardware_security.py - HSM/TPM simulation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import os
from unittest.mock import patch

import pytest

from gateway.hardware_security import HardwareSecurity, get_hsm


@pytest.fixture
def hsm_secret():
    with patch.dict(os.environ, {"SME_HSM_SECRET": "test-secret"}):
        yield


def test_sign_evidence_format(hsm_secret):
    hsms = HardwareSecurity()
    sig = hsms.sign_evidence("source1", "abcd1234")
    assert sig.startswith("hws_v1_")
    assert len(sig) == len("hws_v1_") + 16


def test_sign_evidence_deterministic(hsm_secret):
    hsm1 = HardwareSecurity()
    hsm2 = HardwareSecurity()
    sig1 = hsm1.sign_evidence("src", "hash")
    sig2 = hsm2.sign_evidence("src", "hash")
    assert sig1 == sig2


def test_verify_integrity_success(hsm_secret):
    hsm = HardwareSecurity()
    data_hash = "somehash"
    sig = hsm.sign_evidence("src", data_hash)
    assert hsm.verify_integrity("src", data_hash, sig) is True


def test_verify_integrity_failure(hsm_secret):
    hsm = HardwareSecurity()
    assert hsm.verify_integrity("src", "hash", "bad sig") is False
    assert len(hsm.alerts) == 1
    assert hsm.alerts[0]["event"] == "TAMPER_DETECTED"
    assert hsm.status == "ALERT_ACTIVE"


def test_verify_integrity_empty_signature(hsm_secret):
    hsm = HardwareSecurity()
    assert hsm.verify_integrity("src", "hash", "") is False


def test_get_telemetry(hsm_secret):
    hsm = HardwareSecurity()
    # Initially no alerts
    tel = hsm.get_telemetry()
    assert tel["device_id"] == "TPM_2.0_FS_MOCK"
    assert tel["status"] == "HEALTHY"
    assert tel["alert_count"] == 0
    assert tel["last_alerts"] == []
    # Trigger an alert and check telemetry updates
    hsm.trigger_tamper_alert("src")
    tel2 = hsm.get_telemetry()
    assert tel2["alert_count"] == 1
    assert len(tel2["last_alerts"]) == 1


def test_trigger_tamper_alert(hsm_secret):
    hsm = HardwareSecurity()
    hsm.trigger_tamper_alert("sourceX")
    assert len(hsm.alerts) == 1
    alert = hsm.alerts[0]
    assert alert["source"] == "sourceX"
    assert alert["event"] == "TAMPER_DETECTED"
    assert alert["severity"] == "CRITICAL"
    assert hsm.status == "ALERT_ACTIVE"


def test_get_hsm_singleton():
    a = get_hsm()
    b = get_hsm()
    assert a is b
