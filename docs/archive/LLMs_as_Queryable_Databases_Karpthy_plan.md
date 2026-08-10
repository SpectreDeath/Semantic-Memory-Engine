# LLMs as Queryable Databases - Semantic Memory Engine Plan

This plan merges the **Semantic Memory Engine (SME)** architecture with the **"LLM as a Database"** paradigm using a **Karpathy Loop** for each stage: a tight cycle of *Observation -> Theory -> Implementation -> Evaluation* to build from first principles.

---

## Phase 1: The "V-Index" Ingestion Bridge

*Goal: Move from RAG (storing facts in vector DB) to "Physical" facts (mapping to weight-space triples).*

- [x] **Step 1.1: Feature Probing Script**
    - **Task**: Create a script using `nnsight` or `transformer_lens` to probe model weights.
    - **Implementation**: `gateway/feature_prober.py` - probes activations with transformer_lens
    - **Karpathy Goal**: Identify which neurons fire for stylometric fingerprints in your `faststylometry` corpus.
- [x] **Step 1.2: The Triplet-Extractor (The Harvester v2)**
    - **Task**: Modify "The Harvester" to output `(Entity, Relation, Target)` triples instead of raw Markdown.
    - **Implementation**: `gateway/triplet_harvester.py` - extracts triples using spacy NER
    - **Karpathy Goal**: Evaluate the "Semantic Density" of extracted triples vs. raw text.
- [x] **Step 1.3: Mock V-Index Overlay**
    - **Task**: Implement a "Patch Overlay" system that intercepts LLM calls and injects these triples into prompt context via hidden "Actuator" tokens.
    - **Implementation**: `gateway/vindex_overlay.py` - patches LLM calls with triplets

---

## Phase 2: Gephi Topology Visualization

*Goal: Map the "Subconscious" of the model using the SME forensic toolkit.*

- [x] **Step 2.1: Weight-to-GML Exporter**
    - **Task**: Write a utility to export model activations into `.graphml` or `.csv` (Edge List) for Gephi.
    - **Implementation**: `gateway/weight_exporter.py` - exports to GraphML/CSV/GEXF
    - **Karpathy Goal**: Visualize the "Western Nations" cluster. Can you see your "Stylistic DNA" clumped together?
- [x] **Step 2.2: Real-time Activation Streaming**
    - **Task**: Create a WebSocket bridge between the SME Operator and Gephi's "Streaming Plugin."
    - **Implementation**: `gateway/activation_streamer.py` - WebSocket streaming to Gephi
    - **Karpathy Goal**: Watch the graph light up in Gephi as the LLM processes a forensic authorship query.

---

## Phase 3: The "Graph Walk" Navigator

*Goal: Decouple Attention from the Knowledge Store for efficient retrieval.*

- [x] **Step 3.1: KNN Look-up Implementation**
    - **Task**: Implement a k-Nearest Neighbor search on local embeddings to act as an FFN-style knowledge look-up.
    - **Implementation**: `gateway/graph_walk.py` - KNN search with graph walk retrieval
    - **Karpathy Goal**: Compare retrieval latency of dense attention vs. graph walk inference.
- [x] **Step 3.2: Epistemic Trust Validation**
    - **Task**: Integrate SME Trust Scores. If a "Graph Walk" hits a node with low trust (noise), force the model to backtrack.
    - **Implementation**: `gateway/epistemic_trust.py` - trust scoring and hallucination blocking
    - **Karpathy Goal**: Successfully "block" a hallucination by steering away from a low-trust cluster.

---

## Phase 4: The VS Code Forensic IDE

*Goal: Finalize the "Lawnmower Man" interface.*

- [x] **Step 4.1: SME Explorer Integration**
    - **Task**: Add a "Weight Explorer" view to your VS Code extension sidebar.
    - **Implementation**: `extension/extension.js` - Weight Explorer webview + `gateway/vscode_explorer.py`
    - **Karpathy Goal**: Click a word in your editor and see the "Top 5 Activations" in the local model weights.
- [x] **Step 4.2: The "Poseidon" Test (The Insert Pipeline)**
    - **Task**: Implement a "Right-Click to Inject" feature. Select text -> Insert as Physical Fact.
    - **Implementation**: `sme.injectFact` command in extension + Poseidon MCP tool
    - **Karpathy Goal**: Perform the "Atlantis Test." Inject a fake fact and verify the model repeats it with >90% confidence without retraining.

---

### The Karpathy Loop Parameters

For each step above, apply this iterative loop:

1.  **Observation**: Probe the model to see current behavior/activations.
2.  **Theory**: Hypothesize how a V-index patch or Graph Walk would modify that behavior.
3.  **Implementation**: Code the specific logic.
4.  **Evaluation**: Run a forensic trace. Did the "Physical Edge" change? If not, tweak and repeat.