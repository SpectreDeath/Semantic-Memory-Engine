import requests
import json
import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.core.config import Config
from src.core.centrifuge import get_current_db_path

logger = logging.getLogger(__name__)

class AIFdbConnector:
    """
    Connector for fetching and mapping argumentation structures from AIFdb (arg.tech).
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_current_db_path()
        self.aifdb_base_url = "http://www.aifdb.org/json"

    def fetch_nodeset(self, nodeset_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a NodeSet from AIFdb by its ID."""
        url = f"{self.aifdb_base_url}/{nodeset_id}"
        logger.info(f"🌐 Fetching NodeSet {nodeset_id} from {url}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to fetch NodeSet {nodeset_id}: {e}")
            return None

    def map_to_sme(self, aif_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Map AIF data to SME schema (atomic_facts and logical_links).
        Returns a summary of items mapped.
        """
        if not aif_data or 'nodes' not in aif_data:
            return {"facts": 0, "links": 0}

        nodes = aif_data.get('nodes', [])
        edges = aif_data.get('edges', [])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        summary = {"facts": 0, "links": 0, "signals": 0}
        
        try:
            # 1. Map I-nodes (Information) to atomic_facts
            i_nodes = [n for n in nodes if n.get('type') == 'I']
            for node in i_nodes:
                node_id = str(node.get('nodeID'))
                content = node.get('text', '')
                
                cursor.execute("""
                    INSERT OR REPLACE INTO atomic_facts (node_id, content, source_type)
                    VALUES (?, ?, ?)
                """, (node_id, content, 'AIFdb'))
                summary["facts"] += 1

            # 2. Map RA/CA nodes and their edges to logical_links
            # S-nodes (Schemes) can be RA (Inference), CA (Conflict), TA (Transition), etc.
            s_nodes = {str(n.get('nodeID')): n for n in nodes if n.get('type') != 'I'}
            
            for edge in edges:
                # In AIF, connections go Node -> S-Node -> Node
                # We want to represent Node -> Link -> Node
                from_id = str(edge.get('fromID'))
                to_id = str(edge.get('toID'))
                
                # If 'toID' is an S-node, we are entering a link context
                if to_id in s_nodes:
                    s_node = s_nodes[to_id]
                    link_type = s_node.get('type') # RA, CA, etc.
                    scheme = s_node.get('text', '') # e.g. 'Analogy'
                    
                    # Find where this S-node goes next
                    for next_edge in edges:
                        if str(next_edge.get('fromID')) == to_id:
                            target_id = str(next_edge.get('toID'))
                            
                            cursor.execute("""
                                INSERT INTO logical_links (source_node_id, target_node_id, link_type, scheme)
                                VALUES (?, ?, ?, ?)
                            """, (from_id, target_id, link_type, scheme))
                            summary["links"] += 1
                            
                            # RHETORICAL SIGNAL ENRICHMENT
                            if link_type == 'RA' and scheme:
                                self._flag_rhetorical_signal(scheme)
                                summary["signals"] += 1

            conn.commit()
            logger.info(f"✅ Mapped NodeSet: {summary['facts']} facts, {summary['links']} links")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error mapping AIF data: {e}")
        finally:
            conn.close()
            
        return summary

    def _flag_rhetorical_signal(self, scheme: str):
        """Flag specific schemes in the Scribe engine."""
        try:
            from src.core.factory import ToolFactory
            importer = ToolFactory.create_lexicon_importer()
            # We treat schemes as signals with weight 1.0 for enrichment
            importer.import_lexicon_internal_entry(
                word=scheme, 
                signal_type=f"signal_logic_{scheme.lower()}", 
                weight=1.0, 
                source_type="AIFdb_Enrichment"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not flag rhetorical signal: {e}")

    def batch_import(self, nodeset_ids: List[int]) -> Dict[str, int]:
        """Perform batch import of multiple NodeSets."""
        total_summary = {"facts": 0, "links": 0, "signals": 0}
        
        for ns_id in nodeset_ids:
            data = self.fetch_nodeset(ns_id)
            if data:
                summary = self.map_to_sme(data)
                for k in total_summary:
                    total_summary[k] += summary.get(k, 0)
                    
        return total_summary
