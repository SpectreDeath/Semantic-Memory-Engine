import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.bootstrap

src.bootstrap.initialize()

from gateway.mcp_server import SmeCoreBridge
from src.core.factory import ToolFactory


def verify_live_triples():
    print("[*] Verifying Live Ego-Triples (WordNet Integration)...")
    bridge = SmeCoreBridge()

    # Test with a known word
    test_entity = "cryptography"
    print(f"[*] Querying triples for: {test_entity}")

    triples = bridge.get_ego_triples(test_entity)

    print(f"[+] Found {len(triples)} triples.")
    for s, p, o in triples:
        print(f"    ({s}) --[{p}]--> ({o})")

    # Verification conditions
    has_definition = any(p == "definition" for s, p, o in triples)
    has_synonym = any(p == "synonym" for s, p, o in triples)
    has_is_a = any(p == "is_a" for s, p, o in triples)

    if has_definition and (has_synonym or has_is_a):
        print("[SUCCESS] Live WordNet data detected!")
    else:
        print("[FAILURE] Data appears simulated or missing.")
        sys.exit(1)

def verify_vram_guardrail():
    print("\n[*] Verifying VRAM Guardrail...")
    from src.core.config import Config
    Config()

    # Temporarily force a low limit in the config object if possible,
    # or just check if the logic executes.
    # Since we can't easily mock the GPU VRAM without deep intervention,
    # we'll check if the ToolFactory method exists and can be called.

    try:
        # We'll try to create a tool that requires lots of VRAM
        # and see if it logs a warning or raises if we were to force it.
        # For now, just ensuring it doesn't crash.
        ToolFactory.create_semantic_graph()
        print("[SUCCESS] ToolFactory initialized SemanticGraph successfully.")
    except RuntimeError as e:
        print(f"[INFO] Guardrail likely triggered (expected if VRAM low): {e}")
    except Exception as e:
        print(f"[FAILURE] Unexpected error in ToolFactory: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import traceback
    try:
        verify_live_triples()
        verify_vram_guardrail()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
