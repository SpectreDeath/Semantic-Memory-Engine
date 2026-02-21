import os
import json
import logging
import asyncio
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
import base64

# Try to import visualization libraries with fallbacks
try:
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("[Atlas] scikit-learn not available, T-SNE functionality will be limited")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("[Atlas] plotly not available, interactive visualization will be limited")

# NexusAPI: use self.nexus.nexus and self.nexus.get_hsm() — no gateway imports
from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Atlas")

@dataclass
class FingerprintRecord:
    """Represents a fingerprint record from the forensic ledger."""
    sample_id: str
    model_fingerprint: str
    combined_anomaly_score: float
    timestamp: datetime
    source_plugin: str
    is_recurring: bool
    recurring_with: Optional[str]
    metadata: Dict[str, Any]

class Atlas(BasePlugin):
    """
    Atlas v1.0
    Forensic Visualizer that creates interactive 2D maps of fingerprint data using T-SNE.
    Color-codes points by source_plugin and highlights recurring samples.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        
        # Configuration
        self.tsne_perplexity = 30
        self.tsne_early_exaggeration = 12
        self.tsne_learning_rate = 200
        self.tsne_n_iter = 1000
        
        # Color mapping for source plugins
        self.plugin_colors = {
            'SDA': '#FF6B6B',      # Red
            'APB': '#4ECDC4',      # Teal
            'LTA': '#45B7D1',      # Blue
            'LogicAuditor': '#45B7D1',  # Blue (alias for LTA)
            'Manual': '#F7DC6F',   # Yellow
            'Unknown': '#95A5A6'   # Gray
        }
        
        # Ensure reports directory exists
        self.reports_dir = os.path.join("D:", "SME", "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        
        logger.info(f"[{self.plugin_id}] Atlas initialized with T-SNE visualization capabilities")

    async def on_startup(self):
        """
        Initialize the Atlas.
        """
        try:
            logger.info(f"[{self.plugin_id}] Atlas started successfully")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to start Atlas: {e}")

    async def on_shutdown(self):
        """
        Clean shutdown of the Atlas.
        """
        try:
            logger.info(f"[{self.plugin_id}] Atlas shutdown complete")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error during shutdown: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Atlas does not process on_ingestion directly.
        It provides visualization tools for forensic analysis.
        """
        return {
            "status": "skipped",
            "reason": "Atlas provides visualization tools, not direct ingestion processing"
        }

    def get_tools(self) -> list:
        return [
            self.generate_forensic_atlas,
            self.get_atlas_statistics,
            self.export_atlas_data,
            self.create_atlas_summary
        ]

    async def generate_forensic_atlas(self, output_path: str = None, include_recurring_only: bool = False) -> str:
        """
        Generate the Forensic Atlas using T-SNE visualization.
        
        Fetches all records from nexus_forensic_ledger, creates a 2D map using T-SNE,
        color-codes points by source_plugin, and highlights recurring samples.
        """
        try:
            if not SKLEARN_AVAILABLE:
                return json.dumps({
                    "error": "scikit-learn not available. Install with: pip install scikit-learn"
                })
            
            if not PLOTLY_AVAILABLE:
                return json.dumps({
                    "error": "plotly not available. Install with: pip install plotly"
                })
            
            # Fetch data from forensic ledger
            records = await self._fetch_forensic_data(include_recurring_only)
            
            if not records:
                return json.dumps({
                    "error": "No data found in nexus_forensic_ledger"
                })
            
            # Prepare data for T-SNE
            fingerprints, labels, anomaly_scores, is_recurring, sample_ids = self._prepare_data_for_tsne(records)
            
            # Generate T-SNE embedding
            tsne_result = self._perform_tsne(fingerprints)
            
            # Create visualization
            output_file = output_path or os.path.join(self.reports_dir, "current_atlas.html")
            html_content = self._create_interactive_visualization(
                tsne_result, labels, anomaly_scores, is_recurring, sample_ids, output_file
            )
            
            # Save the HTML report
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate statistics
            stats = self._generate_atlas_statistics(records, tsne_result)
            
            result = {
                "status": "success",
                "output_file": output_file,
                "total_samples": len(records),
                "visualization_type": "T-SNE 2D Map",
                "color_coding": "source_plugin",
                "recurring_highlighted": True,
                "statistics": stats
            }
            
            logger.info(f"[{self.plugin_id}] Forensic Atlas generated: {output_file}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error generating forensic atlas: {e}")
            return json.dumps({
                "error": f"Failed to generate forensic atlas: {str(e)}"
            })

    async def get_atlas_statistics(self) -> str:
        """Get statistics about the forensic atlas data."""
        try:
            records = await self._fetch_forensic_data()
            
            if not records:
                return json.dumps({"error": "No data found in nexus_forensic_ledger"})
            
            stats = self._generate_atlas_statistics(records)
            return json.dumps(stats, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error getting atlas statistics: {e}")
            return json.dumps({"error": f"Failed to get atlas statistics: {str(e)}"})

    async def export_atlas_data(self, format: str = "csv") -> str:
        """Export atlas data to various formats."""
        try:
            records = await self._fetch_forensic_data()
            
            if not records:
                return json.dumps({"error": "No data found in nexus_forensic_ledger"})
            
            if format.lower() == "csv":
                output_file = os.path.join(self.reports_dir, "atlas_data.csv")
                self._export_to_csv(records, output_file)
            elif format.lower() == "json":
                output_file = os.path.join(self.reports_dir, "atlas_data.json")
                self._export_to_json(records, output_file)
            else:
                return json.dumps({"error": f"Unsupported format: {format}"})
            
            return json.dumps({
                "status": "success",
                "output_file": output_file,
                "format": format.upper(),
                "records_exported": len(records)
            })
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error exporting atlas data: {e}")
            return json.dumps({"error": f"Failed to export atlas data: {str(e)}"})

    async def create_atlas_summary(self) -> str:
        """Create a summary report of the forensic atlas."""
        try:
            records = await self._fetch_forensic_data()
            
            if not records:
                return json.dumps({"error": "No data found in nexus_forensic_ledger"})
            
            summary = self._create_atlas_summary_report(records)
            return json.dumps(summary, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error creating atlas summary: {e}")
            return json.dumps({"error": f"Failed to create atlas summary: {str(e)}"})

    async def _fetch_forensic_data(self, include_recurring_only: bool = False) -> List[FingerprintRecord]:
        """Fetch data from the forensic ledger."""
        try:
            sql = """
                SELECT sample_id, model_fingerprint, combined_anomaly_score, 
                       timestamp, source_plugin, metadata, is_recurring, recurring_with
                FROM nexus_forensic_ledger
            """
            
            if include_recurring_only:
                sql += " WHERE is_recurring = 1"
            
            sql += " ORDER BY timestamp DESC"
            
            rows = self.nexus.nexus.execute(sql).fetchall()
            
            records = []
            for row in rows:
                metadata = json.loads(row[5]) if row[5] else {}
                records.append(FingerprintRecord(
                    sample_id=row[0],
                    model_fingerprint=row[1],
                    combined_anomaly_score=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    source_plugin=row[4],
                    is_recurring=bool(row[6]),
                    recurring_with=row[7],
                    metadata=metadata
                ))
            
            logger.debug(f"[{self.plugin_id}] Fetched {len(records)} records from forensic ledger")
            return records
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error fetching forensic data: {e}")
            return []

    def _prepare_data_for_tsne(self, records: List[FingerprintRecord]) -> Tuple[np.ndarray, List[str], List[float], List[bool], List[str]]:
        """Prepare fingerprint data for T-SNE analysis."""
        try:
            # Convert fingerprints to numerical vectors
            fingerprint_vectors = []
            labels = []
            anomaly_scores = []
            is_recurring = []
            sample_ids = []
            
            for record in records:
                # Convert fingerprint string to character frequency vector
                vector = self._fingerprint_to_vector(record.model_fingerprint)
                fingerprint_vectors.append(vector)
                
                labels.append(record.source_plugin)
                anomaly_scores.append(record.combined_anomaly_score)
                is_recurring.append(record.is_recurring)
                sample_ids.append(record.sample_id)
            
            # Convert to numpy array
            fingerprint_matrix = np.array(fingerprint_vectors)
            
            # Standardize the features
            scaler = StandardScaler()
            fingerprint_matrix_scaled = scaler.fit_transform(fingerprint_matrix)
            
            logger.debug(f"[{self.plugin_id}] Prepared {len(records)} fingerprint vectors for T-SNE")
            return fingerprint_matrix_scaled, labels, anomaly_scores, is_recurring, sample_ids
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error preparing data for T-SNE: {e}")
            raise

    def _fingerprint_to_vector(self, fingerprint: str, vector_size: int = 128) -> List[float]:
        """
        Convert a fingerprint string to a numerical vector.
        
        Uses character frequency and positional encoding.
        """
        try:
            # Character frequency vector
            char_freq = [0] * 256  # ASCII range
            for char in fingerprint:
                char_freq[ord(char)] += 1
            
            # Normalize character frequencies
            char_freq = [freq / len(fingerprint) if len(fingerprint) > 0 else 0 for freq in char_freq]
            
            # Positional encoding (first, middle, last characters)
            pos_encoding = [0] * 3
            if len(fingerprint) > 0:
                pos_encoding[0] = ord(fingerprint[0]) / 255.0  # First char
                pos_encoding[1] = ord(fingerprint[len(fingerprint)//2]) / 255.0  # Middle char
                pos_encoding[2] = ord(fingerprint[-1]) / 255.0  # Last char
            
            # Combine features
            combined_vector = char_freq[:vector_size-3] + pos_encoding
            
            # Pad or truncate to desired size
            if len(combined_vector) < vector_size:
                combined_vector.extend([0] * (vector_size - len(combined_vector)))
            elif len(combined_vector) > vector_size:
                combined_vector = combined_vector[:vector_size]
            
            return combined_vector
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error converting fingerprint to vector: {e}")
            return [0.0] * vector_size

    def _perform_tsne(self, fingerprint_matrix: np.ndarray) -> np.ndarray:
        """Perform T-SNE dimensionality reduction."""
        try:
            # Configure T-SNE
            tsne = TSNE(
                n_components=2,
                perplexity=self.tsne_perplexity,
                early_exaggeration=self.tsne_early_exaggeration,
                learning_rate=self.tsne_learning_rate,
                n_iter=self.tsne_n_iter,
                random_state=42,
                verbose=1
            )
            
            # Fit and transform
            tsne_result = tsne.fit_transform(fingerprint_matrix)
            
            logger.info(f"[{self.plugin_id}] T-SNE completed with {tsne_result.shape[0]} points")
            return tsne_result
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error performing T-SNE: {e}")
            raise

    def _create_interactive_visualization(self, tsne_result: np.ndarray, labels: List[str], 
                                        anomaly_scores: List[float], is_recurring: List[bool], 
                                        sample_ids: List[str], output_file: str) -> str:
        """Create an interactive HTML visualization using Plotly."""
        try:
            # Prepare data for plotting
            x_coords = tsne_result[:, 0]
            y_coords = tsne_result[:, 1]
            
            # Create color mapping
            colors = [self.plugin_colors.get(label, self.plugin_colors['Unknown']) for label in labels]
            
            # Create size mapping (larger for recurring samples)
            sizes = [20 if recurring else 10 for recurring in is_recurring]
            
            # Create hover text
            hover_text = []
            for i, (sample_id, label, score, recurring) in enumerate(zip(sample_ids, labels, anomaly_scores, is_recurring)):
                status = "RECURRING" if recurring else "NORMAL"
                hover_text.append(
                    f"<b>Sample:</b> {sample_id}<br>"
                    f"<b>Plugin:</b> {label}<br>"
                    f"<b>Anomaly Score:</b> {score:.3f}<br>"
                    f"<b>Status:</b> {status}<br>"
                    f"<b>Position:</b> ({x_coords[i]:.3f}, {y_coords[i]:.3f})"
                )
            
            # Create the scatter plot
            fig = go.Figure()
            
            # Add scatter plot
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers',
                marker=dict(
                    color=colors,
                    size=sizes,
                    line=dict(width=1, color='white'),
                    opacity=0.8
                ),
                text=hover_text,
                hoverinfo='text',
                name='Fingerprints'
            ))
            
            # Update layout
            fig.update_layout(
                title={
                    'text': 'Forensic Atlas: T-SNE Visualization of Fingerprint Patterns',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20}
                },
                xaxis_title='T-SNE Dimension 1',
                yaxis_title='T-SNE Dimension 2',
                width=1200,
                height=800,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial, sans-serif", size=12),
                annotations=[
                    dict(
                        text="Recurring samples are highlighted with larger points",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.02, y=0.98,
                        xanchor='left', yanchor='top',
                        font=dict(size=10, color='gray')
                    )
                ]
            )
            
            # Add legend for colors
            unique_labels = list(set(labels))
            for label in unique_labels:
                color = self.plugin_colors.get(label, self.plugin_colors['Unknown'])
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],  # Empty trace for legend
                    mode='markers',
                    marker=dict(color=color, size=10),
                    name=label,
                    showlegend=True
                ))
            
            # Add legend for recurring samples
            fig.add_trace(go.Scatter(
                x=[None], y=[None],  # Empty trace for legend
                mode='markers',
                marker=dict(color='black', size=20, symbol='circle'),
                name='Recurring Samples',
                showlegend=True
            ))
            
            # Save as HTML
            html_content = fig.to_html(include_plotlyjs='cdn', full_html=True)
            
            logger.info(f"[{self.plugin_id}] Interactive visualization created: {output_file}")
            return html_content
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error creating interactive visualization: {e}")
            raise

    def _generate_atlas_statistics(self, records: List[FingerprintRecord], tsne_result: np.ndarray = None) -> Dict[str, Any]:
        """Generate statistics about the atlas data."""
        try:
            # Basic statistics
            total_samples = len(records)
            recurring_samples = sum(1 for r in records if r.is_recurring)
            unique_plugins = list(set(r.source_plugin for r in records))
            
            # Plugin distribution
            plugin_counts = defaultdict(int)
            for record in records:
                plugin_counts[record.source_plugin] += 1
            
            # Anomaly score statistics
            anomaly_scores = [r.combined_anomaly_score for r in records]
            avg_anomaly_score = np.mean(anomaly_scores) if anomaly_scores else 0
            max_anomaly_score = max(anomaly_scores) if anomaly_scores else 0
            min_anomaly_score = min(anomaly_scores) if anomaly_scores else 0
            
            # Time range
            if records:
                time_range = {
                    "earliest": records[-1].timestamp.isoformat(),
                    "latest": records[0].timestamp.isoformat()
                }
            else:
                time_range = {"earliest": None, "latest": None}
            
            stats = {
                "total_samples": total_samples,
                "recurring_samples": recurring_samples,
                "unique_plugins": len(unique_plugins),
                "plugin_distribution": dict(plugin_counts),
                "anomaly_score_stats": {
                    "average": round(avg_anomaly_score, 3),
                    "maximum": round(max_anomaly_score, 3),
                    "minimum": round(min_anomaly_score, 3),
                    "std_dev": round(np.std(anomaly_scores), 3) if anomaly_scores else 0
                },
                "time_range": time_range,
                "plugins": unique_plugins,
                "visualization_ready": True if tsne_result is not None else False
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error generating atlas statistics: {e}")
            return {"error": str(e)}

    def _export_to_csv(self, records: List[FingerprintRecord], output_file: str):
        """Export records to CSV format."""
        try:
            import csv
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['sample_id', 'model_fingerprint', 'combined_anomaly_score', 
                             'timestamp', 'source_plugin', 'is_recurring', 'recurring_with', 'metadata']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in records:
                    writer.writerow({
                        'sample_id': record.sample_id,
                        'model_fingerprint': record.model_fingerprint,
                        'combined_anomaly_score': record.combined_anomaly_score,
                        'timestamp': record.timestamp.isoformat(),
                        'source_plugin': record.source_plugin,
                        'is_recurring': record.is_recurring,
                        'recurring_with': record.recurring_with,
                        'metadata': json.dumps(record.metadata)
                    })
            
            logger.info(f"[{self.plugin_id}] Data exported to CSV: {output_file}")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error exporting to CSV: {e}")
            raise

    def _export_to_json(self, records: List[FingerprintRecord], output_file: str):
        """Export records to JSON format."""
        try:
            data = []
            for record in records:
                data.append({
                    'sample_id': record.sample_id,
                    'model_fingerprint': record.model_fingerprint,
                    'combined_anomaly_score': record.combined_anomaly_score,
                    'timestamp': record.timestamp.isoformat(),
                    'source_plugin': record.source_plugin,
                    'is_recurring': record.is_recurring,
                    'recurring_with': record.recurring_with,
                    'metadata': record.metadata
                })
            
            with open(output_file, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"[{self.plugin_id}] Data exported to JSON: {output_file}")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error exporting to JSON: {e}")
            raise

    def _create_atlas_summary_report(self, records: List[FingerprintRecord]) -> Dict[str, Any]:
        """Create a comprehensive summary report of the atlas."""
        try:
            stats = self._generate_atlas_statistics(records)
            
            # Additional analysis
            recurring_details = []
            for record in records:
                if record.is_recurring:
                    recurring_details.append({
                        'sample_id': record.sample_id,
                        'plugin': record.source_plugin,
                        'anomaly_score': record.combined_anomaly_score,
                        'recurring_with': record.recurring_with
                    })
            
            summary = {
                "report_title": "Forensic Atlas Summary Report",
                "generated_at": datetime.now().isoformat(),
                "data_source": "nexus_forensic_ledger",
                "statistics": stats,
                "recurring_patterns": {
                    "count": len(recurring_details),
                    "details": recurring_details
                },
                "recommendations": [
                    "Monitor recurring patterns for potential adversarial campaigns",
                    "Investigate high-anomaly-score samples from different plugins",
                    "Consider temporal analysis for pattern evolution"
                ],
                "visualization": {
                    "type": "T-SNE 2D Map",
                    "output_file": os.path.join(self.reports_dir, "current_atlas.html"),
                    "features": [
                        "Color-coded by source plugin",
                        "Size-coded for recurring samples",
                        "Interactive hover details",
                        "Exportable format"
                    ]
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error creating atlas summary: {e}")
            return {"error": str(e)}


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return an Atlas instance."""
    return Atlas(manifest, nexus_api)


def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)