from mcp.server.fastmcp import FastMCP
import ping3
import requests
import socket
from typing import List, Dict

mcp = FastMCP("NetworkProbe")

@mcp.tool()
def check_latency(host: str = "8.8.8.8") -> str:
    """Measures the round-trip time to a specific host (ms)."""
    try:
        # ping3.ping returns time in seconds, we convert to ms
        latency = ping3.ping(host, unit='ms')
        if latency is None:
            return f"Latency Check: {host} is unreachable."
        return f"Latency to {host}: {latency:.2f} ms"
    except Exception as e:
        return f"Latency Error: {str(e)}"

@mcp.tool()
def verify_connectivity(urls: List[str] = None) -> str:
    """Verifies external service availability via HEAD requests."""
    if urls is None:
        urls = ["https://www.google.com", "https://duckduckgo.com", "https://api.github.com"]
    
    results = []
    for url in urls:
        try:
            response = requests.head(url, timeout=5)
            status = "Online" if response.status_code < 400 else f"Error ({response.status_code})"
            results.append(f"{url}: {status}")
        except requests.exceptions.RequestException as e:
            results.append(f"{url}: Offline ({type(e).__name__})")
            
    return "\n".join(results)

@mcp.tool()
def get_network_summary() -> str:
    """Consolidated report of laboratory network health."""
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "Unknown"
        
    latency = check_latency()
    connectivity = verify_connectivity()
    
    return (
        f"--- NETWORK SUMMARY ---\n"
        f"Hostname: {hostname}\n"
        f"Local IP: {local_ip}\n"
        f"{latency}\n"
        f"\n--- Connectivity ---\n"
        f"{connectivity}"
    )

if __name__ == "__main__":
    mcp.run()
