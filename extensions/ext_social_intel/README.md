# 🕷️ Social Media Intelligence Crawler

**Advanced social media monitoring and disinformation detection system**

## 📋 **Overview**

The Social Media Intelligence Crawler is a comprehensive extension for the Semantic Memory Engine (SME) that provides advanced social media monitoring capabilities. It enables real-time tracking of disinformation campaigns, sentiment analysis, bot detection, and coordinated activity identification across multiple social media platforms.

## 🎯 **Key Capabilities**

### **🔍 Multi-Platform Monitoring**

- **Twitter/X**: Real-time tweet analysis and hashtag tracking
- **Reddit**: Subreddit monitoring and discussion analysis
- **Facebook**: Page and post monitoring (API-dependent)
- **YouTube**: Video and comment analysis
- **TikTok**: Short-form video content monitoring

### **📊 Advanced Analytics**

- **Sentiment Analysis**: Multi-language sentiment detection with bias analysis
- **Bot Detection**: Pattern recognition for automated accounts
- **Coordination Detection**: Identification of coordinated disinformation campaigns
- **Geographic Analysis**: Location-based content distribution mapping
- **Influencer Tracking**: Cross-platform influence pattern analysis

### **🛡️ Content Moderation**

- **NSFW Detection**: Automatic filtering of inappropriate content
- **Spam Prevention**: Advanced spam pattern recognition
- **Hate Speech Detection**: Comprehensive hate speech and toxic content identification
- **Quality Assessment**: Content quality and coherence evaluation

## 🏗️ **Architecture**

### **Core Components**

```
Social Media Intelligence Crawler
├── 📡 API Manager (api_manager.py)
│   ├── Multi-platform API integration
│   ├── Rate limiting and quota management
│   └── OAuth authentication handling
├── 🧠 Sentiment Analyzer (sentiment_analyzer.py)
│   ├── Multi-language sentiment analysis
│   ├── Bias detection and analysis
│   └── Cross-platform sentiment correlation
├── 🕵️ Campaign Detector (campaign_detector.py)
│   ├── Bot pattern detection
│   ├── Coordination pattern recognition
│   └── Risk assessment and scoring
└── 🛡️ Content Moderator (content_moderator.py)
    ├── NSFW content filtering
    ├── Spam detection
    └── User behavior analysis
```

### **Plugin Interface (plugin.py)**

- **Main Plugin Class**: `SocialIntelligenceCrawler`
- **Tool Registration**: 6 core tools for different analysis types
- **Configuration Management**: Dynamic configuration loading
- **Database Integration**: Campaign and user data persistence

## 🚀 **Quick Start**

### **Installation**

1. **Prerequisites**: Ensure SME v2.0.0+ is installed
2. **Extension Location**: Place the `ext_social_intel` folder in the SME extensions directory
3. **Dependencies**: Install required Python packages:

   ```bash
   pip install numpy>=1.21.0 aiohttp>=3.8.0 requests>=2.28.0
   ```

### **Configuration**

Create environment variables for API access:

```bash
# Twitter API credentials
export TWITTER_API_KEY="your_api_key"
export TWITTER_API_SECRET="your_api_secret"
export TWITTER_ACCESS_TOKEN="your_access_token"
export TWITTER_ACCESS_SECRET="your_access_secret"

# Reddit API credentials
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="SME-Bot/1.0"

# Facebook API credentials (if available)
export FACEBOOK_ACCESS_TOKEN="your_access_token"

# YouTube API credentials
export YOUTUBE_API_KEY="your_api_key"

# TikTok API credentials (if available)
export TIKTOK_ACCESS_TOKEN="your_access_token"
```

### **Basic Usage**

```python
# Import the extension
from extensions.ext_social_intel import SocialIntelligenceCrawler

# Initialize the crawler
crawler = SocialIntelligenceCrawler(manifest, nexus_api)

# Monitor a hashtag campaign
result = await crawler.monitor_hashtag_campaign(
    hashtag="climatechange",
    time_window=24,
    platforms=["twitter", "reddit"]
)

# Analyze sentiment spread
sentiment_result = await crawler.analyze_sentiment_spread(
    topic="election2024",
    platforms=["twitter", "facebook"],
    time_range=48
)

# Detect coordinated campaigns
coordination_result = await crawler.detect_coordinated_campaigns(
    keywords=["fake news", "conspiracy"],
    time_window=12
)
```

## 🛠️ **API Reference**

### **Core Tools**

#### **1. monitor_hashtag_campaign**

Track hashtag usage patterns and bot activity across specified platforms.

**Parameters:**

- `hashtag` (str): The hashtag to monitor (without # symbol)
- `time_window` (int): Time window in hours to analyze (default: 24)
- `platforms` (List[str]): List of platforms to monitor (default: all configured)

**Returns:**

```python
{
    "hashtag": "#climatechange",
    "time_window_hours": 24,
    "platforms_monitored": ["twitter", "reddit"],
    "total_posts": 1542,
    "unique_users": 891,
    "bot_activity_analysis": {
        "bot_score": 0.34,
        "suspicious_patterns": [...]
    },
    "sentiment_analysis": {
        "overall_sentiment": 0.23,
        "sentiment_breakdown": {...}
    },
    "status": "active"
}
```

#### **2. analyze_sentiment_spread**

Analyze sentiment propagation across platforms for a given topic.

**Parameters:**

- `topic` (str): Topic to analyze sentiment for
- `platforms` (List[str]): List of platforms to analyze
- `time_range` (int): Time range in hours to analyze (default: 48)

**Returns:**

```python
{
    "topic": "election2024",
    "time_range_hours": 48,
    "platforms_analyzed": ["twitter", "facebook"],
    "platform_sentiment": {
        "twitter": {...},
        "facebook": {...}
    },
    "cross_platform_correlation": 0.72,
    "sentiment_trends": {...}
}
```

#### **3. detect_coordinated_campaigns**

Identify coordinated disinformation campaigns using pattern recognition.

**Parameters:**

- `keywords` (List[str]): List of keywords to monitor for coordination
- `time_window` (int): Time window in hours to analyze (default: 24)
- `platforms` (List[str]): List of platforms to monitor

**Returns:**

```python
{
    "keywords": ["fake news", "conspiracy"],
    "coordination_analysis": {
        "coordination_score": 0.85,
        "detected_campaigns": [...]
    },
    "risk_assessment": {
        "risk_level": "HIGH",
        "risk_score": 0.78
    }
}
```

#### **4. track_influencer_activity**

Track activity and influence patterns of specific accounts.

**Parameters:**

- `influencer_handles` (List[str]): List of influencer handles to track
- `time_window` (int): Time window in hours to analyze (default: 168)

**Returns:**

```python
{
    "influencers_tracked": ["@example_user"],
    "influencer_data": {
        "@example_user": {
            "platform_data": {...},
            "influence_metrics": {...}
        }
    },
    "cross_platform_analysis": {...}
}
```

#### **5. analyze_geolocation_patterns**

Analyze geographic distribution and patterns of social media activity.

**Parameters:**

- `topic` (str): Topic to analyze geolocation patterns for
- `platforms` (List[str]): List of platforms to analyze

**Returns:**

```python
{
    "topic": "protest2024",
    "geolocation_analysis": {
        "geographic_distribution": {...},
        "anomaly_detection": {...}
    },
    "geographic_heatmap": {...}
}
```

#### **6. generate_social_media_report**

Generate comprehensive social media intelligence reports.

**Parameters:**

- `report_type` (str): Type of report to generate
- `parameters` (Dict): Parameters for the report generation

**Report Types:**

- `hashtag_analysis`: Comprehensive hashtag campaign analysis
- `sentiment_overview`: Cross-platform sentiment summary
- `coordination_assessment`: Coordinated campaign risk assessment
- `influencer_impact`: Influencer activity and impact analysis
- `geographic_distribution`: Geographic content distribution analysis

## 🔧 **Configuration**

### **Rate Limiting**

The extension includes intelligent rate limiting to prevent API abuse:

```json
{
  "rate_limits": {
    "twitter": 300,    // 300 requests per 15 minutes
    "reddit": 60,      // 60 requests per minute
    "facebook": 200,   // 200 requests per hour
    "youtube": 10000,  // 10,000 requests per day
    "tiktok": 1000     // 1000 requests per hour
  }
}
```

### **Moderation Thresholds**

Customizable thresholds for content moderation:

```json
{
  "moderation_thresholds": {
    "nsfw": 0.7,           // NSFW content threshold
    "spam": 0.6,           // Spam detection threshold
    "hate_speech": 0.5,    // Hate speech detection threshold
    "combined": 0.8        // Combined moderation threshold
  }
}
```

### **Coordination Detection**

Configurable thresholds for coordination pattern detection:

```json
{
  "coordination_thresholds": {
    "time_correlation": 0.7,     // Time correlation threshold
    "content_similarity": 0.6,   // Content similarity threshold
    "account_overlap": 0.3,      // Account overlap threshold
    "coordination_score": 0.7    // Overall coordination threshold
  }
}
```

## 🛡️ **Security & Privacy**

### **Data Protection**

- **Encryption**: AES-256 encryption for sensitive data
- **Anonymization**: Automatic user data anonymization
- **Retention**: Configurable data retention policies (default: 30 days)
- **Compliance**: GDPR and CCPA compliance support

### **API Security**

- **OAuth Integration**: Secure OAuth authentication for all platforms
- **Rate Limiting**: Intelligent rate limiting to prevent abuse
- **Error Handling**: Graceful error handling without data leakage
- **Audit Logging**: Comprehensive audit trails for all operations

## 📊 **Monitoring & Metrics**

### **Performance Metrics**

The extension provides comprehensive monitoring capabilities:

```python
# Available metrics
metrics = [
    "api_call_count",        # Total API calls made
    "error_rate",           # Error rate percentage
    "response_time",        # Average response time
    "moderation_decisions", # Content moderation decisions
    "coordination_detections" # Coordinated campaign detections
]
```

### **Alert System**

Configurable alerts for critical events:

```python
# Alert types
alerts = [
    "high_coordination_score",  # High coordination score detected
    "nsfw_content_detected",    # NSFW content detected
    "spam_campaign_detected",   # Spam campaign detected
    "api_rate_limit_exceeded"   # API rate limit exceeded
]
```

## 🧪 **Testing**

### **Unit Tests**

The extension includes comprehensive unit tests:

```bash
# Run all tests
python -m pytest extensions/ext_social_intel/tests/

# Run specific test module
python -m pytest extensions/ext_social_intel/tests/test_api_manager.py

# Run with coverage
python -m pytest extensions/ext_social_intel/tests/ --cov=extensions.ext_social_intel
```

### **Integration Tests**

Integration tests for end-to-end functionality:

```bash
# Run integration tests
python -m pytest extensions/ext_social_intel/tests/integration/

# Test specific platform integration
python -m pytest extensions/ext_social_intel/tests/integration/test_twitter_integration.py
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **API Authentication Errors**

```bash
# Check if API credentials are properly set
echo $TWITTER_API_KEY
echo $REDDIT_CLIENT_ID

# Verify credentials format
python -c "import os; print('Twitter API Key set:', bool(os.getenv('TWITTER_API_KEY')))"
```

#### **Rate Limiting Issues**

```python
# Check current rate limit status
from extensions.ext_social_intel.api_manager import SocialMediaAPIManager
manager = SocialMediaAPIManager()
print(f"Rate limit status: {manager.rate_limiters}")
```

#### **Content Moderation False Positives**

```python
# Adjust moderation thresholds
moderator = ContentModerator()
moderator.set_moderation_policy("nsfw_threshold", 0.8)  # Increase threshold
```

### **Debug Mode**

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export SME_DEBUG=1
```

## 📈 **Performance Optimization**

### **Caching Strategy**

The extension implements intelligent caching:

- **API Response Caching**: Cache API responses for 15 minutes
- **Content Analysis Caching**: Cache sentiment analysis results
- **User Profile Caching**: Cache user moderation profiles

### **Parallel Processing**

Optimized for parallel processing:

- **Async Operations**: All API calls are asynchronous
- **Concurrent Requests**: Multiple platform requests in parallel
- **Background Tasks**: Non-blocking background processing

### **Memory Management**

Efficient memory usage:

- **Streaming Processing**: Process large datasets in chunks
- **Garbage Collection**: Automatic cleanup of temporary data
- **Resource Limits**: Configurable memory and CPU limits

## 🤝 **Contributing**

### **Development Setup**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Add tests for your changes
5. Run the test suite: `python -m pytest`
6. Submit a pull request

### **Code Style**

Follow the project's code style:

- Use `black` for code formatting
- Use `flake8` for linting
- Write docstrings for all public functions
- Follow PEP 8 guidelines

### **Testing Requirements**

All contributions must include:

- Unit tests for new functionality
- Integration tests for API changes
- Documentation updates for public APIs
- Performance benchmarks for significant changes

## 📄 **License**

This extension is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

### **Documentation**

- [API Documentation](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

### **Community**

- [SME Discord Server](https://discord.gg/sme)
- [GitHub Issues](https://github.com/SpectreDeath/Semantic-Memory-Engine/issues)
- [Discussion Forum](https://github.com/SpectreDeath/Semantic-Memory-Engine/discussions)

### **Professional Support**

For enterprise support and custom development:

- Email: <support@semanticmemory.engine>
- Website: <https://semanticmemory.engine/enterprise>

## 🙏 **Acknowledgments**

This extension builds upon the excellent work of the open-source community:

- **Crawl4AI**: For web crawling capabilities
- **AIOHTTP**: For async HTTP requests
- **NumPy**: For numerical computations
- **NLTK**: For natural language processing

## 📝 **cSpell Configuration**

This document includes the following technical terms that may be flagged by spell checkers but are correct:

- `aiohttp`: Python library for asynchronous HTTP requests
- `NumPy`: Python numerical computing library
- `NLTK`: Natural Language Toolkit library
- `SME`: Semantic Memory Engine
- `API`: Application Programming Interface
- `OAuth`: Open standard for authorization
- `GDPR`: General Data Protection Regulation
- `CCPA`: California Consumer Privacy Act

## 📝 **Changelog**

### **v1.0.0** (Current)

- Initial release of Social Media Intelligence Crawler
- Multi-platform API integration
- Advanced sentiment analysis
- Bot and coordination detection
- Content moderation system
- Comprehensive monitoring and alerting

---

**🔗 Connect with us:**

- 📧 Email: <team@semanticmemory.engine>
- 🐦 Twitter: @SemanticMemory
- 💼 LinkedIn: Semantic Memory Engine
- 📸 Instagram: @semanticmemory.engine

**Made with ❤️ by the SME Team**
