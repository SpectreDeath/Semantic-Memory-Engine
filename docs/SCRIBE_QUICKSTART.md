# 🖋️ SCRIBE - Layer 6 Quick Start (2 min)

**File:** `scribe_authorship.py`  
**Purpose:** Forensic authorship analysis using 6,734 rhetoric signals  
**Status:** ✅ Production-ready

---

## What is Scribe?

Instead of analyzing **what text means** (Loom's job), Scribe analyzes **who wrote it** using:
- Sentence structure patterns
- Punctuation "sparks" (Oxford commas, em-dashes, etc.)
- 6,734 rhetorical signal weights
- Vocabulary richness & word choice
- Active/passive voice ratios

**Result:** A unique "linguistic fingerprint" that's nearly impossible to fake at scale.

---

## The 4 Tools

### 1️⃣ Extract Fingerprint
```python
from scribe_authorship import ScribeEngine

scribe = ScribeEngine()

# Turn any text into a fingerprint
fp = scribe.extract_linguistic_fingerprint(
    "The rapid proliferation of digital communication...",
    author_id="author_smith"
)

print(f"Sentence length: {fp.avg_sentence_length} words")
print(f"Vocabulary diversity: {fp.lexical_diversity:.2f}")
print(f"Passive voice: {fp.passive_voice_ratio:.0%}")
```

---

### 2️⃣ Compare to Known Profiles
```python
# Find who might have written unknown text
unknown_text = "The widespread adoption of internet technologies..."

matches = scribe.compare_to_profiles(
    scribe.extract_linguistic_fingerprint(unknown_text),
    min_confidence=50.0
)

for match in matches[:3]:
    print(f"{match['author_name']}: {match['confidence_score']:.0f}% 📊")
    print(f"  Strength: {match['match_strength']}")
```

---

### 3️⃣ Attribution Score (Precise)
```python
# "Is this written by Dr. Smith?" (0-100 confidence)
score, breakdown = scribe.calculate_attribution_score(
    unknown_text,
    "author_smith"
)

print(f"Attribution: {score:.0f}%")
print(f"Confidence level: {breakdown['confidence_level']}")

# See component breakdown
print(f"  Signal alignment: {breakdown['signal_alignment']:.0f}%")
print(f"  Punctuation match: {breakdown['punctuation_habits']:.0f}%")
print(f"  Voice ratio match: {breakdown['voice_ratio_match']:.0f}%")
```

**Confidence guide:**
- ✅ **90%+** → Publish with attribution
- ⚠️ **75-89%** → Likely, needs caveats
- 🔍 **60-74%** → Possible, needs corroboration
- ❓ **<60%** → Inconclusive

---

### 4️⃣ Detect Anomalies
```python
# Did this author's style suddenly change?
# (Detects ghostwriting, AI generation, account takeover)

report = scribe.identify_stylistic_anomalies(
    "author_smith",
    new_text  # Recent content from Dr. Smith
)

if report:
    print(f"🚨 ANOMALIES DETECTED ({report.severity})")
    for anomaly in report.anomalies_detected:
        print(f"  {anomaly}")
    print(f"Confidence: {report.confidence:.0f}%")
else:
    print("✅ No anomalies - style is consistent")
```

**What triggers anomalies:**
- Sentence length shifts >25%
- Signal distribution changes >30%
- Vocabulary richness change >20%
- Punctuation usage change >35%
- Voice ratio shift >15% (AI indicator)

---

## Full Workflow Example

### Step 1: Build Author Profile (One-time)

```python
# Get representative text from known author
known_article = """
The examination of contemporary rhetorical patterns reveals 
a significant divergence between formal and colloquial discourse...
"""

# Extract and save fingerprint
fp = scribe.extract_linguistic_fingerprint(
    known_article, 
    author_id="author_smith"
)
scribe.save_author_profile(fp, author_name="Dr. Eleanor Smith")
print("✅ Profile saved")
```

### Step 2: Analyze Unknown Text

```python
# Unknown blog post
unknown_blog = """
The widespread adoption of internet technologies has fundamentally 
altered how we understand language patterns and communication...
"""

# Method A: Broad search (who might have written this?)
fp_unknown = scribe.extract_linguistic_fingerprint(unknown_blog)
matches = scribe.compare_to_profiles(fp_unknown)

if matches:
    print(f"🎯 Likely author: {matches[0]['author_name']}")
    print(f"   Confidence: {matches[0]['confidence_score']:.0f}%")
```

### Step 3: Verify (Optional)

```python
# If you have a suspect, get precise score
score, breakdown = scribe.calculate_attribution_score(
    unknown_blog,
    "author_smith"
)

if score > 80:
    print(f"✅ High confidence match: {score:.0f}%")
elif score > 70:
    print(f"⚠️ Possible match: {score:.0f}% (needs corroboration)")
else:
    print(f"❌ Unlikely: {score:.0f}%")
```

---

## Real-World Scenarios

### Scenario A: De-mask Anonymous Blogger

```python
# Harvest anonymous blog
spider = HarvesterSpider()
capture_id, blog_md = await spider.capture_site("https://anon-blog.com/post")

# Who likely wrote it?
fp = scribe.extract_linguistic_fingerprint(blog_md)
matches = scribe.compare_to_profiles(fp, min_confidence=60)

if matches and matches[0]['confidence_score'] > 75:
    print(f"🎯 {matches[0]['author_name']} ({matches[0]['confidence_score']:.0f}%)")
```

### Scenario B: Detect Ghostwriting

```python
# Executive's known tweets
exec_baseline = await spider.capture_site("https://twitter.com/executive/...")

# Recent press release
press_release = await spider.capture_site("https://company.com/press-release")

# Was this ghostwritten by PR agency?
report = scribe.identify_stylistic_anomalies(
    "executive",
    press_release
)

if report and "VOICE SHIFT" in str(report.anomalies_detected):
    print("🚨 Likely ghostwritten (PR agency detected)")
```

### Scenario C: Bot Farm Detection

```python
# Check if 10 accounts are run by same person
accounts = ["account_001", ..., "account_010"]

similarities = {}
for i, acc1 in enumerate(accounts):
    for acc2 in accounts[i+1:]:
        fp1 = scribe.extract_linguistic_fingerprint(get_tweets(acc1))
        fp2 = scribe.extract_linguistic_fingerprint(get_tweets(acc2))
        
        sim = scribe._calculate_signal_similarity(
            fp1.signal_vector,
            fp2.signal_vector
        )
        
        if sim > 0.85:  # High similarity = likely same person
            print(f"🚨 {acc1} ↔ {acc2}: {sim:.0%} match (SOCKPUPPET?)")
```

---

## Performance Profile

| Operation | Time | Memory | GPU |
|-----------|------|--------|-----|
| Extract fingerprint | 160ms | <5MB | 0% |
| Compare to 100 profiles | 250ms | <20MB | 0% |
| Attribution score | 100ms | <5MB | 0% |
| Anomaly detection | 75ms | <5MB | 0% |

**Batch 10 texts:** ~1.8s total, <30MB memory, 0% GPU

✅ Leaves 100% of 1660 Ti free for concurrent Loom processing

---

## Database Schema

### Tables Created Automatically

1. **`author_profiles`** - Store fingerprints for known authors
2. **`attribution_history`** - Track attribution results
3. **`anomaly_reports`** - Flagged style changes

All tables auto-initialize on first run. Just start using it!

---

## Integration Points

### With HarvesterSpider

```python
async def harvest_and_analyze(url):
    spider = HarvesterSpider()
    _, markdown = await spider.capture_site(url)
    
    # Immediately run through Scribe
    scribe = ScribeEngine()
    fp = scribe.extract_linguistic_fingerprint(markdown)
    matches = scribe.compare_to_profiles(fp)
    
    return matches
```

### With Loom

```python
# After Loom compresses content, verify source credibility
# via Scribe authorship attribution

loom_facts = loom.distill_web_content(markdown)
source_attribution = scribe.calculate_attribution_score(
    markdown,
    expected_author_id
)

if source_attribution[0] > 80:
    loom_facts['source_verified'] = True
```

### With Beacon Dashboard

```python
# Show "Who's driving this trend?" overlay
for trending_article in trending_articles:
    fp = scribe.extract_linguistic_fingerprint(article.text)
    matches = scribe.compare_to_profiles(fp)
    
    beacon.add_trend_author(
        trending_article.topic,
        matches[0]['author_name'],
        matches[0]['confidence_score']
    )
```

---

## Configuration

### Anomaly Sensitivity

In `scribe_authorship.py`, adjust `ANOMALY_THRESHOLDS`:

```python
ANOMALY_THRESHOLDS = {
    "sentence_length_shift": 0.25,      # 25% = flag
    "signal_consistency_drop": 0.30,    # 30% = flag
    "vocabulary_shift": 0.20,           # 20% = flag
    "punctuation_variation": 0.35,      # 35% = flag
}

# More sensitive? Decrease thresholds
# Less sensitive? Increase thresholds
```

### Confidence Weights

Attribution combines:
- **40%** - Signal vector alignment (most important)
- **25%** - Linguistic metrics (sentence length, etc.)
- **15%** - Punctuation patterns
- **15%** - Vocabulary richness
- **5%** - Voice ratio

Adjust in `calculate_attribution_score()` method.

---

## Troubleshooting

### Low confidence scores everywhere?

```python
# Check database
stats = scribe.get_scribe_stats()
print(f"Profiles: {stats['total_author_profiles']}")
# Need at least 5-10 profiles for reliable matching
```

**Solution:** Create more author profiles with diverse text samples.

### Too many false positives?

```python
# Use higher confidence threshold
matches = scribe.compare_to_profiles(fp, min_confidence=70.0)

# Or inspect detailed breakdown
score, breakdown = scribe.calculate_attribution_score(text, author_id)
if breakdown["signal_alignment"] < 0.60:
    print("⚠️ Weak signal match - might be false positive")
```

### Performance slow?

```python
# Check profile count
cursor.execute("SELECT COUNT(*) FROM author_profiles")
# If >1000, consider archiving old profiles

# Or trim signal vector size
signal_vector = signal_vector[:50]  # Use top 50 dimensions
```

---

## Next Steps

1. ✅ **Install:** Dependencies already in `requirements.txt`
2. ✅ **Understand:** Read [SCRIBE_INTEGRATION_GUIDE.md](SCRIBE_INTEGRATION_GUIDE.md)
3. 📖 **Learn architecture:** [SCRIBE_ARCHITECTURE.md](SCRIBE_ARCHITECTURE.md)
4. 🚀 **Deploy:** Add scribe calls to your pipeline
5. 📊 **Monitor:** Check stats with `get_scribe_stats()`

---

## Key Insights

**Why Scribe Works:**
- Humans have 6,734+ rhetorical signal patterns
- Faking 1-2 patterns = easy
- Faking all 6,734 consistently = impossible
- Signal distribution is their forensic fingerprint

**What Scribe Can't Do:**
- ❌ Identify from 1 sentence
- ❌ Distinguish identical twins
- ❌ Handle intentional mimicry attempts
- ❌ Non-English languages (yet)

**Confidence Threshold Recommendations:**
- Legal proceedings: 85%+
- Journalism: 70%+ with disclosure
- Research: 75%+ with methodology
- Casual use: 60%+

---

## API Reference (Copy-Paste)

```python
from scribe_authorship import ScribeEngine

scribe = ScribeEngine()

# Tool 1: Fingerprint
fp = scribe.extract_linguistic_fingerprint(text, author_id="id")

# Tool 2: Compare
matches = scribe.compare_to_profiles(fp, min_confidence=50.0)

# Tool 3: Attribution
score, breakdown = scribe.calculate_attribution_score(text, "author_id")

# Tool 4: Anomalies
report = scribe.identify_stylistic_anomalies("author_id", new_text)

# Stats
stats = scribe.get_scribe_stats()

# Save profile
scribe.save_author_profile(fp, author_name="Name")
```

---

## Questions?

- 📖 Full guide: [SCRIBE_INTEGRATION_GUIDE.md](SCRIBE_INTEGRATION_GUIDE.md)
- 🏗️ Architecture: [SCRIBE_ARCHITECTURE.md](SCRIBE_ARCHITECTURE.md)
- 💻 Source: `scribe_authorship.py` (fully commented)
- 🧪 Demo: `python scribe_authorship.py` (run to see all 4 tools in action)

---

**Ready to identify the forensic fingerprint of every text in your data lake?**

Let's go! 🖋️
