#!/usr/bin/env python3
"""
Data Guard Auditor - Outlier Detection Tool

Uses PyOD's Isolation Forest to detect outliers in numerical data.
Outputs a new CSV with an 'is_outlier' column indicating detected anomalies.
"""

import pandas as pd
import numpy as np
from pyod.models.iforest import IForest
import argparse
import sys
import os


def load_data(file_path):
    """Load CSV data and validate."""
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            print(f"Error: File {file_path} is empty.")
            sys.exit(1)
        return df
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)


def detect_outliers(df, contamination=0.1, random_state=42):
    """
    Detect outliers using Isolation Forest.
    
    Args:
        df: Input DataFrame
        contamination: Expected proportion of outliers (default 10%)
        random_state: Random seed for reproducibility
    
    Returns:
        DataFrame with 'is_outlier' column added
    """
    # Select only numerical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        print("Warning: No numerical columns found. Adding is_outlier=False for all rows.")
        df['is_outlier'] = False
        return df
    
    # Handle missing values by filling with median
    df_numeric = df[numeric_cols].copy()
    for col in numeric_cols:
        if df_numeric[col].isnull().any():
            median_val = df_numeric[col].median()
            df_numeric[col].fillna(median_val, inplace=True)
    
    # Initialize and fit Isolation Forest
    detector = IForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100
    )
    
    # Fit model and predict outliers
    detector.fit(df_numeric.values)
    outlier_labels = detector.predict(df_numeric.values)
    
    # Convert predictions: PyOD returns 0 (normal) and 1 (outlier) or -1 (outlier) and 1 (normal)
    # Handle both cases for compatibility
    if set(outlier_labels) == {0, 1}:
        # PyOD newer version: 0 = normal, 1 = outlier
        is_outlier = outlier_labels == 1
    else:
        # PyOD older version: -1 = outlier, 1 = normal
        is_outlier = outlier_labels == -1
    
    # Add outlier column to original dataframe
    df['is_outlier'] = is_outlier
    
    return df


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Data Guard Auditor - Outlier Detection')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('--output', '-o', default='audit_results.csv', 
                       help='Output CSV file path (default: audit_results.csv)')
    parser.add_argument('--contamination', '-c', type=float, default=0.1,
                       help='Expected proportion of outliers (default: 0.1)')
    parser.add_argument('--random-state', '-r', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading data from {args.input_file}...")
    df = load_data(args.input_file)
    
    # Detect outliers
    print("Detecting outliers using Isolation Forest...")
    df_with_outliers = detect_outliers(
        df, 
        contamination=args.contamination, 
        random_state=args.random_state
    )
    
    # Save results
    print(f"Saving results to {args.output}...")
    df_with_outliers.to_csv(args.output, index=False)
    
    # Print summary
    outlier_count = df_with_outliers['is_outlier'].sum()
    total_count = len(df_with_outliers)
    outlier_percentage = (outlier_count / total_count) * 100
    
    print(f"\nAudit Summary:")
    print(f"- Total records: {total_count}")
    print(f"- Outliers detected: {outlier_count} ({outlier_percentage:.2f}%)")
    print(f"- Output saved to: {args.output}")
    print("Audit complete!")


if __name__ == "__main__":
    main()