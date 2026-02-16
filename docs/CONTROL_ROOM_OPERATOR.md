# 🕹️ Control Room Operator Guide (v2.0.0)

Welcome to the **Command Center** of the Semantic Memory Engine. Version 2.0.0 transitions SME from a collection of CLI scripts into a unified, containerized forensic laboratory.

---

## 🚀 Quick Launch

The v2.0.0 stack is designed to run in **Docker** to bypass environment conflicts and optimize your GPU (1660 Ti) automatically.

```bash
# Pull and start the laboratory
docker-compose up -d
```

**Access Points:**

- **Control Room UI**: [http://localhost:5173](http://localhost:5173)
- **Operator API**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **AI Sidecar**: [http://localhost:8089/health](http://localhost:8089/health)

---

## 🔌 Navigation: The Three Pillars

### 1. Connections Manager

Monitor the pulse of your infrastructure.

- **Service Status**: Real-time health checks for the **Operator**, **Sidecar**, and **Database**.
- **AI Strategy**: Switch between AI providers (Langflow, Ollama, Mock) on the fly without restarting the containers.
- **Hardware Pulse**: Monitor VRAM usage to stay within the 6GB limit of the 1660 Ti.

### 2. The Harvester

The entry point for all semantic data.

- **Semantic Crawl**: Input a URL to convert it into atomic facts.
- **Deep Domain Mapping**: Enable **Deep Crawl** to recursively map an entire domain.
- **JS Rendering**: Toggle **JS Render** for modern SPAs (Next.js/React).

### 3. Tool Lab

Access specialized forensic utilities in one place.

- Run audits, sniffs, and visual bridges directly from the dashboard.

---

## 📂 Forensic Pathing (Container vs. Local)

> [!IMPORTANT]
> In v2.0.0, the "Source of Truth" for data is within the container volumes.

| Local Path (Host) | Container Path | Purpose |
| :--- | :--- | :--- |
| `d:/SME/data/` | `/app/data/` | Knowledge Graph & Centrifuge DB |
| `d:/SME/storage/` | `/app/storage/` | Raw Harvester captures & Logs |
| `d:/SME/extensions/` | `/app/extensions/` | Custom logic & plugin manifests |

**Note on Manual Scripts**: If you run a local script like `python src/utils/auditor.py`, ensure your environment variables (like `SME_DB_PATH`) point to the relative paths to match the container's expectations.

---

## 🛠️ Troubleshooting

- **Sidecar Offline**: Ensure the `sme-sidecar` container is running (`docker logs sme-sidecar`).
- **Database Connection**: Check if Postgres is healthy at `localhost:5432`.
- **UI Build Error**: If running manually outside Docker, run `npm install` in the `frontend` folder.

---

**Next Steps**: See [ADVANCED_QUICKSTART.md](file:///d:/SME/docs/ADVANCED_QUICKSTART.md) for deeper probe configurations.
