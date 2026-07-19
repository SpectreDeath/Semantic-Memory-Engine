"""
ScientificDomainRouter - Forensic Science & Multi-Modal Domain Workflow Router
==============================================================================
Maps multi-modal bioinformatics and cheminformatics prompts (ChEMBL, PubChem,
PDB, PyMOL, UniProt) into em-cubed DAG tasks with pre-configured 6D MIMO presets.
"""

from __future__ import annotations

import logging
from typing import Any

from gateway.mimo_bridge import Mimo6DConfig, MimoControlBridge

logger = logging.getLogger("lawnmower.scientific_router")


class ScientificDomainRouter:
    """
    Domain router generating em-cubed multi-step DAG workflows for scientific tasks.
    """

    def __init__(self) -> None:
        self.mimo_bridge = MimoControlBridge()

    def generate_scientific_dag(
        self, prompt: str, target_domain: str = "bioinformatics"
    ) -> dict[str, Any]:
        """
        Decompose natural language scientific prompt into multi-step DAG tasks with 6D presets.
        """
        logger.info(f"ScientificDomainRouter generating DAG for domain '{target_domain}'")

        # 6D Presets for Scientific Workflows (D1 context max, D2 longer timeouts, D6 strict schema)
        mimo_config = Mimo6DConfig(
            d1_context_max_triplets=30,
            d2_tool_timeout=90.0,
            d3_decoding_temperature=0.1,
            d4_routing_mode="em_cubed_workflow",
            d5_persistence_enabled=True,
            d6_enforce_json_schema=True,
        )

        tasks_spec = [
            {
                "task_id": "fetch_compound_metadata",
                "skill_id": "chembl_database",
                "input_data": {"query": prompt, "domain": target_domain},
            },
            {
                "task_id": "fetch_protein_structure",
                "skill_id": "pdb_database",
                "input_data": {"action": "fetch_pdb", "query": prompt},
            },
            {
                "task_id": "render_3d_molecular_binding",
                "skill_id": "pymol",
                "input_data": {"code": "result = 'Rendered 3D binding site'"},
            },
        ]

        return {
            "workflow_id": f"sci_wf_{target_domain}",
            "target_domain": target_domain,
            "mimo_harness_preset": mimo_config.to_dict(),
            "tasks_spec": tasks_spec,
        }

    def execute_scientific_workflow(
        self, prompt: str, target_domain: str = "bioinformatics"
    ) -> dict[str, Any]:
        """
        Generate and execute scientific workflow DAG via EmCubedWorkflowBridge.
        """
        dag_plan = self.generate_scientific_dag(prompt=prompt, target_domain=target_domain)

        from gateway.em_cubed_bridge import EmCubedWorkflowBridge

        bridge = EmCubedWorkflowBridge()
        res = bridge.execute_workflow_dag(
            workflow_id=dag_plan["workflow_id"],
            tasks_spec=dag_plan["tasks_spec"],
        )

        return {
            "status": "success",
            "dag_plan": dag_plan,
            "execution_result": res,
        }
