"""
SME Forensic Data Processing using Polars

This module provides high-performance data processing for forensic analysis
using Polars as a faster alternative to Pandas.

v2.1.0: Added Polars for accelerated data processing.
"""

import json
import pathlib
from typing import Any, Dict, List

import polars as pl


# ============================================================================
# Forensic Data Schemas
# ============================================================================

# Schema for forensic events
FORENSIC_EVENTS_SCHEMA = {
    "timestamp": pl.Float64,
    "source_ip": pl.Utf8,
    "dest_ip": pl.Utf8,
    "action": pl.Utf8,
    "user": pl.Utf8,
    "risk_score": pl.Float64,
    "synthetic_probability": pl.Float64,
}

# Schema for entity relationships
ENTITY_RELATIONSHIP_SCHEMA = {
    "source": pl.Utf8,
    "target": pl.Utf8,
    "relationship": pl.Utf8,
    "weight": pl.Float64,
    "first_seen": pl.Float64,
    "last_seen": pl.Float64,
}


# ============================================================================
# Core Polars Processing Functions
# ============================================================================

def load_forensic_events(file_path: str) -> pl.DataFrame:
    """
    Load forensic events from CSV or Parquet.
    
    Args:
        file_path: Path to data file
        
    Returns:
        Polars DataFrame with forensic events
    """
    path = pathlib.Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.csv':
        return pl.read_csv(file_path)
    elif suffix == '.parquet':
        return pl.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def detect_anomalies(df: pl.DataFrame, column: str = "risk_score", threshold: float = 0.8) -> pl.DataFrame:
    """
    Detect anomalies in forensic data based on risk score.
    
    Args:
        df: Polars DataFrame
        column: Column to check for anomalies
        threshold: Threshold for anomaly detection
        
    Returns:
        DataFrame containing only anomalous records
    """
    return df.filter(pl.col(column) > threshold)


def calculate_entity_centrality(relationships: pl.DataFrame) -> pl.DataFrame:
    """
    Calculate entity centrality from relationship graph.
    
    Args:
        relationships: DataFrame with source, target, weight columns
        
    Returns:
        DataFrame with entity centrality scores
    """
    # Calculate in-degree centrality
    in_degree = relationships.group_by("target").agg(
        pl.col("weight").sum().alias("in_centrality")
    ).rename({"target": "entity"})
    
    # Calculate out-degree centrality
    out_degree = relationships.group_by("source").agg(
        pl.col("weight").sum().alias("out_centrality")
    ).rename({"source": "entity"})
    
    # Combine and calculate total
    result = in_degree.join(out_degree, on="entity", how="outer").fill_null(0)
    result = result.with_columns(
        (pl.col("in_centrality") + pl.col("out_centrality")).alias("total_centrality")
    ).sort("total_centrality", descending=True)
    
    return result


def detect_synthetic_patterns(df: pl.DataFrame, probability_column: str = "synthetic_probability") -> Dict[str, Any]:
    """
    Detect synthetic patterns in forensic data.
    
    Args:
        df: Polars DataFrame
        probability_column: Column containing synthetic probability scores
        
    Returns:
        Dictionary with synthetic pattern analysis
    """
    total_records = len(df)
    
    # High probability of synthetic content
    high_prob = df.filter(pl.col(probability_column) > 0.8)
    medium_prob = df.filter((pl.col(probability_column) > 0.5) & (pl.col(probability_column) <= 0.8))
    low_prob = df.filter(pl.col(probability_column) <= 0.5)
    
    return {
        "total_records": total_records,
        "high_synthetic_probability": len(high_prob),
        "medium_synthetic_probability": len(medium_prob),
        "low_synthetic_probability": len(low_prob),
        "high_prob_percentage": round(len(high_prob) / total_records * 100, 2) if total_records > 0 else 0,
        "avg_synthetic_probability": df[probability_column].mean(),
    }


def temporal_pattern_analysis(df: pl.DataFrame, timestamp_col: str = "timestamp") -> Dict[str, Any]:
    """
    Analyze temporal patterns in forensic events.
    
    Args:
        df: Polars DataFrame with timestamp column
        timestamp_col: Name of timestamp column
        
    Returns:
        Dictionary with temporal analysis
    """
    # Sort by timestamp
    df_sorted = df.sort(timestamp_col)
    
    # Calculate time deltas between events
    time_deltas = df_sorted.select(
        pl.col(timestamp_col).diff().alias("delta")
    ).drop_nulls()
    
    return {
        "earliest_event": df[timestamp_col].min(),
        "latest_event": df[timestamp_col].max(),
        "event_span_hours": (df[timestamp_col].max() - df[timestamp_col].min()) / 3600,
        "avg_time_between_events": time_deltas["delta"].mean(),
        "min_time_between_events": time_deltas["delta"].min(),
        "max_time_between_events": time_deltas["delta"].max(),
        "total_events": len(df),
    }


def calculate_trust_scores(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculate normalized trust scores for forensic entities.
    
    Args:
        df: DataFrame with risk and synthetic probability columns
        
    Returns:
        DataFrame with added trust_score column
    """
    return df.with_columns(
        # Trust is inverse of risk and synthetic probability
        ((1 - pl.col("risk_score")) * (1 - pl.col("synthetic_probability")) * 100).alias("trust_score")
    )


def group_by_entity_type(df: pl.DataFrame, entity_col: str = "user") -> Dict[str, int]:
    """
    Group forensic events by entity type.
    
    Args:
        df: Polars DataFrame
        entity_col: Column to group by
        
    Returns:
        Dictionary with entity counts
    """
    counts = df.group_by(entity_col).agg(pl.len().alias("count"))
    # Convert to a list of dicts and then to dict
    result = {}
    for row in counts.iter_rows(named=True):
        result[row[entity_col]] = row["count"]
    return result


# ============================================================================
# SME Integration Functions
# ============================================================================

def process_forensic_batch(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a batch of forensic data using Polars.
    
    Args:
        data: List of forensic event dictionaries
        
    Returns:
        Analysis results dictionary
    """
    # Convert to Polars DataFrame
    df = pl.DataFrame(data)
    
    # Run analyses
    anomalies = detect_anomalies(df)
    synthetic_analysis = detect_synthetic_patterns(df)
    trust_scores = calculate_trust_scores(df)
    entity_counts = group_by_entity_type(df)
    
    return {
        "summary": {
            "total_events": len(df),
            "anomalies_detected": len(anomalies),
            "entity_types": len(entity_counts),
        },
        "synthetic_patterns": synthetic_analysis,
        "top_entities": sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "trust_distribution": {
            "high_trust": len(trust_scores.filter(pl.col("trust_score") > 80)),
            "medium_trust": len(trust_scores.filter((pl.col("trust_score") > 50) & (pl.col("trust_score") <= 80))),
            "low_trust": len(trust_scores.filter(pl.col("trust_score") <= 50)),
        }
    }


def export_to_parquet(df: pl.DataFrame, output_path: str) -> str:
    """
    Export Polars DataFrame to Parquet format.
    
    Args:
        df: Polars DataFrame
        output_path: Output file path
        
    Returns:
        Success message
    """
    df.write_parquet(output_path)
    return f"Exported {len(df)} records to {output_path}"


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Create sample forensic data
    sample_data = [
        {"timestamp": 1700000000 + i * 3600, "source_ip": f"192.168.1.{i%255}", 
         "dest_ip": "10.0.0.1", "action": "login", "user": f"user{i%5}", 
         "risk_score": 0.3 + (i % 10) * 0.07, "synthetic_probability": 0.1 + (i % 5) * 0.15}
        for i in range(100)
    ]
    
    result = process_forensic_batch(sample_data)
    print(json.dumps(result, indent=2))
