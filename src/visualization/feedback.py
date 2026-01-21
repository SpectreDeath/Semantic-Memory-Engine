from mcp.server.fastmcp import FastMCP
import sqlite3
import os
import matplotlib.pyplot as plt
from datetime import datetime

mcp = FastMCP("BioFeedback")

# Paths
DB_PATH = os.path.normpath("D:/mcp_servers/storage/laboratory.db")
CHARTS_DIR = os.path.normpath("D:/mcp_servers/storage/charts")

@mcp.tool()
def plot_sentiment_history(days: int = 7) -> str:
    """Generates a sentiment trend chart for the specified period."""
    try:
        os.makedirs(CHARTS_DIR, exist_ok=True)
        
        # 1. Fetch data from Centrifuge
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, compound FROM sentiment_logs 
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp ASC
        ''', (f'-{days} days',))
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            return f"No data found to plot for the last {days} days."
            
        # 2. Process data
        timestamps = [datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') for row in data]
        compounds = [row[1] for row in data]
        
        # 3. Create Plot
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, compounds, marker='o', linestyle='-', color='b')
        plt.axhline(0, color='black', linestyle='--', linewidth=0.8)
        plt.title(f"Laboratory Sentiment Trends (Last {days} Days)")
        plt.xlabel("Time")
        plt.ylabel("Compound Score (-1 to 1)")
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 4. Save and return path
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"sentiment_trend_{timestamp_str}.png"
        chart_path = os.path.normpath(os.path.join(CHARTS_DIR, chart_filename))
        plt.savefig(chart_path)
        plt.close()
        
        return f"Chart generated successfully: {chart_path}"
        
    except Exception as e:
        return f"Visualization Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
