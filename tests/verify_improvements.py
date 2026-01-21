import os
import sys

# Add the directory to path so we can import the logic
sys.path.append("D:/mcp_servers")

def test_file_service():
    print("--- Testing File Service Jail ---")
    from file_service import get_safe_path
    
    # Test valid path
    try:
        path = get_safe_path("test.txt")
        print(f"✅ Valid path: {path}")
    except Exception as e:
        print(f"❌ Valid path failed: {e}")

    # Test nested valid path
    try:
        path = get_safe_path("subfolder/data.md")
        print(f"✅ Nested path: {path}")
    except Exception as e:
        print(f"❌ Nested path failed: {e}")

    # Test invalid path (parent directory escape)
    try:
        path = get_safe_path("../VADER.py")
        print(f"❌ Jailbreak succeeded (FAIL): {path}")
    except PermissionError as e:
        print(f"✅ Jailbreak blocked (PASS): {e}")

    # Test absolute path escape
    try:
        path = get_safe_path("C:/Windows/win.ini")
        print(f"❌ Absolute escape succeeded (FAIL): {path}")
    except PermissionError as e:
        print(f"✅ Absolute escape blocked (PASS): {e}")

def test_web_search():
    print("\n--- Testing Web Search Logic ---")
    from web_search import search_duckduckgo
    
    # Minimal test to see if it runs (might fail without internet, but logic should be sound)
    try:
        result = search_duckduckgo("test query")
        print("✅ Search logic executed.")
        # print(result[:100] + "...")
    except Exception as e:
        print(f"⚠️ Search failed (possibly network): {e}")

if __name__ == "__main__":
    test_file_service()
    test_web_search()
