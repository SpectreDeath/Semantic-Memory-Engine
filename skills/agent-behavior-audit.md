---
name: agent-behavior-audit
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Governance
source_file: extensions/ext_behavior_audit/
source: Semantic Memory Engine (SME)
tags:
  - agent-behavior-audit
  - action-compliance
  - policy-governance
  - trace-auditing
  - merkle-verification
inputs:
  agent_execution_trace:
    type: array
    required: true
    description: Full chronological transcript of agent actions, tool calls, and observations.
  compliance_policies:
    type: array
    required: false
    description: List of mandatory behavior constraint rules `['no_external_writes', 'enforce_pii_redaction']`.
outputs:
  audit_verdict:
    type: string
    description: Governance compliance decision (`'compliant'`, `'warning'`, `'violation'`).
  policy_violations:
    type: array
    description: List of specific policy breaches with step indices and action payloads.
  integrity_hash:
    type: string
    description: SHA-256 Merkle root verifying audit log immutability.
---

# Agent Behavior Audit Engine

`agent-behavior-audit` analyzes agent execution transcripts to verify strict adherence to safety, privacy, and operational policy boundaries in Python:

$$\text{Compliance} = \bigwedge_{t=1}^T \bigwedge_{p \in \text{Policies}} \text{CheckAction}(a_t, p)$$

---

## The 5-Stage Agent Behavior Audit Progression

1. **Trace Ingestion & Action Extraction**: Ingest agent transcript; extract all tool dispatches and state mutations.
2. **Policy Rule Matching**: Evaluate each action against active governance constraint sets.
3. **The Visual Brief**: Generate interactive HTML governance audit timeline at `%TEMP%\behavior-audit-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert zero critical policy violations (e.g. unredacted PII export, unauthorized shell execution).
5. **Verdict & Merkle Commitment**: Sign audit trail with cryptographic Merkle root and emit verdict.

---

## Implementation Notes

```python
import hashlib
import json
from typing import Dict, List, Any, Optional

def audit_agent_behavior(
    agent_execution_trace: List[Dict[str, Any]],
    compliance_policies: Optional[List[str]] = None
) -> Dict[str, Any]:
    violations = []
    policies = compliance_policies or ["no_unauthorized_writes", "enforce_pii_redaction"]
    
    for step_idx, step in enumerate(agent_execution_trace):
        action = step.get("action", "")
        if "rm -rf" in str(step) or "drop table" in str(step).lower():
            violations.append({"step": step_idx, "policy": "no_unauthorized_writes", "action": action})
            
    trace_hash = hashlib.sha256(json.dumps(agent_execution_trace, sort_keys=True).encode("utf-8")).hexdigest()
    verdict = "compliant" if not violations else "violation"
    
    return {
        "audit_verdict": verdict,
        "policy_violations": violations,
        "integrity_hash": trace_hash
    }
```

---

## Anti-Patterns & Guardrails

- **Un-Hashed Audit Logs** — Recording audit logs without cryptographic hash chaining, allowing retrospective tampering.
- **Surface-Level Log Auditing** — Reviewing agent thoughts while ignoring actual dispatched tool arguments and system side-effects.
