import gephistreamer
from gephistreamer import graph, Streamer, GephiREST

print(f"Module: {gephistreamer.__file__}")
print(f"Has Node: {hasattr(graph, 'Node')}")
print(f"Has Edge: {hasattr(graph, 'Edge')}")

try:
    # Check if the REST and Streamer objects can actually initialize
    rest = GephiREST('http://localhost:8080', workspace='workspace0')
    s = Streamer(rest)
    print("✅ Gephi Objects initialized successfully.")
except Exception as e:
    print(f"❌ Initialization failed: {e}")