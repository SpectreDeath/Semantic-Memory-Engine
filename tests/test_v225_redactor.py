import pytest
from src.core.redactor import Redactor
from src.analysis.federation_gate import FederationGate

def test_basic_redaction():
    text = "Contact John Smith at john.smith@example.com or visit https://sme-forensics.com"
    redacted = Redactor.redact(text)
    assert "[REDACTED]" in redacted
    assert "John Smith" not in redacted
    assert "john.smith@example.com" not in redacted
    assert "https://sme-forensics.com" not in redacted

def test_expanded_patterns():
    text = "Call 555-0199 or check IP 192.168.1.1"
    redacted = Redactor.redact(text)
    assert "[REDACTED]" in redacted
    assert "555-0199" not in redacted
    assert "192.168.1.1" not in redacted

def test_strict_mode_ids():
    text = "My SSN is 123-45-6789 and my passport is AB1234567"
    redacted = Redactor.redact(text, strict=True)
    assert redacted.count("[REDACTED]") >= 2
    assert "123-45-6789" not in redacted
    assert "AB1234567" not in redacted

def test_technical_preservation():
    # In strict mode, "Python Version" might look like a name
    text = "The Python Version is high. John Smith is here."
    redacted = Redactor.redact(text, strict=True)
    assert "Python Version" in redacted
    assert "John Smith" not in redacted
    assert "[REDACTED]" in redacted

def test_federation_gate():
    text = "Private info about Jane Doe: 555-1212"
    hardened = FederationGate.prepare_for_federation(text)
    assert "Jane Doe" not in hardened
    assert "555-1212" not in hardened
    assert "[REDACTED]" in hardened

def test_empty_handling():
    assert Redactor.redact("") == ""
    assert FederationGate.prepare_for_federation(None) == ""
