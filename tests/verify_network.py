import sys
import socket

# Add path for imports
sys.path.append("D:/mcp_servers")

def test_network_probe():
    print("--- Testing Network Probe Logic ---")
    from network_probe import check_latency, verify_connectivity, get_network_summary
    
    # 1. Test Latency
    print("Testing Latency (Google DNS)...")
    latency_result = check_latency("8.8.8.8")
    print(f"Result: {latency_result}")
    
    # 2. Test Connectivity
    print("\nTesting Connectivity (HEAD requests)...")
    connectivity_result = verify_connectivity(["https://www.google.com"])
    print(f"Result:\n{connectivity_result}")
    
    # 3. Test Summary
    print("\nTesting Network Summary...")
    summary = get_network_summary()
    print(f"Result:\n{summary}")

if __name__ == "__main__":
    test_network_probe()
