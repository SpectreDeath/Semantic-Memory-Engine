#!/usr/bin/env python3
"""
Data Guard Auditor - Outlier Detection Tool

Uses PyOD's Isolation Forest to detect outliers in numerical data.
Outputs a new CSV with an 'is_outlier' column indicating detected anomalies.
"""

# Standard library imports (PEP 8: stdlib before third-party)
import argparse
import os
import sys

# Third-party imports
import numpy as np
import pandas as pd
from pyod.models.iforest import IForest


class AuditorError(Exception):
    """Raised when the Data Guard Auditor encounters an unrecoverable data error."""


def load_data(file_path: str) -> pd.DataFrame:
    """Load CSV data and validate.

    Args:
        file_path: Path to the input CSV file.

    Returns:
        Loaded DataFrame.

    Raises:
        AuditorError: If the file is missing, empty, or unreadable.
    """
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise AuditorError(f"File '{file_path}' is empty.")
        return df
    except FileNotFoundError as exc:
        raise AuditorError(f"File '{file_path}' not found.") from exc
    except AuditorError:
        raise
    except Exception as exc:
        raise AuditorError(f"Error loading file '{file_path}': {exc}") from exc


def detect_outliers(df: pd.DataFrame, contamination: float = 0.1, random_state: int = 42) -> pd.DataFrame:
    """
    Detect outliers using Isolation Forest.

    Args:
        df: Input DataFrame.
        contamination: Expected proportion of outliers (default 10%).
        random_state: Random seed for reproducibility.

    Returns:
        DataFrame with 'is_outlier' column added.
    """
    # Select only numerical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    if len(numeric_cols) == 0:
        print("Warning: No numerical columns found. Adding is_outlier=False for all rows.")
        df['is_outlier'] = False
        return df

    # Handle missing values by filling with column medians (non-mutating assignment,
    # compatible with pandas >= 2.x and future pandas 3.x deprecations).
    df_numeric = df[numeric_cols].copy()
    for col in numeric_cols:
        if df_numeric[col].isnull().any():
            median_val = df_numeric[col].median()
            df_numeric[col] = df_numeric[col].fillna(median_val)

    # Initialize and fit Isolation Forest
    detector = IForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100,
    )

    # Fit model and predict outliers
    detector.fit(df_numeric.values)
    outlier_labels = detector.predict(df_numeric.values)

    # Convert predictions: PyOD returns 0 (normal) and 1 (outlier) or -1 (outlier) and 1 (normal).
    # Handle both label conventions for cross-version compatibility.
    if set(outlier_labels) == {0, 1}:
        # PyOD newer version: 0 = normal, 1 = outlier
        is_outlier = outlier_labels == 1
    else:
        # PyOD older version: -1 = outlier, 1 = normal
        is_outlier = outlier_labels == -1

    # Attach result column to the original dataframe
    df['is_outlier'] = is_outlier
    return df


def main() -> None:
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Data Guard Auditor - Outlier Detection')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument(
        '--output', '-o',
        default='data/results/audit_results.csv',
        help='Output CSV file path (default: data/results/audit_results.csv)',
    )
    parser.add_argument(
        '--contamination', '-c',
        type=float,
        default=0.1,
        help='Expected proportion of outliers (default: 0.1)',
    )
    parser.add_argument(
        '--random-state', '-r',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)',
    )

    args = parser.parse_args()

    try:
        print(f"Loading data from {args.input_file}...")
        df = load_data(args.input_file)
    except AuditorError as err:
        print(f"Error: {err}")
        sys.exit(1)

    print("Detecting outliers using Isolation Forest...")
    df_with_outliers = detect_outliers(
        df,
        contamination=args.contamination,
        random_state=args.random_state,
    )

    print(f"Saving results to {args.output}...")
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    df_with_outliers.to_csv(args.output, index=False)

    outlier_count = int(df_with_outliers['is_outlier'].sum())
    total_count = len(df_with_outliers)
    outlier_percentage = (outlier_count / total_count) * 100

    print(f"\nAudit Summary:")
    print(f"- Total records: {total_count}")
    print(f"- Outliers detected: {outlier_count} ({outlier_percentage:.2f}%)")
    print(f"- Output saved to: {args.output}")
    print("Audit complete!")


if __name__ == "__main__":
    main()