# 🛰️ SME v2.2.0: The Control Room Operator Manual

This guide covers the deployment and operation of the **Semantic Memory Engine (SME)** forensic suite. By using the containerized v2.0.0 release, you bypass the [dependency conflicts](https://github.com/SpectreDeath/Semantic-Memory-Engine/blob/main/docs/DEPENDENCY_GRAPH.md) found in previous versions.

## 1. 🚀 Quick Deployment

To launch the full suite using the pre-built images from the [GitHub Container Registry](https://github.com/SpectreDeath?tab=packages):

1. **Download** the `docker-compose.yaml` from the [v2.0.0 release page](https://github.com/SpectreDeath/Semantic-Memory-Engine/releases/tag/v2.0.0).
2. **Open a Terminal** in that folder and run:

   ```bash
   docker-compose pull && docker-compose up -d
   ```

3. **Access the UI**: Open your browser to `http://localhost:5173`.

---

## 🛠️ Installation & Build Flags (v2.2.0)

When deploying to a new environment (e.g., Python 3.14+), you MUST use specific build flags to enable CUDA acceleration for the **Sentinel Provider**:

```bash
# Enable CUDA for llama-cpp-python on Windows
$env:FORCE_CMAKE="1"
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python --no-cache-dir
```

## 2. 🎮 The Control Room UI

The v2.0.0 interface centralizes the forensic tools that were previously CLI-only:

- **Connections Tab**: Monitor the status of the **Operator** and the **Sidecar**.
- **Harvester Panel**: Trigger URL crawls and structural conversion via **MarkItDown**. Supports PDF, DOCX, and HTML.
- **Forensic Dashboard**: View real-time results from the **Adversarial Pattern Breaker (APB)** and linguistic signature scans.
- **Entity Redaction**: Automated stripping of proper names, emails, and URLs before analysis to preserve identity neutrality.

---

## 3. 🛠️ Hardware Optimization (GTX 1660 Ti)

Your environment is specialized to handle the 6GB VRAM limit of the 1660 Ti:

- **The Sidecar Strategy**: v2.2.0 introduced the **Sentinel Monitor** and **Sentinel Provider**.
- **GGUF-First Stability**: The Sentinel prioritizes stability by leverage system RAM (offloading GGUF layers) if VRAM pressure exceeds 5.5GB.
- **LoRA Switching**: Forensic personas (Legal, Adversarial, etc.) are swapped in sub-seconds via LoRA adapters, avoiding PCIe bandwidth stalls.
- **Polars Integration**: Uses high-performance **Polars LazyFrames** for corpus comparison.
- **VRAM Guard**: The SentinelMonitor issues hardware signals to the sidecar to dynamically adjust offloading before a crash occurs.
- **Node Limits**: Visualization tools are capped at **2,000 nodes** to ensure smooth performance on laptop hardware.

---

## 4. 🔍 Forensic Workflow: The "Miller Print"

To perform a standard identity verification run:

1. **Ingest**: Use the Harvester UI/API to convert documents. Entities are redacted by default.
2. **Analyze**: Trigger the **ForensicAgent** to extract rhetorical signatures.
3. **Compare**: The system computes **Manhattan Distance** against the reference corpus using Polars.
4. **Audit**: Check the **Smoothing Score**. A score below **5.0** indicates potential AI-generated text or "smoothed" rhetoric.
5. **Verify**: Compare results against "Miller Base" prints in `laboratory.db`.

---

## 5. 🛑 Maintenance & Troubleshooting

- **Updating**: Since the images are tagged, you can update the logic by running `docker-compose pull` whenever a new version is released.
- **Data Persistence**: All forensic data, including your [Poisoned Well Reports](https://github.com/SpectreDeath/Semantic-Memory-Engine/blob/main/docs/OPERATION_POISONED_WELL_REPORT.md), are persisted in the `data/` volume and `laboratory.db`.
- **Logs**: If a scan hangs, check the hardware hooks with:

   ```bash
   docker-compose logs -f sme-sidecar
   ```
