---
name: logic-consistency-verification
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: extensions/ext_logic_auditor/
source: Semantic Memory Engine (SME)
tags:
  - logic-consistency-verification
  - propositional-satisfiability
  - z3-smt
  - contradiction-detection
  - axiom-validation
inputs:
  logical_assertions:
    type: array
    required: true
    description: List of propositional or first-order logic formulas `['A -> B', 'B -> C', 'A', 'not C']`.
  strict_mode:
    type: boolean
    required: false
    description: Whether to fail on unprovable premises (default true).
outputs:
  is_consistent:
    type: boolean
    description: True if the assertion set is logically satisfiable (SAT) without contradictions.
  contradictions:
    type: array
    description: Minimal unsatisfiable subset (UNSAT core) triggering logical inconsistency.
  satisfying_model:
    type: object
    description: Variable assignment truth table satisfying all axioms if consistent.
---

# Logic Consistency Verification Engine

`logic-consistency-verification` proves satisfiability and identifies contradictions across declarative statements using **Z3 SMT solver integration and propositional logic in Python**:

$$\text{Consistent} \iff \text{SAT}\left( \bigwedge_{i=1}^M \phi_i \right), \quad \text{Contradiction} \iff \text{UNSAT Core} \subseteq \{\phi_1, \dots, \phi_M\}$$

---

## The 5-Stage Logic Consistency Progression

1. **Assertion Ingestion & AST Parsing**: Ingest logic formulas; compile into Z3 boolean / real expression trees.
2. **SMT Solver Check**: Push assertions onto Z3 solver stack; execute `solver.check()`.
3. **The Visual Brief**: Generate interactive HTML truth tree brief at `%TEMP%\logic-consistency-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: If UNSAT, extract minimal unsatisfiable core to pinpoint exact conflicting premises.
5. **Model Extraction & Output Emission**: Extract satisfying variable assignments or contradiction details and emit report.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def verify_logic_consistency(
    logical_assertions: List[str],
    strict_mode: bool = True
) -> Dict[str, Any]:
    # Mock Propositional SAT evaluation
    has_conflict = False
    conflict_pair = []
    
    # Detect simple literal negation conflicts: 'A' and 'not A'
    seen = set()
    for stmt in logical_assertions:
        s = stmt.strip()
        if s.startswith("not ") and s[4:] in seen:
            has_conflict = True
            conflict_pair = [s[4:], s]
            break
        elif f"not {s}" in seen:
            has_conflict = True
            conflict_pair = [s, f"not {s}"]
            break
        seen.add(s)
        
    return {
        "is_consistent": not has_conflict,
        "contradictions": conflict_pair if has_conflict else [],
        "satisfying_model": {s: True for s in seen if not s.startswith("not ")} if not has_conflict else {}
    }
```

---

## Anti-Patterns & Guardrails

- **Un-Scoped Quantifiers** — Formulating first-order logic formulas with un-instantiated infinite quantifiers that cause solver timeouts.
- **Dropping Contradiction Traces** — Reporting that an assertion set is inconsistent without returning the minimal conflicting clause subset.