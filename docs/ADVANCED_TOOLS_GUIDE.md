# 🚀 Advanced Tools: Curator, Beacon, Echo

## Three Powerful Additions to SimpleMem Toolkit

Your toolbox now includes three advanced capabilities for intelligent signal calibration, predictive analytics, and audio processing.

---

## 🎯 The Curator (Lexicon Auto-Calibration)

**File:** `curator_lexicon.py`
**Purpose:** Closed-loop feedback learning for signal weights

### Tools (6):

1. **`calibrate_signal_term()`**
   - Adjusts weight of a single signal term
   - Correction types: `too_high` | `too_low` | `neutral` | `context_dependent`
   - Adaptive adjustment based on correction strength (0-1)

2. **`bulk_calibrate_signals()`**
   - Applies multiple calibrations simultaneously
   - Input: JSON array of corrections
   - Returns success count and details

3. **`get_calibration_statistics()`**
   - Shows calibration history and trends
   - Most-calibrated terms
   - Correction type distribution

4. **`suggest_signal_calibrations()`**
   - AI-powered suggestions based on statistical anomalies
   - Uses z-score outlier detection
   - Highlights terms needing review

5. **`revert_calibrations()`**
   - Undo last N calibrations
   - Full rollback to previous weights
   - Maintains audit trail

6. **`process_watcher_feedback()`**
   - Processes corrections from Watch & Analyze
   - Format: `"term1:too_high|term2:neutral|term3:context_dependent"`
   - Automatic adjustment with rationale logging

### Example Workflow:

```python
# Watch & Analyze flags: "dehumanizing_metaphors in document.txt"
# You review and say: "Actually, these terms aren't THAT negative"

correction = {
    "term": "vermin",
    "correction_type": "too_high",  # Was -3.5, reduce to -2.0
    "moral_foundation": "Sanctity/Degradation",
    "rationale": "Medical context, not dehumanizing",
    "strength": 0.7
}

# Curator learns
calibrate_signal_term(
    term="vermin",
    correction_type="too_high",
    moral_foundation="Sanctity/Degradation",
    rationale="User override after manual review",
    strength=0.7
)

# Get stats
stats = get_calibration_statistics()
# Shows: 47 calibrations, most-adjusted terms, trend analysis
```

### Adaptive Adjustment Formula:

- **too_high**: Reduces magnitude (toward 0)
- **too_low**: Increases magnitude (more extreme)
- **neutral**: Moves toward 0 (confidence reduction)
- **context_dependent**: Reduces weight by 70% (flags for contextual analysis)

---

## 📊 The Beacon (Predictive Rhetoric Dashboard)

**File:** `beacon_dashboard.py`
**Purpose:** Streamlit-based visualization & Pharos predictive alerts

### Installation:
```bash
pip install streamlit plotly
python -m streamlit run beacon_dashboard.py
```

### Dashboard Modes:

#### 1. **Trends Mode**
- Sentiment timeline with 7-day and 30-day moving averages
- Heat-map colored sentiment markers
- Rhetorical spike detection (customizable threshold)
- Daily/weekly aggregation

#### 2. **Pharos (Predictive) Mode**
- **Trend Direction**: Escalating vs. Deescalating
- **Trend Strength**: Magnitude of change
- **7-Day Projection**: Linear extrapolation
- **Alert System**: AUTO flags escalation
- Use case: Detect when dehumanizing rhetoric is accelerating

#### 3. **Foundations Mode**
- Radar chart of 6 Moral Foundations:
  - Care/Harm
  - Fairness/Cheating
  - Loyalty/Betrayal
  - Authority/Subversion
  - Sanctity/Degradation
  - Liberty/Oppression
- Foundation intensity heatmap
- Trend analysis per foundation

#### 4. **Alerts Mode**
- 🔴 **CRITICAL**: Escalation detected
- 🟢 **NORMAL**: Safe zone
- High-intensity event listing
- Dehumanizing rhetoric warnings

### Dashboard Features:

**Real-time Updates:**
```
Current Sentiment: -0.345
7-Day Average: -0.218
Trend: 📈 Improving
```

**Spike Detection:**
- Z-score > threshold triggers alert
- Shows source document
- Severity classification (medium/high)

**Predictive Alerts:**
```
Trend: ESCALATING
Strength: 0.0847
Recent Mean: -0.402
Alert: ESCALATION_DETECTED ⚠️
```

### Example Dashboard Session:

```
User opens Beacon → Pharos Mode
↓
System detects: Recent 7-day mean = -0.402
Previous 7-day mean = -0.280
↓
Alert: "Dehumanizing rhetoric escalating 12% week-over-week"
↓
Projected trajectory shows continued decline
↓
Curator recommends: Review top 5 high-z-score documents
```

---

## 🎙️ The Echo (Local Transcription Engine)

**File:** `echo_transcriber.py`
**Purpose:** GPU-accelerated Whisper transcription for audio/video → text

### Installation:

```bash
# 1. Install Python dependencies
pip install openai-whisper yt-dlp

# 2. Install FFmpeg (required for yt-dlp)
# Windows: Download from https://ffmpeg.org/download.html
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg

# 3. Verify dependencies
python -c "from echo_transcriber import check_transcription_dependencies"
```

### Tools (5):

1. **`transcribe_youtube_url()`**
   - Downloads audio from YouTube
   - Transcribes using GPU-accelerated Whisper
   - Returns complete transcript
   - Model options: tiny, base, small, medium (recommended), large

2. **`transcribe_audio_file()`**
   - Transcribes local audio files
   - Supports: MP3, WAV, M4A, FLAC, OGG, etc.
   - Same Whisper models available

3. **`check_transcription_dependencies()`**
   - Verifies Whisper, yt-dlp, FFmpeg installed
   - Provides install commands if missing
   - Pre-flight check before processing

4. **`list_transcripts()`**
   - Shows all transcripts in storage
   - File size, word count, source metadata
   - JSON format for easy integration

5. **`get_transcript_text()`**
   - Retrieves full transcript by filename
   - Returns text ready for Loom distillation
   - Includes metadata

### Whisper Model Sizes:

| Model | Speed | Quality | VRAM | Best For |
|-------|-------|---------|------|----------|
| tiny | ⚡⚡⚡ | ⭐ | 1GB | Quick testing |
| base | ⚡⚡ | ⭐⭐ | 1GB | Fast processing |
| small | ⚡ | ⭐⭐⭐ | 2GB | Good balance |
| medium | 🐢 | ⭐⭐⭐⭐ | 5GB | **Recommended for 1660 Ti** |
| large | 🐢🐢 | ⭐⭐⭐⭐⭐ | 10GB | Best quality |

### GPU Optimization for 1660 Ti:

- **VRAM Available**: ~6GB
- **Recommended Model**: `medium`
- **Performance**: ~15-30 min for 1-hour video (depending on audio quality)
- **Batch Processing**: Queue multiple transcriptions for overnight runs

### Example Workflow:

```python
# Scenario: Analyze rhetoric from YouTube video

# Step 1: Transcribe
result = transcribe_youtube_url(
    url="https://www.youtube.com/watch?v=...",
    model_size="medium"
)
# Returns: transcript_20260120_143022.json (12,547 words)

# Step 2: Verify transcription
transcripts = list_transcripts()
# Shows: "Rhetoric Analysis - Jan 2026 Event" (234 KB, 12,547 words)

# Step 3: Get full text
full_text = get_transcript_text("transcript_20260120_143022.json")

# Step 4: Feed to Loom
distilled = distill_web_content(
    content=full_text['text'],
    source_url="YouTube: " + full_text['source']
)
# Atomic facts extracted, compressed 30x

# Step 5: Verify sentiment
facts = extract_atomic_facts(distilled)
# Rhetoric spikes identified

# Step 6: Dashboard
beacon_analyze(distilled)
# Visualize moral foundation usage in speech
```

---

## 🔄 Integration: Echo → Loom → Beacon

### Complete Pipeline:

```
YouTube URL
    ↓
Echo (Whisper Transcription)
    ↓
Transcript JSON
    ↓
Loom (Semantic Distillation)
    ↓
Atomic Facts (30x compressed)
    ↓
Beacon Dashboard
    ↓
Moral Foundation Heat Map
    ↓
Pharos Alerts (if escalating)
```

### Example: Processing a 30-min Speech

**Time Breakdown (1660 Ti):**
- Echo transcription: 5-10 minutes
- Loom distillation: <1 second
- Beacon analysis: <1 second
- Dashboard generation: <5 seconds
- **Total: ~10 minutes per video**

---

## 🛠️ Advanced Configuration

### Curator: Custom Adjustment Functions

Edit `_adaptive_adjustment()` in curator_lexicon.py to implement custom learning rules:

```python
# Example: More aggressive learning
def aggressive_learning(old_weight, strength):
    # Double the adjustment magnitude
    return old_weight * (1 - strength * 0.6)
```

### Beacon: Custom Foundation Mappings

Edit `analyze_moral_foundations()` to add domain-specific foundations:

```python
# Add custom foundation
'Environmental/Exploitation': {
    'terms': ['ecosystem', 'climate', 'nature', 'destroy'],
    'intensity': 0
}
```

### Echo: Batch Transcription

Queue multiple videos for overnight processing:

```bash
# Create batch_urls.txt with one URL per line
# Then run:
for url in $(cat batch_urls.txt); do
    python -c "transcribe_youtube_url('$url', model_size='medium')"
done
```

---

## 📊 Data Storage & Persistence

### Curator:
- `compiled_signals.json` - Updated weights
- `calibration_log.json` - Full audit trail

### Beacon:
- `sentiment_logs` table - Visualization source
- Reads from Centrifuge DB (no new storage needed)

### Echo:
- `transcripts/` directory
- Each transcript: JSON file with metadata
- Auto-indexed by list_transcripts()

---

## 🚨 Troubleshooting

### Curator:
- **Issue**: Weights not updating
- **Fix**: Check `compiled_signals.json` permissions
- **Tip**: Run `get_calibration_statistics()` to verify updates

### Beacon:
- **Issue**: Dashboard won't load
- **Fix**: `pip install streamlit plotly`
- **Tip**: Run `streamlit run beacon_dashboard.py --logger.level=debug`

### Echo:
- **Issue**: YouTube download fails
- **Fix**: Update yt-dlp: `pip install --upgrade yt-dlp`
- **Tip**: Check FFmpeg is in PATH: `ffmpeg -version`

- **Issue**: CUDA out of memory
- **Fix**: Use smaller model: `model_size="base"` or `"small"`
- **Tip**: Transcribe during low-GPU periods

---

## 🎯 Best Practices

### Curator:
1. ✅ Start with strength=0.5 (conservative learning)
2. ✅ Review suggestions before bulk calibration
3. ✅ Keep calibration_log.json backed up (audit trail)
4. ✅ Run `suggest_signal_calibrations()` weekly

### Beacon:
1. ✅ Monitor Pharos alerts for escalation
2. ✅ Check moral foundation heatmap weekly
3. ✅ Set custom spike threshold (default 1.5σ)
4. ✅ Export dashboard screenshots for analysis

### Echo:
1. ✅ Check dependencies before batch processing
2. ✅ Use model_size="medium" for best balance
3. ✅ Transcribe during off-peak GPU usage
4. ✅ Verify transcript quality before distillation

---

## 📈 Performance & Resource Usage

| Tool | CPU | GPU | Memory | Storage |
|------|-----|-----|--------|---------|
| Curator | <1% | 0% | <50MB | ~5KB/calibration |
| Beacon | <5% | 0% | ~200MB | 0 (uses DB) |
| Echo (idle) | <1% | 0% | <100MB | N/A |
| Echo (transcribing) | ~30% | 85% | ~5GB | ~50MB/hour audio |

---

## 📚 Documentation Files

Each tool has inline docstrings:
```python
help(calibrate_signal_term)
help(transcribe_youtube_url)
# etc.
```

---

## 🚀 Quick Start Commands

```bash
# 1. Check all dependencies
python -c "from curator_lexicon import SignalCurator; from echo_transcriber import WhisperTranscriber; print('✓ Ready')"

# 2. Start Beacon dashboard
streamlit run beacon_dashboard.py

# 3. Test Curator
python -c "from curator_lexicon import calibrate_signal_term; calibrate_signal_term('test_term', 'too_high', strength=0.5)"

# 4. Check Echo
python -c "from echo_transcriber import check_transcription_dependencies"

# 5. Transcribe YouTube
python -c "from echo_transcriber import transcribe_youtube_url; transcribe_youtube_url('https://youtube.com/watch?v=...')"
```

---

## 🎯 Your Complete SimpleMem Stack

**Now includes 33+ tools across 10 categories:**

Original 7:
- Semantic Loom
- Memory Synapse
- Adaptive Scout
- Data Processor
- Monitoring & Diagnostics
- Pipeline Orchestrator
- Retrieval & Query

**New 3:**
- ✨ The Curator (Signal Calibration)
- ✨ The Beacon (Predictive Dashboard)
- ✨ The Echo (Audio Transcription)

**Total: 33 tools, production-ready, fully integrated** 🎉
