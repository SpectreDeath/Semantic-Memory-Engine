"""
🕸️ Layer 0 Harvester - Database Schema Migration

This script initializes the raw_content table in Centrifuge DB to support
the Harvester crawler with proper indices for fast retrieval.

Run once before deploying Harvester to production.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import json

DB_PATH = "d:/mcp_servers/storage/laboratory.db"

def migrate_add_raw_content_table():
    """Create raw_content table for Harvester archival."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create main table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            domain TEXT NOT NULL,
            raw_html TEXT,
            markdown_content TEXT,
            extracted_schema JSON,
            content_type TEXT DEFAULT 'article',
            js_required BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed_by_loom BOOLEAN DEFAULT 0,
            source_quality INTEGER DEFAULT 0,
            fetch_method TEXT,
            error_log TEXT
        )
    """)
    
    print("✅ Created raw_content table")
    
    # Create indices for fast queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_content_domain 
        ON raw_content(domain)
    """)
    print("✅ Created index on domain")
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_content_loom 
        ON raw_content(processed_by_loom)
    """)
    print("✅ Created index on processed_by_loom")
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_content_quality 
        ON raw_content(source_quality)
    """)
    print("✅ Created index on source_quality")
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_raw_content_timestamp 
        ON raw_content(timestamp)
    """)
    print("✅ Created index on timestamp")
    
    conn.commit()
    conn.close()
    print("\n✅ Migration complete: raw_content table ready for Harvester")


def verify_schema():
    """Verify raw_content table schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("PRAGMA table_info(raw_content)")
    columns = cursor.fetchall()
    
    if not columns:
        print("❌ raw_content table not found!")
        return False
    
    print("\n📊 raw_content Table Schema:")
    print("─" * 60)
    for col in columns:
        col_id, name, col_type, notnull, default, pk = col
        print(f"  {name:25} {col_type:15} {'NOT NULL' if notnull else 'NULL':10}")
    
    # Get indices
    cursor.execute("PRAGMA index_list(raw_content)")
    indices = cursor.fetchall()
    
    print("\n📋 Indices:")
    print("─" * 60)
    for idx in indices:
        print(f"  {idx[1]}")
    
    conn.close()
    return True


def get_table_stats():
    """Get current statistics for raw_content table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM raw_content")
    total_rows = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(LENGTH(raw_html)) FROM raw_content")
    total_html_bytes = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(LENGTH(markdown_content)) FROM raw_content")
    total_markdown_bytes = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT AVG(source_quality) FROM raw_content")
    avg_quality = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM raw_content WHERE processed_by_loom = 1")
    processed_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_rows': total_rows,
        'total_html_bytes': total_html_bytes,
        'total_markdown_bytes': total_markdown_bytes,
        'avg_quality': avg_quality,
        'processed_count': processed_count,
        'unprocessed_count': total_rows - processed_count
    }


def cleanup_old_entries(days: int = 30):
    """Remove raw_content entries older than specified days (only unprocessed)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM raw_content 
        WHERE processed_by_loom = 0 
        AND timestamp < datetime('now', '-' || ? || ' days')
    """, (days,))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ Deleted {deleted} unprocessed entries older than {days} days")
    return deleted


def optimize_database():
    """Run VACUUM and ANALYZE for optimal performance."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n🔧 Optimizing database...")
    cursor.execute("VACUUM")
    print("  ✅ VACUUM complete")
    
    cursor.execute("ANALYZE")
    print("  ✅ ANALYZE complete")
    
    conn.close()
    print("✅ Database optimization done")


def add_harvest_batch_table():
    """Add optional table for tracking batch crawl jobs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS harvest_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_name TEXT NOT NULL,
            seed_url TEXT NOT NULL,
            domain TEXT,
            max_depth INTEGER,
            max_pages INTEGER,
            total_crawled INTEGER,
            failed_count INTEGER,
            avg_quality REAL,
            status TEXT DEFAULT 'running',
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            processing_time_seconds REAL
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_harvest_batches_status 
        ON harvest_batches(status)
    """)
    
    conn.commit()
    conn.close()
    print("✅ Created harvest_batches table for batch tracking")


def report_database_status():
    """Generate comprehensive database status report."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get database file size
        db_file = Path(DB_PATH)
        db_size_mb = db_file.stat().st_size / (1024 * 1024)
        
        # Get total tables
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sqlite_master 
            WHERE type='table'
        """)
        table_count = cursor.fetchone()[0]
        
        print("\n" + "=" * 60)
        print("📊 CENTRIFUGE DATABASE STATUS")
        print("=" * 60)
        
        print(f"\n📁 File: {DB_PATH}")
        print(f"   Size: {db_size_mb:.1f} MB")
        print(f"   Tables: {table_count}")
        
        # raw_content table stats
        stats = get_table_stats()
        print(f"\n🕸️ raw_content Table:")
        print(f"   Total records: {stats['total_rows']}")
        print(f"   Processed (by Loom): {stats['processed_count']}")
        print(f"   Pending: {stats['unprocessed_count']}")
        print(f"   HTML storage: {stats['total_html_bytes'] / (1024*1024):.1f} MB")
        print(f"   Markdown storage: {stats['total_markdown_bytes'] / (1024*1024):.1f} MB")
        print(f"   Avg quality score: {stats['avg_quality']:.0f}/100")
        
        # Storage capacity
        capacity_mb = 5000  # 5GB
        used_mb = (stats['total_html_bytes'] + stats['total_markdown_bytes']) / (1024*1024)
        remaining_mb = capacity_mb - used_mb
        usage_pct = (used_mb / capacity_mb) * 100
        
        print(f"\n💾 Storage Capacity:")
        print(f"   Allocated: {capacity_mb:.0f} MB")
        print(f"   Used: {used_mb:.1f} MB ({usage_pct:.1f}%)")
        print(f"   Available: {remaining_mb:.1f} MB")
        
        if remaining_mb < 500:
            print(f"   ⚠️ WARNING: Less than 500MB remaining!")
        else:
            print(f"   ✅ Healthy capacity")
        
        # Engine statistics
        cursor.execute("""
            SELECT fetch_method, COUNT(*) as count, AVG(source_quality) as avg_quality
            FROM raw_content
            GROUP BY fetch_method
            ORDER BY count DESC
        """)
        
        print(f"\n🔧 Engine Usage:")
        for method, count, avg_q in cursor.fetchall():
            print(f"   {method}: {count} ({avg_q:.0f}/100 avg quality)")
        
        # Content type distribution
        cursor.execute("""
            SELECT content_type, COUNT(*) as count
            FROM raw_content
            GROUP BY content_type
        """)
        
        print(f"\n📄 Content Types:")
        for ctype, count in cursor.fetchall():
            print(f"   {ctype}: {count}")
        
        conn.close()
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error generating status report: {e}")


if __name__ == "__main__":
    import sys
    
    print("🕸️ Harvester Layer 0 - Database Migration Tool")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            # Initialize fresh
            migrate_add_raw_content_table()
            verify_schema()
        
        elif command == "verify":
            # Check existing schema
            verify_schema()
        
        elif command == "stats":
            # Show statistics
            report_database_status()
        
        elif command == "cleanup":
            # Clean old entries
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            cleanup_old_entries(days)
            report_database_status()
        
        elif command == "optimize":
            # Optimize database
            optimize_database()
        
        elif command == "status":
            # Full status report
            report_database_status()
        
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python harvester_schema.py init         - Initialize schema")
            print("  python harvester_schema.py verify       - Verify schema")
            print("  python harvester_schema.py stats        - Show statistics")
            print("  python harvester_schema.py cleanup [n]  - Remove entries >n days old")
            print("  python harvester_schema.py optimize     - Vacuum & analyze")
            print("  python harvester_schema.py status       - Full status report")
    
    else:
        # Default: full setup
        print("\n🚀 Running default setup...\n")
        migrate_add_raw_content_table()
        add_harvest_batch_table()
        verify_schema()
        report_database_status()
        print("\n✅ Harvester database ready for production!")
