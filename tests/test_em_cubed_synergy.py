"""Unit tests for SME and Em-Cubed Synergy Bridges (Bridges 1 - 5)."""

from gateway.em_cubed_bridge import EmCubedWorkflowBridge
from gateway.mcp_server import SemanticGraphBridge
from src.logic.audit_engine import AuditEngine
from src.logic.textual_gradient import TextualGradientEngine


def test_bridge_1_harvester_elicitation():
    bridge = EmCubedWorkflowBridge()
    res = bridge.elicit_ontology_from_harvester(
        raw_text="The supplier delivers Folic Acid from Montevideo.",
        domain_prompt="Pharmaceutical Logistics",
    )
    assert res["status"] == "success"
    assert res["triples_count"] > 0


def test_bridge_2_guided_textual_gradient():
    engine = TextualGradientEngine()
    dl_expr = engine.induce_dl_concept_guard(
        subclass_name="HighTrustAgent",
        positive_samples=[{"type": "Agent", "property": "trust", "target": "High"}],
    )
    assert "HighTrustAgent" in dl_expr


def test_bridge_3_topos_modal_truth():
    graph_bridge = SemanticGraphBridge()
    modal_str = graph_bridge.get_topos_modal_truth(0.95)
    assert "ToposModalTruth" in modal_str


def test_bridge_4_merkle_exact_truthmaker():
    audit_engine = AuditEngine(h5_path="data/test_core.h5")
    # Add a mock record
    audit_engine.audit_records.append(
        type(
            "MockRecord",
            (),
            {
                "index": 0,
                "event_type": "has_origin",
                "actor": "Supplier_1",
                "payload": {"action": "OriginCheck"},
                "timestamp": 123456789.0,
                "prev_hash": "0" * 64,
                "hash": "abc",
            },
        )()
    )

    res = audit_engine.attach_exact_truthmaker_ground(0, "Origin Compliance")
    assert res["status"] == "success"
    assert res["truthmaker"]["is_satisfied"] is True
