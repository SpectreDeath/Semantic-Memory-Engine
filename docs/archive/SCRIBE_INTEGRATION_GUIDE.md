# 🖋️ SCRIBE Integration Guide - Layer 6 Forensic Analysis

**Location:** `scribe_authorship.py`  
**Purpose:** Forensic authorship analysis using 6,734 rhetoric signals  
**Hardware Profile:** CPU/RAM intensive, 0% GPU (stays free for Loom)  
**Database:** `centrifuge_db.sqlite` (author profiles + attribution history)

---

## Table of Contents

1. [Quick Start (2 min)](#quick-start)
2. [The 4 Core Tools](#core-tools)
3. [Workflow Integration](#workflow-integration)
4. [Scout Integration](#scout-integration)
5. [Beacon Dashboard Integration](#beacon-dashboard)
6. [Database Schema](#database-schema)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

```bash
pip install scipy nltk
python -m nltk.downloader punkt
```

### Basic Usage (Copy-Paste Ready)

```python
from scribe_authorship import ScribeEngine
import asyncio

# Initialize
scribe = ScribeEngine()

# Step 1: Create a profile for a known author
known_text = """
The rapid proliferation of digital communication has fundamentally altered 
our understanding of linguistic patterns. Moreover, the statistical analysis 
thereof reveals significant deviations from established paradigms...
"""

fp = scribe.extract_linguistic_fingerprint(known_text, author_id="author_smith")
scribe.save_author_profile(fp, author_name="Dr. Eleanor Smith")
print("✅ Profile created for Dr. Smith")

# Step 2: Analyze unknown text
unknown_text = """
The widespread adoption of internet technologies has changed how we think 
about language. Furthermore, empirical evidence demonstrates notable shifts 
from traditional communication models...
"""

# Compare to all known profiles
matches = scribe.compare_to_profiles(
    scribe.extract_linguistic_fingerprint(unknown_text),
    min_confidence=50.0
)

print(f"🔍 Top match: {matches[0]['author_name']} ({matches[0]['confidence_score']:.1f}%)")

# Step 3: Get precise attribution score
score, breakdown = scribe.calculate_attribution_score(unknown_text, "author_smith")
print(f"📈 Attribution confidence: {score:.1f}%")

# Step 4: Detect anomalies
report = scribe.identify_stylistic_anomalies("author_smith", unknown_text)
if report:
    print(f"⚠️ Anomalies detected ({report.severity}):")
    for anomaly in report.anomalies_detected:
        print(f"   {anomaly}")
else:
    print("✅ No anomalies - writing style is consistent")
```

---

## Core Tools

### Tool 1: `extract_linguistic_fingerprint(text, author_id)`

**Purpose:** Convert any text into a unique behavioral profile vector

**What it captures:**
- Sentence structure preferences (avg length, variance)
- Vocabulary richness (type-token ratio, lexical diversity)
- Punctuation "sparks" (Oxford commas, em-dashes, etc.)
- Rhetorical signal distribution (which of 6,734 signals they favor)
- Voice usage (active vs. passive ratio)
- Clause complexity patterns

**Returns:**
```python
LinguisticFingerprint(
    author_id="author_smith",
    avg_sentence_length=18.3,  # words
    lexical_diversity=0.68,     # 0-1 scale
    passive_voice_ratio=0.35,   # 35% passive
    signal_vector=[...],        # 100-dim normalized vector
    signal_weights={...},       # {signal_id: weight}
    punctuation_profile={...}   # {',': 0.15, ';': 0.08}
)
```

**Computational profile:**
- Input: 1000 words = ~50ms
- Input: 10,000 words = ~200ms
- Memory overhead: <5MB per call
- GPU usage: 0% (NLTK processing on CPU)

---

### Tool 2: `compare_to_profiles(unknown_fingerprint, min_confidence)`

**Purpose:** Match unknown text against all known author profiles

**How it works:**
1. Calculates cosine similarity on signal vectors (40% weight)
2. Compares linguistic metrics (25% weight)
3. Evaluates punctuation patterns (15% weight)
4. Checks lexical diversity (15% weight)
5. Scores voice ratio alignment (5% weight)

**Returns:**
```python
[
    AuthorshipMatch(
        author_id="author_smith",
        author_name="Dr. Eleanor Smith",
        confidence_score=82.4,  # 0-100
        match_strength="High",  # "High", "Medium", "Low", "Inconclusive"
        reasoning="Signal alignment: 85% | Metric similarity: 79% | ..."
    ),
    AuthorshipMatch(
        author_id="author_jones",
        confidence_score=45.2,
        match_strength="Low",
        ...
    )
]
```

**Use cases:**
- ✓ De-masking anonymous blog posts
- ✓ Identifying likely authors of leaked documents
- ✓ Detecting plagiarism (text doesn't match any known author)
- ✓ Finding copycats (new author mimicking known style)

---

### Tool 3: `calculate_attribution_score(unknown_text, candidate_author_id)`

**Purpose:** Get precise 0-100 attribution probability for ONE author

**Returns detailed breakdown:**
```python
(
    attribution_score=87.3,  # 0-100 confidence
    breakdown={
        "signal_alignment": 89.2,
        "linguistic_metrics": 84.5,
        "punctuation_habits": 88.1,
        "lexical_diversity": 82.3,
        "voice_ratio_match": 78.4,
        "final_attribution_score": 87.3,
        "confidence_level": "High"  # "Very High", "High", "Moderate", "Low", "Very Low"
    }
)
```

**Confidence levels:**
- **Very High (90+%):** Near-certain match (strong for court evidence)
- **High (75-89%):** Very likely match (useful for investigations)
- **Moderate (60-74%):** Probable match (requires corroboration)
- **Low (40-59%):** Possible match (not reliable alone)
- **Very Low (<40%):** Unlikely match (inconsistent profile)

---

### Tool 4: `identify_stylistic_anomalies(author_id, new_text)`

**Purpose:** Detect when a known author's style suddenly changes

**What triggers anomalies:**
- Sentence length shift >25%
- Signal distribution shift >30%
- Vocabulary richness change >20%
- Punctuation usage change >35%
- Voice ratio shift >15% (often indicates AI generation)

**Returns anomaly report:**
```python
AnomalyReport(
    author_id="author_smith",
    author_name="Dr. Eleanor Smith",
    anomalies_detected=[
        "⚠️ SENTENCE LENGTH: Baseline 18.3 → New 8.7 words (52% shift)",
        "⚠️ VOICE SHIFT: Passive voice 35% → 68% (might indicate AI generation)"
    ],
    severity="High",     # "Critical", "High", "Medium", "Low"
    confidence=75.3,     # 0-100
    baseline_profile={...},
    current_profile={...}
)
```

**Use cases:**
- ✓ Ghost-writing detection (author outsourced writing)
- ✓ AI generation flagging (sudden neutral, balanced style)
- ✓ Account takeover (sudden style change + suspicious content)
- ✓ Quality control (editorial changes that feel "off")

---

## Workflow Integration

### Typical Pipeline: Harvester → Loom → Scribe → Beacon

```
🕷️ HarvesterSpider
    ↓ (raw markdown)
🧠 Loom (semantic compression)
    ↓ (facts + signals)
🖋️ Scribe (authorship check)
    ↓ (confidence + anomalies)
🔔 Beacon (dashboard alert)
```

### Integration Pattern 1: Post-Harvest Attribution

```python
from harvester_spider import HarvesterSpider
from scribe_authorship import ScribeEngine

async def harvest_and_attribute():
    # Step 1: Harvest web content
    spider = HarvesterSpider()
    capture_id, markdown = await spider.capture_site("https://example.com/article")
    
    # Step 2: Extract fingerprint
    scribe = ScribeEngine()
    fingerprint = scribe.extract_linguistic_fingerprint(markdown)
    
    # Step 3: Find matches
    matches = scribe.compare_to_profiles(fingerprint)
    
    if matches and matches[0]['confidence_score'] > 75:
        print(f"🎯 Likely author: {matches[0]['author_name']}")
        return matches
    else:
        print("❓ Unknown author - new profile?")
        return None
```

### Integration Pattern 2: Anonymous Source Identification

```python
def identify_anonymous_blog():
    """Given anonymous blog content, find likely author"""
    
    # Get anonymous blog content
    anonymous_content = """...blog post text..."""
    
    scribe = ScribeEngine()
    
    # Method 1: Broad search
    matches = scribe.compare_to_profiles(
        scribe.extract_linguistic_fingerprint(anonymous_content),
        min_confidence=60.0  # Lower threshold for fishing
    )
    
    # Method 2: Precise scoring on top candidates
    for match in matches[:5]:
        score, breakdown = scribe.calculate_attribution_score(
            anonymous_content,
            match['author_id']
        )
        if score > 80:
            print(f"🎯 High confidence match: {match['author_name']} ({score:.1f}%)")
            return match
    
    print("❌ No high-confidence matches found")
```

### Integration Pattern 3: Anomaly-Triggered Investigation

```python
def monitor_author_for_anomalies(author_id, new_content):
    """Continuously monitor known authors for style changes"""
    
    scribe = ScribeEngine()
    report = scribe.identify_stylistic_anomalies(author_id, new_content)
    
    if report and report.severity in ["Critical", "High"]:
        # Escalate to investigation team
        print(f"🚨 ALERT: {report.severity} anomalies detected")
        print(f"Confidence: {report.confidence:.1f}%")
        
        for anomaly in report.anomalies_detected:
            print(f"  {anomaly}")
        
        # Trigger further analysis
        return report
    else:
        print("✅ Writing style is consistent")
        return None
```

---

## Scout Integration

Scout detects knowledge gaps (complexity ≥7) and can trigger Scribe for:
1. Verifying source credibility based on authorship patterns
2. Flagging suspicious or unverified sources
3. Identifying coordinated inauthentic behavior (multiple "authors" with same fingerprint)

```python
# In scout.py or scout_integration.py

class ScoutWithScribeVerification(Scout):
    def __init__(self):
        super().__init__()
        self.scribe = ScribeEngine()
    
    async def verify_source_authenticity(self, url, harvest_markdown):
        """Verify if harvested content matches claimed author"""
        
        complexity = self.estimate_query_complexity(url)
        if complexity >= 7:
            # Extract fingerprint from harvested content
            fingerprint = self.scribe.extract_linguistic_fingerprint(harvest_markdown)
            
            # Try to match against known credible sources
            matches = self.scribe.compare_to_profiles(fingerprint)
            
            if matches[0]['confidence_score'] > 80:
                return {
                    "verified": True,
                    "likely_author": matches[0]['author_name'],
                    "confidence": matches[0]['confidence_score']
                }
            else:
                return {
                    "verified": False,
                    "reason": "Unverified author profile",
                    "confidence": 0
                }
```

---

## Beacon Dashboard Integration

### Overlay 1: "Identity" View on Trends

```python
# In beacon_dashboard.py

class BeaconScribeOverlay:
    """Show likely authors behind detected trends"""
    
    def build_identity_overlay(self, trend_articles):
        """For trending topic, identify likely driving authors"""
        
        scribe = ScribeEngine()
        author_scores = {}
        
        for article in trend_articles:
            # Extract fingerprint from each article
            fp = scribe.extract_linguistic_fingerprint(article['text'])
            
            # Get matches
            matches = scribe.compare_to_profiles(fp)
            
            # Aggregate author strength
            for match in matches[:3]:  # Top 3 matches per article
                author_id = match['author_id']
                author_scores[author_id] = author_scores.get(author_id, 0) + match['confidence_score']
        
        # Return top authors driving this trend
        return sorted(
            author_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
```

### Overlay 2: "Anomalies" Alert Panel

```python
def build_anomalies_panel():
    """Show suspicious writing pattern changes"""
    
    scribe = ScribeEngine()
    
    # Get all profiles being monitored
    profiles = scribe._get_all_author_profiles()
    
    alerts = []
    for profile in profiles:
        # Get recent content from this author
        recent_content = get_recent_content_by_author(profile['author_id'])
        
        # Check for anomalies
        for content in recent_content:
            report = scribe.identify_stylistic_anomalies(
                profile['author_id'],
                content['text']
            )
            
            if report and report.severity in ["Critical", "High"]:
                alerts.append({
                    "author": profile['author_name'],
                    "severity": report.severity,
                    "confidence": report.confidence,
                    "anomalies": report.anomalies_detected,
                    "timestamp": report.analysis_timestamp
                })
    
    return alerts
```

---

## Database Schema

### `author_profiles` Table

```sql
CREATE TABLE author_profiles (
    author_id TEXT PRIMARY KEY,
    author_name TEXT,
    
    -- Syntactic features
    avg_sentence_length REAL,
    sentence_length_std REAL,
    avg_word_length REAL,
    avg_clause_count REAL,
    
    -- Lexical features
    lexical_diversity REAL,        -- 0-1 scale
    type_token_ratio REAL,
    
    -- Voice preferences
    passive_voice_ratio REAL,      -- 0-1 scale
    active_voice_ratio REAL,
    
    -- Signal-based fingerprinting
    punctuation_profile TEXT,      -- JSON: {',': 0.15, ';': 0.08}
    signal_weights TEXT,           -- JSON: {signal_id: weight}
    signal_vector TEXT,            -- JSON: [100-dim normalized vector]
    
    -- Metadata
    text_sample_count INTEGER,     -- Words analyzed
    samples_count INTEGER,         -- Number of texts in profile
    avg_confidence REAL,           -- Average confidence across samples
    created_at TEXT,
    updated_at TEXT
);

-- Indices for fast lookup
CREATE INDEX idx_author_id ON author_profiles(author_id);
```

### `attribution_history` Table

```sql
CREATE TABLE attribution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unknown_text_hash TEXT UNIQUE,
    candidate_author_id TEXT,
    attribution_score REAL,        -- 0-100
    confidence_level TEXT,         -- "High", "Medium", "Low"
    breakdown TEXT,                -- JSON: detailed component scores
    verified BOOLEAN DEFAULT 0,    -- Manual verification flag
    created_at TEXT,
    FOREIGN KEY (candidate_author_id) REFERENCES author_profiles(author_id)
);

CREATE INDEX idx_attribution_author ON attribution_history(candidate_author_id);
```

### `anomaly_reports` Table

```sql
CREATE TABLE anomaly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id TEXT,
    anomalies_detected TEXT,       -- JSON: list of detected anomalies
    severity TEXT,                 -- "Critical", "High", "Medium", "Low"
    confidence REAL,               -- 0-100
    baseline_profile TEXT,         -- JSON: baseline metrics
    current_profile TEXT,          -- JSON: current metrics
    analysis_timestamp TEXT,
    created_at TEXT,
    FOREIGN KEY (author_id) REFERENCES author_profiles(author_id)
);

CREATE INDEX idx_anomaly_author ON anomaly_reports(author_id);
```

---

## Configuration

### Anomaly Detection Thresholds (in `scribe_authorship.py`)

```python
ANOMALY_THRESHOLDS = {
    "sentence_length_shift": 0.25,      # 25% = flag anomaly
    "signal_consistency_drop": 0.30,    # 30% = flag anomaly
    "vocabulary_shift": 0.20,           # 20% = flag anomaly
    "punctuation_variation": 0.35,      # 35% = flag anomaly
}
```

### Profile Matching Weights

```python
# In compare_to_profiles()
signal_score * 0.40         # 40% - Most important (rhetorical signals)
+ metrics_score * 0.25      # 25% - Linguistic features
+ punctuation_score * 0.15  # 15% - Punctuation habits
+ diversity_score * 0.15    # 15% - Vocabulary richness
+ voice_ratio_score * 0.05  # 5%  - Voice preference
= final_confidence (0-100)
```

Adjust weights based on your domain:
- **Academic detection:** Increase metrics_score weight to 0.35
- **Social media detection:** Increase punctuation_score weight to 0.25
- **Bot detection:** Increase signal consistency monitoring

---

## Troubleshooting

### Issue: Low confidence scores across all matches

**Symptoms:** `confidence_score < 50%` for all authors

**Causes:**
1. Unknown author (not in database)
2. Author database is too small (need minimum 5-10 profiles)
3. Text sample is too short (<500 words)

**Solution:**
```python
# Check database size
stats = scribe.get_scribe_stats()
print(f"Profiles in database: {stats['total_author_profiles']}")

# For new databases, create baseline profiles
for author, sample in training_texts.items():
    fp = scribe.extract_linguistic_fingerprint(sample, author_id=author)
    scribe.save_author_profile(fp, author_name=author)
    
print("✅ Baseline profiles created")
```

### Issue: Too many false positives

**Symptoms:** Attribution scores too high even for dissimilar authors

**Cause:** Confidence threshold too low

**Solution:**
```python
# Increase minimum confidence threshold
matches = scribe.compare_to_profiles(fingerprint, min_confidence=70.0)

# Or inspect breakdown to understand the match
score, breakdown = scribe.calculate_attribution_score(unknown_text, author_id)
if breakdown["signal_alignment"] < 0.60:
    print("⚠️ Weak signal match - might be false positive")
```

### Issue: Anomalies flagged too frequently

**Symptoms:** Every few texts trigger anomaly warnings

**Cause:** Thresholds too sensitive

**Solution:**
```python
# Increase anomaly thresholds in scribe_authorship.py
ANOMALY_THRESHOLDS = {
    "sentence_length_shift": 0.40,      # Was 0.25 (now 40% = flag)
    "signal_consistency_drop": 0.50,    # Was 0.30 (now 50% = flag)
    # ... other thresholds
}
```

### Issue: Performance degradation with large profiles

**Symptoms:** Profile comparison takes >5s

**Causes:**
1. Signal vector is too large
2. Too many profiles in database (>1000)
3. Large text samples (>50KB)

**Solution:**
```python
# Trim oldest low-confidence profiles
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("""
    DELETE FROM author_profiles 
    WHERE avg_confidence < 0.3 
    AND created_at < DATE('now', '-90 days')
""")
conn.commit()

# Or optimize vector size
signal_vector = signal_vector[:50]  # Use top 50 dimensions only
```

---

## Performance Metrics

| Operation | Input | Time | Memory |
|-----------|-------|------|--------|
| Extract fingerprint | 1000 words | 50ms | <5MB |
| Extract fingerprint | 10,000 words | 200ms | <10MB |
| Compare to profiles | 100 profiles | 250ms | <20MB |
| Attribution score | single author | 100ms | <5MB |
| Anomaly detection | baseline check | 75ms | <5MB |

**Hardware profile:** CPU/RAM optimized, 0% GPU usage

---

## Example: Complete Real-World Workflow

```python
"""
Real-world scenario: Monitoring a political influencer for coordinated 
inauthentic behavior (sockpuppet accounts posting in their style)
"""

from scribe_authorship import ScribeEngine

def monitor_influencer_network(influencer_id, suspect_account_texts):
    scribe = ScribeEngine()
    
    # Step 1: Get influencer's baseline profile
    influencer_baseline = scribe._get_author_profile(influencer_id)
    
    # Step 2: Check each suspect account for fingerprint match
    findings = []
    
    for account_id, texts in suspect_account_texts.items():
        combined_text = "\n".join(texts)
        
        # Method A: Pattern matching
        matches = scribe.compare_to_profiles(
            scribe.extract_linguistic_fingerprint(combined_text)
        )
        
        # Method B: Precise attribution
        score, _ = scribe.calculate_attribution_score(
            combined_text,
            influencer_id
        )
        
        if score > 80:
            findings.append({
                "status": "⚠️ SUSPECTED SOCKPUPPET",
                "account": account_id,
                "attribution_score": score,
                "confidence": "High",
                "action": "Flag for further investigation"
            })
        else:
            findings.append({
                "status": "✅ Independent author",
                "account": account_id,
                "attribution_score": score,
                "confidence": "Low match"
            })
    
    return findings
```

---

## Next Steps

1. **Build author profiles** - Feed representative texts from known authors
2. **Start with known sources** - Build confidence on verified profiles first
3. **Monitor for drift** - Use anomaly detection to catch style changes early
4. **Integrate with Beacon** - Add Scribe insights to your dashboard
5. **Validate manually** - Confirm high-confidence matches with domain experts

**Questions?** Refer to the code comments in `scribe_authorship.py` or run the demo:

```bash
python scribe_authorship.py
```
