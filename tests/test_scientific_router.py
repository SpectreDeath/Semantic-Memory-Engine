"""
Unit Tests for Pillar 3: Scientific Domain Workflow Router
===========================================================
Tests ScientificDomainRouter DAG generation, 6D MIMO presets, and execution.
"""

from __future__ import annotations

import pytest

from gateway.scientific_router import ScientificDomainRouter


class TestScientificDomainRouter:
    """Test Scientific Domain Workflow Router."""

    def test_generate_scientific_dag(self):
        router = ScientificDomainRouter()
        dag_plan = router.generate_scientific_dag(
            prompt="Analyze compound aspirin bioactivity and render PDB 3D binding structure",
            target_domain="cheminformatics",
        )

        assert dag_plan["workflow_id"] == "sci_wf_cheminformatics"
        assert dag_plan["target_domain"] == "cheminformatics"
        assert dag_plan["mimo_harness_preset"]["d1_context_max_triplets"] == 30
        assert dag_plan["mimo_harness_preset"]["d2_tool_timeout"] == 90.0
        assert len(dag_plan["tasks_spec"]) == 3

    def test_execute_scientific_workflow(self):
        router = ScientificDomainRouter()
        res = router.execute_scientific_workflow(
            prompt="Analyze protein kinase structure",
            target_domain="bioinformatics",
        )

        assert res["status"] == "success"
        assert res["execution_result"]["status"] == "completed"
        assert len(res["execution_result"]["step_results"]) == 3
