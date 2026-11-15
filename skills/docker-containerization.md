---
name: docker-containerization
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Process
category: Core
source_file: Dockerfile.operator
source: Semantic Memory Engine (SME)
tags:
  - docker-containerization
  - container-lifecycle
  - multi-stage-builds
  - service-isolation
  - docker-compose
inputs:
  service_name:
    type: string
    required: true
    description: Target service container (`'operator'`, `'frontend'`, `'nexus_db'`).
  action:
    type: string
    required: true
    description: Operation (`'build'`, `'up'`, `'down'`, `'inspect'`).
outputs:
  container_status:
    type: string
    description: Current container execution state (`'running'`, `'stopped'`, `'exited'`).
  port_mappings:
    type: object
    description: Host-to-container port binding mapping.
  health_status:
    type: string
    description: Docker container health check verdict (`'healthy'` or `'unhealthy'`).
---

# Docker Containerization Engine

`docker-containerization` orchestrates multi-container builds and deployments for the Lawnmower Man operator, frontend, and database services:

$$\text{DeploymentState} = \text{DockerCompose}(\{\text{Operator: 8000}, \text{Frontend: 5173}, \text{NexusDB: 5432}\})$$

---

## The 5-Stage Docker Containerization Progression

1. **Service Target Intake & Compose Parsing**: Ingest service name; parse `docker-compose.yaml` configuration.
2. **Multi-Stage Build Execution**: Build lightweight production image with minimal runtime layers.
3. **The Visual Brief**: Generate interactive HTML container topology dashboard at `%TEMP%\docker-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert container health check passing (`/health` endpoint 200 OK).
5. **Service Status & Output Emission**: Emit port mappings and active container state.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def manage_docker_service(
    service_name: str,
    action: str = "inspect"
) -> Dict[str, Any]:
    port_map = {"operator": {"8000/tcp": "8000"}, "frontend": {"5173/tcp": "5173"}}
    return {
        "container_status": "running",
        "port_mappings": port_map.get(service_name, {}),
        "health_status": "healthy"
    }
```

---

## Anti-Patterns & Guardrails

- **Root Container Execution** — Running production containers with default root privileges.
- **Bloated Image Layers** — Including build tools and test caches in production container images.