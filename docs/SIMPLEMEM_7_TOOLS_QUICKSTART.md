# ⚡ SimpleMem 7-Tool Suite - Quick Start Guide

Complete implementation of forensic authorship analysis + trend attribution platform with 7 integrated analysis tools.

## 🎯 The 7 Tools (In Recommended Order)

1. ✅ **HARVESTER SPIDER** - Web scraping (Layer 0)
2. ✅ **SCRIBE** - Forensic authorship (Layer 6)
3. ✅ **NETWORK ANALYZER** - Sockpuppet detection
4. ✅ **BEACON DASHBOARD** - Real-time visualization
5. ✅ **TREND CORRELATOR** - Trend attribution
6. ✅ **FACT VERIFIER** - Claim verification
7. ✅ **SCOUT** - Knowledge gap detection
8. ✅ **PIPELINE ORCHESTRATOR** - Workflow automation

---

## 🚀 Installation & Setup

### 1. Install Dependencies

```bash
cd d:\mcp_servers
pip install -r requirements.txt
```

**Required packages:**
- `crawl4ai` - Web scraping
- `numpy` - Vector operations
- `scipy` - Cosine similarity
- `nltk` - Text processing
- `plotly` - Visualization
- `dash` - Interactive dashboard

### 2. Initialize Databases

```python
import sqlite3
import os

# All tools auto-initialize their databases on first run
# Manual initialization optional:

from scribe_authorship import ScribeEngine
from network_analyzer import NetworkAnalyzer
from scout_integration import Scout

scribe = ScribeEngine()      # Creates scribe_profiles.sqlite
analyzer = NetworkAnalyzer()  # Creates network_profiles.sqlite
scout = Scout()              # Creates scout_gaps.sqlite
```

---

## 📖 5-Minute Tutorial

### Scenario: Analyze Breaking News Article

**Goal:** Extract author fingerprint, check for AI-generation, verify claims, identify gaps

```python
# ============================================================================
# STEP 1: HARVEST CONTENT
# ============================================================================

from harvester_spider import HarvesterSpider

spider = HarvesterSpider()

# Scrape an article
article = spider.capture_site("https://example.com/breaking-news")

print(f"✅ Captured: {article['title']}")
print(f"   Author: {article['author']}")
print(f"   Length: {len(article['content'])} chars")

# ============================================================================
# STEP 2: RUN FORENSIC ANALYSIS (SCRIBE)
# ============================================================================

from scribe_authorship import ScribeEngine

scribe = ScribeEngine()

# Extract author fingerprint
fingerprint = scribe.extract_linguistic_fingerprint(
    text=article['content'],
    author_id=article['author']
)

print(f"\n✅ Fingerprint extracted")
print(f"   Lexical diversity: {fingerprint.lexical_diversity:.2f}")
print(f"   Avg sentence length: {fingerprint.avg_sentence_length:.1f} words")

# Check for AI-generation (anomaly detection)
anomaly = scribe.identify_stylistic_anomalies(fingerprint)

print(f"\n✅ Anomaly detection")
print(f"   Status: {anomaly['classification']}")
print(f"   Confidence: {anomaly['confidence']:.1f}%")

if anomaly['is_anomalous']:
    print(f"   ⚠️ LIKELY AI-GENERATED TEXT")

# ============================================================================
# STEP 3: VERIFY CLAIMS (FACT VERIFIER)
# ============================================================================

from fact_verifier import FactVerifier

verifier = FactVerifier()

# Extract claims from article
claims = verifier.extract_claims(article['content'], article['author'])

print(f"\n✅ Extracted {len(claims)} claims")

# Verify each claim
verified_claims = []
for claim in claims[:5]:  # Check first 5
    result = verifier.verify_claim(claim)
    verified_claims.append(result)
    
    print(f"\n   Claim: {claim.claim_text[:60]}...")
    print(f"   Status: {result.status}")
    print(f"   Confidence: {result.confidence:.0f}%")

# ============================================================================
# STEP 4: IDENTIFY KNOWLEDGE GAPS (SCOUT)
# ============================================================================

from scout_integration import Scout

scout = Scout()

# Detect gaps in article
gaps = scout.detect_gaps_in_text(
    text=article['content'],
    auto_harvest=True  # Auto-trigger if complexity ≥ 70
)

print(f"\n✅ Detected {len(gaps)} knowledge gaps")

for gap in gaps[:3]:  # Show top 3
    print(f"\n   Gap: {gap.question[:80]}")
    print(f"   Complexity: {gap.complexity_score:.0f}%")
    print(f"   Urgency: {gap.urgency}")
    if gap.auto_harvest_triggered:
        print(f"   🚀 Auto-harvest triggered!")

# ============================================================================
# STEP 5: TREND ANALYSIS (TREND CORRELATOR)
# ============================================================================

from trend_correlator import TrendCorrelator

correlator = TrendCorrelator()

# If this article is about a trending topic
article_data = [{
    'author_id': article['author'],
    'text': article['content'],
    'timestamp': article['date'],
    'url': article['url']
}]

# Analyze if this is a trend driver
analysis = correlator.identify_trend_drivers(
    trend_topic="Breaking News Topic",
    article_data=article_data
)

if analysis.primary_drivers:
    print(f"\n✅ Trend analysis")
    for driver in analysis.primary_drivers[:3]:
        print(f"   {driver.author_name}: {driver.attribution_score:.1f}%")

print(f"\n   Coordinated promotion: {analysis.coordinated_promotion}")

# ============================================================================
# STEP 6: NETWORK ANALYSIS (NETWORK ANALYZER)
# ============================================================================

from network_analyzer import NetworkAnalyzer

analyzer = NetworkAnalyzer()

# Check if author has sockpuppet accounts
# (Requires multiple texts from multiple accounts)
account_texts = {
    article['author']: article['content'],
    "another_account": "text from another account",
    "third_account": "text from third account"
}

suspects = analyzer.detect_sockpuppets(account_texts)

if suspects:
    print(f"\n⚠️ SOCKPUPPET ALERT")
    for pair in suspects:
        print(f"   {pair['accounts'][0]} ↔ {pair['accounts'][1]}")
        print(f"   Match strength: {pair['match_strength']:.1f}%")
else:
    print(f"\n✅ No sockpuppets detected")

# ============================================================================
# STEP 7: AUTOMATED PIPELINE (ORCHESTRATOR)
# ============================================================================

from pipeline_orchestrator import PipelineOrchestrator
import asyncio

orchestrator = PipelineOrchestrator()

async def full_analysis():
    """Run complete pipeline"""
    execution = await orchestrator.execute_full_pipeline(
        input_url=article['url'],
        enable_stages=["HARVEST", "PROCESS", "ANALYSIS", "ENRICHMENT"]
    )
    
    return execution

# Run it
execution = asyncio.run(full_analysis())

print(f"\n✅ FULL PIPELINE COMPLETE")
print(f"   Execution ID: {execution.execution_id}")
print(f"   Duration: {execution.total_duration_seconds:.1f}s")
print(f"   Tasks: {execution.tasks_completed}/{execution.tasks_total}")
print(f"   Status: {execution.overall_status}")

# ============================================================================
# RESULTS SUMMARY
# ============================================================================

print("\n" + "="*80)
print("📊 ANALYSIS SUMMARY")
print("="*80)

summary = {
    "Article": article['title'][:50],
    "Author": article['author'],
    "AI Risk": f"{anomaly['confidence']:.1f}% (Anomalous)" if anomaly['is_anomalous'] else "✅ Human",
    "Verified Claims": sum(1 for r in verified_claims if r.verified),
    "Total Claims": len(claims),
    "Knowledge Gaps": len(gaps),
    "Sockpuppet Risk": "⚠️ Possible" if suspects else "✅ None",
    "Processing Time": f"{execution.total_duration_seconds:.1f}s"
}

for key, value in summary.items():
    print(f"{key:.<30} {value}")
```

---

## 🎨 Dashboard Visualization

### Start BEACON Dashboard

```python
from beacon_dashboard import BeaconDashboard

# Launch interactive dashboard
dashboard = BeaconDashboard(port=5000)
dashboard.start()

# Now open browser: http://localhost:5000
# Displays:
# - Author fingerprint networks
# - Real-time anomaly alerts
# - Trend driver rankings
# - Article timeline
# - Signal strength heatmap
```

---

## 💾 Working with Results

### Save Analysis Results

```python
import json
from datetime import datetime

# Compile complete analysis
analysis_result = {
    "timestamp": datetime.utcnow().isoformat(),
    "article": {
        "title": article['title'],
        "author": article['author'],
        "url": article['url']
    },
    "forensic_analysis": {
        "fingerprint_metrics": fingerprint.signal_weights,
        "anomaly_score": anomaly['confidence'],
        "classification": anomaly['classification']
    },
    "fact_verification": {
        "total_claims": len(claims),
        "verified": sum(1 for r in verified_claims if r.verified),
        "disputed": sum(1 for r in verified_claims if r.status == "Disputed")
    },
    "knowledge_gaps": [
        {
            "question": gap.question,
            "complexity": gap.complexity_score,
            "urgency": gap.urgency
        }
        for gap in gaps[:5]
    ],
    "network_analysis": {
        "sockpuppets_detected": len(suspects),
        "confidence": suspects[0]['match_strength'] if suspects else 0
    }
}

# Save to file
with open(f"analysis_{datetime.now().isoformat()}.json", "w") as f:
    json.dump(analysis_result, f, indent=2)

print("✅ Results saved to analysis_*.json")
```

### Query Historical Results

```python
import sqlite3

# Query Scribe database
conn = sqlite3.connect("d:\\mcp_servers\\storage\\scribe_profiles.sqlite")
cursor = conn.cursor()

# Get all authors analyzed
cursor.execute("SELECT DISTINCT author_id FROM attribution_history")
authors = cursor.fetchall()

print(f"✅ Analyzed {len(authors)} unique authors")

# Get anomalies detected
cursor.execute("""
    SELECT anomaly_type, COUNT(*) as count 
    FROM anomaly_reports 
    GROUP BY anomaly_type
""")

anomalies = cursor.fetchall()
print(f"✅ Anomalies detected: {sum(a[1] for a in anomalies)}")

conn.close()
```

---

## ⚙️ Advanced Usage

### Batch Processing

```python
# Analyze 100 articles in parallel

from harvester_spider import HarvesterSpider
from scribe_authorship import ScribeEngine

spider = HarvesterSpider()
scribe = ScribeEngine()

urls = [f"https://example.com/article-{i}" for i in range(100)]

# Parallel harvest
articles = spider.batch_capture(urls, max_workers=5)

print(f"✅ Harvested {len(articles)} articles")

# Parallel analysis
for article in articles:
    fingerprint = scribe.extract_linguistic_fingerprint(
        article['content'],
        author_id=article['author']
    )
    
    # Store results
    profile = scribe.get_or_create_author_profile(article['author'])
    print(f"✅ Analyzed: {article['author']}")

print(f"✅ Batch processing complete")
```

### Real-Time Monitoring

```python
# Monitor social media for breaking trends

from harvester_spider import HarvesterSpider
from trend_correlator import TrendCorrelator
from scribe_authorship import ScribeEngine
import time

spider = HarvesterSpider()
correlator = TrendCorrelator()
scribe = ScribeEngine()

print("🔎 Starting real-time trend monitor...")

while True:
    # Search for trending topics
    trending = spider.search_web("latest trending topics", max_results=10)
    
    # Analyze each trend
    for trend_url in trending:
        article = spider.capture_site(trend_url)
        
        # Quick fingerprint
        fp = scribe.extract_linguistic_fingerprint(article['content'])
        
        # Check for anomalies
        anomaly = scribe.identify_stylistic_anomalies(fp)
        
        if anomaly['is_anomalous']:
            print(f"\n⚠️ ANOMALY DETECTED")
            print(f"   URL: {trend_url[:60]}...")
            print(f"   Confidence: {anomaly['confidence']:.1f}%")
    
    print(f"✅ Monitoring active... (next check in 60s)")
    time.sleep(60)
```

### Custom Scoring

```python
# Create custom author reputation score

def calculate_author_score(author_id):
    """Custom scoring: consistency + fact accuracy + no anomalies"""
    
    verifier = FactVerifier()
    scribe = ScribeEngine()
    
    # Get author's claim history
    consistency = verifier.analyze_author_consistency(
        author_id=author_id,
        claim_history=[...]  # Get from database
    )
    
    # Get anomaly profile
    profile = scribe.get_or_create_author_profile(author_id)
    anomalies = profile.anomaly_count if profile else 0
    
    # Calculate score
    score = (
        (consistency.consistency_score * 0.5) +  # 50% consistency
        (100 - (anomalies * 2) * 0.3) +           # 30% no anomalies
        ((len(profile.attribution_history) / 10) * 0.2)  # 20% track record
    )
    
    return max(0, min(100, score))

# Score top authors
top_authors = ["alice", "bob", "charlie"]
for author in top_authors:
    score = calculate_author_score(author)
    print(f"{author}: {score:.0f}%")
```

---

## 🧪 Testing & Validation

### Run Complete Test Suite

```bash
# Run calibration test (validates core functionality)
python test_scribe.py

# Output:
# PHASE 1: Fingerprint Extraction ✅
# PHASE 2: Profile Comparison ✅
# PHASE 3: Anomaly Detection ✅
# PHASE 4: Author Attribution ✅
# PHASE 5: Batch Processing ✅
# PHASE 6: Profile Persistence ✅
```

### Performance Benchmarking

```python
import time
from scribe_authorship import ScribeEngine

scribe = ScribeEngine()
test_text = """
Long test text here (repeats many times)...
""" * 100

# Benchmark fingerprinting
start = time.time()
for _ in range(100):
    fp = scribe.extract_linguistic_fingerprint(test_text)
duration = time.time() - start

print(f"100 fingerprints in {duration:.2f}s")
print(f"Average: {duration/100*1000:.1f}ms per fingerprint")

# Benchmark comparison
profiles = []
for i in range(100):
    profiles.append(scribe.extract_linguistic_fingerprint(test_text))

start = time.time()
for _ in range(10):
    for profile in profiles:
        scribe.compare_to_profiles(test_text, f"author_{_}")
duration = time.time() - start

print(f"\n100 profile comparisons in {duration:.2f}s")
print(f"Average: {duration/100:.3f}s per comparison")
```

---

## 🎯 Common Use Cases

### Detect Disinformation Campaign

```python
# Monitor for coordinated posting by multiple accounts

from network_analyzer import NetworkAnalyzer
from fact_verifier import FactVerifier

analyzer = NetworkAnalyzer()
verifier = FactVerifier()

suspect_accounts = ["@user1", "@user2", "@user3", "@user4", "@user5"]
texts = {acc: get_posts(acc) for acc in suspect_accounts}

# Check 1: Sockpuppets
sockpuppets = analyzer.detect_sockpuppets(texts)
if sockpuppets:
    print("🚨 DISINFORMATION: Sockpuppet network detected")

# Check 2: Fact consistency
false_claims = 0
for account, text in texts.items():
    claims = verifier.extract_claims(text, account)
    for claim in claims:
        result = verifier.verify_claim(claim)
        if result.status == "Contradicted":
            false_claims += 1

if false_claims > len(texts) * 0.3:
    print("🚨 DISINFORMATION: High false claim rate")

# Check 3: Coordinated timing
coordination = analyzer.analyze_coordination_patterns(suspect_accounts)
if coordination.get('coordinated'):
    print("🚨 DISINFORMATION: Coordinated posting detected")
```

### Track Influencer Credibility

```python
# Build ongoing credibility profile for influencers

from fact_verifier import FactVerifier
from scribe_authorship import ScribeEngine

verifier = FactVerifier()
scribe = ScribeEngine()

influencer = "trusted_source"

# Track consistency over time
consistency = verifier.analyze_author_consistency(
    author_id=influencer,
    claim_history=get_historical_claims(influencer)
)

# Track anomalies
profile = scribe.get_or_create_author_profile(influencer)

credibility_score = {
    "consistency": consistency.consistency_score,
    "anomalies": len(profile.anomaly_reports) if profile else 0,
    "reliability": consistency.reliability_rating,
    "verified_claims": consistency.verified_claims
}

print(f"Influencer: {influencer}")
print(f"Credibility: {credibility_score['consistency']:.0f}%")
print(f"Reliability: {credibility_score['reliability']}")
```

---

## 📞 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'crawl4ai'"

**Solution:**
```bash
pip install crawl4ai
```

### Issue: "Database locked"

**Solution:**
```python
# Wait before next operation
import time
time.sleep(1)

# Or check for active connections
sqlite3.connect(db_path).close()
```

### Issue: "Fingerprint similarity is NaN"

**Solution:** This is expected for very short texts. Ensure minimum text length:
```python
if len(text) >= 200:  # Minimum 200 characters
    fingerprint = scribe.extract_linguistic_fingerprint(text)
```

---

## 📊 Next Steps

1. **Monitor your first author**: `python -c "from scribe_authorship import ScribeEngine; s = ScribeEngine(); print('Ready')"`
2. **Check dashboard**: Open http://localhost:5000 after starting BEACON
3. **Analyze your first article**: Copy-paste the 5-minute tutorial above
4. **Scale to production**: Set up logging, monitoring, alerts
5. **Extend analysis**: Add custom metrics, integrate external data sources

---

**SimpleMem 7-Tool Suite | Complete & Ready to Use** ✅
