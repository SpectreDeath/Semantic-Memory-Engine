# ⚡ Advanced Tools Quick Start

**New Tools Added:** Curator, Beacon, Echo
**Total SimpleMem Toolkit:** 33+ tools
**Status:** Ready to deploy

---

## 🎯 30-Second Overview

| Tool | Purpose | Command |
| :--- | :--- | :--- |
| **Control Room** | Unified Hub (Connections + Ingestion) | `docker-compose up` |
| **Curator** | Learn from corrections | `calibrate_signal_term("term", "too_high")` |
| **Beacon** | Visualize trends + alerts | `streamlit run beacon_dashboard.py` |
| **Echo** | Transcribe YouTube/audio | `transcribe_youtube_url("https://...")` |

---

## 📦 Installation (2 steps)

```bash
# 1. Update dependencies
pip install -r requirements.txt

# 2. Verify installation
python validate_toolbox.py
```

### Optional: Verify specific dependencies

```bash
python -c "from echo_transcriber import check_transcription_dependencies"
```

---

## 🚀 First Run: Complete Workflow

### Example: Analyze 1 YouTube Video

```bash
# 1. Transcribe (5-10 minutes)
python -c "
from echo_transcriber import transcribe_youtube_url
result = transcribe_youtube_url(
    'https://www.youtube.com/watch?v=...',
    model_size='medium'
)
print(f'Transcribed: {result}')
"

# 2. Check transcripts
python -c "
from echo_transcriber import list_transcripts
transcripts = list_transcripts()
print(f'Found {len(transcripts)} transcripts')
"

# 3. View transcript
python -c "
from echo_transcriber import get_transcript_text
text = get_transcript_text('transcript_20260120_143022.json')
print(text['text'][:500])
"

# 4. Distill with Loom
python -c "
from semantic_loom import distill_web_content
result = distill_web_content(text['text'])
print(f'Atomic facts: {len(result[\"atomic_facts\"])}')
"

# 5. Launch dashboard
streamlit run beacon_dashboard.py
```

---

## 🎯 The Curator: Signal Calibration

**When to use:** After Watch & Analyze flags something

```python
from curator_lexicon import calibrate_signal_term

# Simple: Single term correction
calibrate_signal_term(
    term="vermin",
    correction_type="too_high",  # Was too negative
    strength=0.7  # 70% adjustment strength
)

# Bulk: Multiple corrections
from curator_lexicon import bulk_calibrate_signals
import json

corrections = [
    {"term": "vermin", "correction_type": "too_high"},
    {"term": "entities", "correction_type": "neutral"},
    {"term": "infestation", "correction_type": "too_low"}
]

result = bulk_calibrate_signals(json.dumps(corrections))
print(f"Applied {result['corrections_applied']} corrections")

# Review: Check what changed
from curator_lexicon import get_calibration_statistics
stats = get_calibration_statistics()
print(f"Total calibrations: {stats['total_calibrations']}")
print(f"Most adjusted: {stats['most_calibrated_terms']}")
```

---

## 📊 The Beacon: Predictive Dashboard

**Launch the dashboard:**

```bash
streamlit run beacon_dashboard.py
```

**Then:**

1. Open <http://localhost:8501> in browser
2. Use sidebar to select mode:
   - **Trends:** Sentiment over time
   - **Pharos:** Escalation prediction
   - **Foundations:** Moral foundation heatmap
   - **Alerts:** Real-time warnings

**What to look for:**

- 🔴 Red alert = escalation detected
- 📈 Spikes > 1.5σ = rhetoric spike
- Upward trend = concerning pattern

---

## 🎙️ The Echo: Audio Transcription

**Quick test:**

```python
from echo_transcriber import check_transcription_dependencies

deps = check_transcription_dependencies()
print(f"Whisper installed: {deps['dependencies']['whisper']['installed']}")
print(f"yt-dlp installed: {deps['dependencies']['yt-dlp']['installed']}")
```

**Transcribe YouTube:**

```python
from echo_transcriber import transcribe_youtube_url

result = transcribe_youtube_url(
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    model_size="medium"  # or: tiny, base, small, large
)

if result['status'] == 'complete':
    print(f"✓ Transcribed: {result['video_title']}")
    print(f"  Words: {result['word_count']}")
    print(f"  File: {result['transcript_file']}")
    # Now ready for Loom!
else:
    print(f"✗ Error: {result['error']}")
```

**Transcribe local audio:**

```python
from echo_transcriber import transcribe_audio_file

result = transcribe_audio_file(
    file_path="D:/path/to/audio.mp3",
    model_size="medium"
)

if result['status'] == 'success':
    print(f"✓ Transcript saved: {result['transcript_file']}")
```

**List all transcripts:**

```python
from echo_transcriber import list_transcripts

transcripts = list_transcripts()
for t in transcripts['transcripts']:
    print(f"- {t['filename']} ({t['word_count']} words)")
```

---

## 🔄 Complete Workflows

### Workflow 1: YouTube → Analysis

```python
from echo_transcriber import transcribe_youtube_url
from semantic_loom import distill_web_content
from curator_lexicon import bulk_calibrate_signals

# 1. Transcribe
transcript = transcribe_youtube_url(
    "https://www.youtube.com/watch?v=...",
    model_size="medium"
)

# 2. Extract full text
text = transcript['transcript']

# 3. Distill to facts
distilled = distill_web_content(text, source_url=transcript['url'])

# 4. If needed, calibrate signals
corrections = [
    {"term": "problematic_word", "correction_type": "too_high"}
]
bulk_calibrate_signals(corrections)

print(f"✓ Complete: {distilled}")
```

### Workflow 2: Feedback Loop

```python
from curator_lexicon import process_watcher_feedback

# When Watcher flags something:
flag_event = {
    "source_file": "document.txt",
    "moral_foundation": "Sanctity/Degradation"
}

# You correct it:
user_feedback = "vermin:too_high|parasite:too_high|entities:neutral"

# Curator learns:
result = process_watcher_feedback(
    json.dumps(flag_event),
    user_feedback
)

print(f"✓ Learned {result['corrections_applied']} corrections")
```

### Workflow 3: Weekly Monitoring

```bash
# Run every week:
python -c "
from beacon_dashboard import RhetoricAnalyzer
import json

analyzer = RhetoricAnalyzer('./storage/laboratory.db')
df = analyzer.get_sentiment_timeline(days=7)
prediction = analyzer.predict_escalation(df)

if prediction['alert'] == 'escalation_detected':
    print('⚠️  ALERT: Rhetoric escalating')
    print(f'   Trend strength: {prediction[\"strength\"]}')
else:
    print('✓ Stable - no escalation detected')
"
```

---

## 🛠️ Troubleshooting

### Echo: FFmpeg not found

```bash
# Windows: Download from https://ffmpeg.org/download.html
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

### Echo: CUDA out of memory

```python
# Use smaller model instead of medium
transcribe_youtube_url(url, model_size="base")  # or "small"
```

### Beacon: Can't connect to dashboard

```bash
# Make sure Streamlit is installed
pip install streamlit

# Try explicit URL
streamlit run beacon_dashboard.py --server.port 8501
```

### Curator: Signals not updating

```bash
# Check file permissions
import os
signals_path = "./storage/compiled_signals.json"
print(f"Exists: {os.path.exists(signals_path)}")
print(f"Writable: {os.access(signals_path, os.W_OK)}")
```

---

## 📊 Performance Expectations

| Operation | Time | Notes |
| :--- | :--- | :--- |
| YouTube transcribe (1hr) | 5-10 min | Model: medium, 1660 Ti |
| Loom distillation | <1 sec | For transcripts |
| Beacon dashboard load | <5 sec | First time loads model |
| Signal calibration | <1 ms | Immediate |
| Dashboard pivot | <1 sec | Redraw chart |

---

## 🎯 Best Practices

### Curator

- ✅ Start with `strength=0.5` (conservative)
- ✅ Review suggestions before bulk calibration
- ✅ Keep calibration log backed up
- ✅ Check stats weekly

### Beacon

- ✅ Monitor Pharos alerts for escalation
- ✅ Export snapshots for reports
- ✅ Adjust spike threshold if needed
- ✅ Watch for foundation distribution changes

### Echo

- ✅ Check dependencies before batch
- ✅ Use `model_size="medium"` for balance
- ✅ Transcribe during low-GPU periods
- ✅ Verify quality before distillation

---

## 🚀 Integration Checklist

- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Validation passed: `python validate_toolbox.py`
- [ ] Original 7 tools tested
- [ ] Curator calibration tested
- [ ] Beacon dashboard launches
- [ ] Echo transcription works
- [ ] FFmpeg installed (for Echo)
- [ ] MCP endpoints registered
- [ ] Monitoring enabled

---

## 🕹️ The Control Room: Unified Hub (v2.0.0)

**Launch the full stack:**

```bash
docker-compose up --build
```

**Accessing the Dashboard:**

1. Open [http://localhost:5173](http://localhost:5173)
2. **Connections Tab**: Monitor Sidecar and Database health. Switch AI providers dynamically.
3. **Harvester Tab**: Ingest new web content by providing a URL.

**Harvester Features:**

- ✅ **JS Render**: Enable for React/Next.js sites.
- ✅ **Deep Crawl**: Enable recursive mapping of domain subpages.
- ✅ **Report**: View word count, quality scores, and raw markdown capture.

---

## 📚 Documentation

- [CONTROL_ROOM_OPERATOR.md](CONTROL_ROOM_OPERATOR.md) - Definitive guide for v2.0.0
- [RELEASE_STRATEGY.md](../RELEASE_STRATEGY.md) - Release strategy guide
- Inline docstrings: `help(calibrate_signal_term)`, etc.

---

## 🎉 Summary

**3 new advanced tools:**

- 🎯 **Curator:** Closed-loop learning
- 📊 **Beacon:** Predictive monitoring
- 🎙️ **Echo:** Audio transcription

**Total SimpleMem toolkit:** 33+ tools, 10 categories, production-ready

**Next: Deploy and start analyzing!** 🚀
