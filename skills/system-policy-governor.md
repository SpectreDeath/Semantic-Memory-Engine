---
name: system-policy-governor
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Governance
source_file: extensions/ext_governor/
source: Semantic Memory Engine (SME)
tags:
  - system-policy-governor
  - policy-enforcement
  - rule-evaluation
  - access-boundaries
  - runtime-governance
inputs:
  proposed_action:
    type: object
    required: true
    description: Action dictionary containing actor, command, target resource, and arguments.
  context_environment:
    type: object
    required: false
    description: Current environmental state (active tenant, security level, system mode).
outputs:
  policy_decision:
    type: string
    description: Governance decision (`'allow'`, `'deny'`, `'require_human_approval'`).
  applied_rules:
    type: array
    description: List of policy rules triggered during evaluation.
  governance_reason:
    type: string
    description: Human-readable explanation justifying the decision.
---

# System Policy Governor Engine

`system-policy-governor` serves as the runtime gateway gatekeeper, evaluating proposed agent actions against corporate security policies in Python:

$$\text{Decision} = \text{EvaluatePolicy}(\text{Action}, \text{ActorRole}, \text{ResourceLevel})$$

---

## The 5-Stage Policy Governor Progression

1. **Action Request Intake**: Ingest proposed action payload and caller credentials.
2. **Policy Rule Tree Traversal**: Evaluate declarative policy rules (RBAC, rate limits, PII boundaries).
3. **The Visual Brief**: Generate interactive HTML policy evaluation decision tree at `%TEMP%\policy-governor-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: If action involves irreversible state mutations, enforce `require_human_approval`.
5. **Verdict Commitment & Output Emission**: Emit governance decision and log audit trail.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def evaluate_system_policy(
    proposed_action: Dict[str, Any],
    context_environment: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    cmd = str(proposed_action.get("command", "")).lower()
    
    if "drop" in cmd or "delete" in cmd:
        return {
            "policy_decision": "require_human_approval",
            "applied_rules": ["destructive_mutation_guard"],
            "governance_reason": "Destructive operations require explicit human confirmation."
        }
        
    return {
        "policy_decision": "allow",
        "applied_rules": ["standard_read_write_policy"],
        "governance_reason": "Action complies with standard security policies."
    }
```

---

## Anti-Patterns & Guardrails

- **Default-Allow Security Posture** — Allowing unrecognized or unhandled actions by default rather than enforcing strict default-deny.
- **Bypassing Policy on Sub-Agent Calls** — Failing to enforce policy rules on delegated secondary sub-agent invocations.
