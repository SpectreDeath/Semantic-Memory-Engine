#!/usr/bin/env python3
"""
Check SQLite database structure
"""

import sqlite3

def check_database():
    """Check the structure of the knowledge_core.sqlite database."""
    try:
        conn = sqlite3.connect('data/knowledge_core.sqlite')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if concepts table exists and get its structure
        cursor.execute("PRAGMA table_info(concepts)")
        columns = cursor.fetchall()
        if columns:
            print("\nConcepts table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("\nNo 'concepts' table found")
        
        # Check if assertions table exists and get its structure
        cursor.execute("PRAGMA table_info(assertions)")
        columns = cursor.fetchall()
        if columns:
            print("\nAssertions table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("\nNo 'assertions' table found")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database()