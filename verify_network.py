import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_network_generator():
    print("🚀 Starting Network Generator Verification...")
    
    # 1. Check dependencies
    try:
        import networkx as nx
        import pyvis
        print("✅ Dependencies (networkx, pyvis) available")
    except ImportError as e:
        print(f"⚠️ Missing dependency: {e}")
        print("Run: pip install networkx pyvis")
        return
    
    # 2. Instantiate via Factory
    try:
        generator = ToolFactory.create_network_generator()
        print("✅ NetworkGenerator instance created via Factory.")
    except Exception as e:
        print(f"❌ Failed to create instance: {e}")
        sys.exit(1)
        
    # 3. Test Network Generation
    print("\n🕸️ Testing Network Generation...")
    
    html_path = generator.generate_network(
        threshold=1.2,
        max_nodes=20  # Small test network
    )
    
    if html_path and os.path.exists(html_path):
        print(f"✅ Network HTML generated: {html_path}")
        
        # Check file size (should be reasonable)
        file_size = os.path.getsize(html_path) / 1024  # KB
        print(f"   File size: {file_size:.1f} KB")
        
        # Verify it's HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read(500)
            assert "<!doctype html>" in content.lower() or "<html>" in content.lower()
            print("✅ Valid HTML structure")
    else:
        print("❌ Network generation failed")
        sys.exit(1)
    
    print("\n✅ Verification COMPLETE: Network Generator operational.")
    print(f"📍 Open {html_path} in a browser to view the interactive network.")

if __name__ == "__main__":
    test_network_generator()
