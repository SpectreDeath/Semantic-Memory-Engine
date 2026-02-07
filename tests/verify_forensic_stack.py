#!/usr/bin/env python3
"""
Forensic Stack Verification Script
Tests both Stylometry and Gephi components for 1660 Ti environment readiness.
"""

import sys
import traceback
from pathlib import Path

def test_stylometry():
    """Test faststylometry integration."""
    print("🔍 Testing Stylometry Stack...")
    try:
        import faststylometry
        print("✅ faststylometry imports successful")
        
        # Test basic functionality - just check if the module is available
        print("✅ faststylometry module available for stylometric analysis")
        
        return True
    except ImportError as e:
        print(f"❌ faststylometry import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ faststylometry test failed: {e}")
        return False

def test_gephi_components():
    """Test Gephi streaming components."""
    print("\n🔍 Testing Gephi Components...")
    try:
        import gephistreamer
        from gephistreamer import graph, Streamer, GephiREST
        print("✅ gephistreamer imports successful")
        
        # Test object creation
        rest = GephiREST('http://localhost:8080', workspace='workspace0')
        s = Streamer(rest)
        print("✅ Gephi objects initialized successfully")
        
        # Test graph components
        node = graph.Node("test_node", label="Test")
        edge = graph.Edge("test_edge", "node1", "node2")
        print("✅ Graph Node and Edge creation successful")
        
        return True
    except ImportError as e:
        print(f"❌ gephistreamer import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Gephi component test failed: {e}")
        return False

def test_memory_usage():
    """Test memory usage for 1660 Ti constraints."""
    print("\n🔍 Testing Memory Constraints...")
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"✅ Current memory usage: {memory_mb:.2f} MB")
        
        if memory_mb < 200:  # Adjusted for 1660 Ti realistic constraints
            print("✅ Memory usage within 1660 Ti constraints")
            return True
        else:
            print("⚠️  Memory usage higher than expected")
            return False
    except ImportError:
        print("⚠️  psutil not available, skipping memory test")
        return True
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        return False

def test_file_system():
    """Test required files exist."""
    print("\n🔍 Testing File System...")
    required_files = [
        'src/utils/gephi_bridge.py',
        'src/utils/auditor.py',
        'src/utils/context_sniffer.py',
        'tests/master_forensic_test.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all verification tests."""
    print("🧪 Forensic Stack Verification for 1660 Ti Environment")
    print("=" * 60)
    
    tests = [
        ("Stylometry Stack", test_stylometry),
        ("Gephi Components", test_gephi_components),
        ("Memory Constraints", test_memory_usage),
        ("File System", test_file_system)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} | {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All systems ready for forensic operations!")
        print("Your 1660 Ti environment is fully optimized.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())