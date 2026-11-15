---
name: ghost-trap-detection
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Security
source_file: extensions/ext_ghost_trap/
source: Semantic Memory Engine (SME)
tags:
  - ghost-trap-detection
  - honeytoken-monitoring
  - canary-triggers
  - breach-detection
  - tamper-detection
inputs:
  system_logs:
    type: array
    required: true
    description: System event logs or database access queries to scan for canary triggers.
  canary_tokens:
    type: array
    required: false
    description: Known honeytoken strings or canary credentials to monitor.
outputs:
  trap_triggered:
    type: boolean
    description: True if an unauthorized access attempt touched a canary honeytoken.
  triggered_traps:
    type: array
    description: List of triggered honeytoken records with accessing agent/IP and timestamps.
  threat_level:
    type: string
    description: Threat assessment (`'none'`, `'medium'`, `'critical'`).
---

# Ghost Trap Detection Engine

`ghost-trap-detection` plants and monitors decoy honeytokens (canary keys, fake database tables, simulated endpoints) to detect unauthorized intrusion or rogue agent data exfiltration in Python:

$$\text{BreachDetected} \iff \exists e \in \text{AccessLogs} : \text{Target}(e) \in \text{Honeytokens}$$

---

## The 5-Stage Ghost Trap Progression

1. **Log & Canary Ingest**: Ingest system access logs and registered canary honeytoken definitions.
2. **Honeytoken Access Matching**: Scan query traces and memory dumps for references to canary strings.
3. **The Visual Brief**: Generate interactive HTML threat alert card at `%TEMP%\ghost-trap-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: If a honeytoken is accessed, automatically escalate `threat_level` to critical.
5. **Incident Report & Output Emission**: Emit triggered trap array and trigger automated quarantine protocols.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def detect_ghost_traps(
    system_logs: List[Dict[str, Any]],
    canary_tokens: Optional[List[str]] = None
) -> Dict[str, Any]:
    canaries = set(canary_tokens or ["canary_api_key_xyz", "decoy_user_admin", "honey_vault_table"])
    triggered = []
    
    for log in system_logs:
        log_str = str(log)
        for c in canaries:
            if c in log_str:
                triggered.append({"canary": c, "log_entry": log, "severity": "CRITICAL"})
                
    has_trap = len(triggered) > 0
    return {
        "trap_triggered": has_trap,
        "triggered_traps": triggered,
        "threat_level": "critical" if has_trap else "none"
    }
```

---

## Anti-Patterns & Guardrails

- **Hard-Coded Public Canaries** — Using publicly documented canary token names that attackers can easily identify and bypass.
- **Missing Automated Quarantines** — Detecting honeytoken breaches without triggering immediate session quarantine.
