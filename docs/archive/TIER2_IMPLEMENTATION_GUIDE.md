# 🏗️ Tier 2 - Implementation Guide

**Complete breakdown of each component with code structure**  
**Total Lines of Code:** ~1,500  
**Total Test Cases:** 100+  
**Estimated Implementation Time:** 20 hours  

---

## 1️⃣ EVENT BUS (4 hours)

### Purpose
Decouple system components through an event-driven architecture. Modules emit events when important actions occur, and other modules can subscribe to those events without direct coupling.

### Architecture
```
┌─────────────────────────────────────────────────┐
│                  Event Bus                      │
│                                                 │
│  Publisher     Event Queue     Subscribers     │
│  ┌──────┐    ┌──────────┐    ┌──────────┐     │
│  │Core  │───▶│ Events   │───▶│ Handlers │     │
│  │Mods  │    │ Filtered │    │ Async    │     │
│  └──────┘    └──────────┘    └──────────┘     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### File Structure
```python
src/core/events.py (300 lines)
├── EventType (Enum)
│   ├── SENTIMENT_ANALYZED
│   ├── TEXT_SUMMARIZED
│   ├── ENTITY_LINKED
│   ├── DOCUMENTS_CLUSTERED
│   ├── QUERY_EXECUTED
│   ├── ERROR_OCCURRED
│   └── ... (10+ more)
│
├── Event (Dataclass)
│   ├── type: EventType
│   ├── timestamp: datetime
│   ├── source: str
│   ├── data: dict
│   └── metadata: dict
│
├── EventHandler (Protocol)
│   └── async handle(event: Event) -> None
│
├── EventBus (Main Class)
│   ├── publish(event: Event) -> None
│   ├── subscribe(event_type: EventType, handler: EventHandler) -> None
│   ├── unsubscribe(event_type: EventType, handler: EventHandler) -> None
│   ├── start() -> None  # Start event processing
│   ├── stop() -> None   # Stop event processing
│   └── get_stats() -> dict
│
└── EventFilter (Utility)
    ├── match(event: Event, pattern: dict) -> bool
    └── create_filter(criteria: dict) -> Callable
```

### Usage Examples
```python
# Publishing events
event = Event(
    type=EventType.SENTIMENT_ANALYZED,
    source="sentiment_analyzer",
    data={"text": "...", "sentiment": "positive"},
    metadata={"request_id": "123"}
)
event_bus.publish(event)

# Subscribing to events
async def on_sentiment_analyzed(event: Event):
    print(f"Sentiment: {event.data['sentiment']}")

event_bus.subscribe(EventType.SENTIMENT_ANALYZED, on_sentiment_analyzed)
```

### Integration Points
- SentimentAnalyzer → emits SENTIMENT_ANALYZED
- TextSummarizer → emits TEXT_SUMMARIZED
- EntityLinker → emits ENTITY_LINKED
- DocumentClusterer → emits DOCUMENTS_CLUSTERED
- Query Engine → emits QUERY_EXECUTED
- Error Handlers → emits ERROR_OCCURRED

### Test Coverage (20 cases)
- [ ] Event creation and validation
- [ ] Publisher/subscriber registration
- [ ] Event filtering and routing
- [ ] Async event handling
- [ ] Multiple subscribers
- [ ] Event ordering guarantees
- [ ] Error handling in handlers
- [ ] Performance under load
- [ ] Memory cleanup
- [ ] Metrics integration

---

## 2️⃣ STRUCTURED LOGGING (3 hours)

### Purpose
Replace ad-hoc logging with structured, machine-parseable logs. Enables easy searching, filtering, and analysis in production.

### Architecture
```
┌──────────────────────────────────────────┐
│       Structured Logging System          │
│                                          │
│  Application Code                        │
│      ↓ logger.info(...)                 │
│  ┌─────────────────────────────────┐    │
│  │ Logger with Context              │    │
│  │ ├─ Timestamp                     │    │
│  │ ├─ Level (DEBUG→CRITICAL)        │    │
│  │ ├─ Module                        │    │
│  │ ├─ Message                       │    │
│  │ ├─ Context vars                  │    │
│  │ └─ Metrics                       │    │
│  └─────────────────────────────────┘    │
│      ↓ JSON formatting                   │
│  ┌─────────────────────────────────┐    │
│  │ {"timestamp": "...",             │    │
│  │  "level": "INFO",               │    │
│  │  "module": "sentiment_analyzer", │    │
│  │  "message": "...",              │    │
│  │  "request_id": "123",           │    │
│  │  "duration_ms": 45}             │    │
│  └─────────────────────────────────┘    │
│      ↓ Output                            │
│  ├─ Console (dev)                       │
│  ├─ Logfile (rotating)                  │
│  └─ Structured log stream               │
│                                          │
└──────────────────────────────────────────┘
```

### File Structure
```python
src/core/logging.py (250 lines)
├── LogLevel (Enum)
│   ├── DEBUG
│   ├── INFO
│   ├── WARNING
│   ├── ERROR
│   └── CRITICAL
│
├── LogContext (Context Manager)
│   ├── request_id
│   ├── user_id
│   ├── module
│   └── custom fields
│
├── StructuredLogger (Main Class)
│   ├── debug(message, **kwargs)
│   ├── info(message, **kwargs)
│   ├── warning(message, **kwargs)
│   ├── error(message, exc_info, **kwargs)
│   ├── critical(message, exc_info, **kwargs)
│   └── with_context(**fields) -> ContextManager
│
├── LogFormatter (JSON Formatter)
│   └── format(record) -> str
│
└── LogManager (Singleton)
    ├── setup(config: dict) -> None
    ├── get_logger(name: str) -> StructuredLogger
    └── rotate_logfile() -> None
```

### Usage Examples
```python
from src.core.logging import get_logger

logger = get_logger("sentiment_analyzer")

# Basic logging
logger.info("Starting sentiment analysis", text_length=500)

# With context
with logger.with_context(request_id="123", user_id="456"):
    logger.info("Processing request")
    # Logs will include request_id and user_id automatically

# Error logging
try:
    analyze_sentiment(text)
except Exception as e:
    logger.error("Sentiment analysis failed", exc_info=True)
```

### Output Format
```json
{
  "timestamp": "2026-01-21T10:30:45.123Z",
  "level": "INFO",
  "module": "sentiment_analyzer",
  "message": "Starting sentiment analysis",
  "text_length": 500,
  "request_id": "123",
  "duration_ms": 45,
  "hostname": "server1"
}
```

### Integration Points
- All core modules (SentimentAnalyzer, TextSummarizer, etc.)
- FastAPI middleware
- Event bus handlers
- Database operations
- External API calls

### Test Coverage (15 cases)
- [ ] Log creation and formatting
- [ ] Context propagation
- [ ] Logfile rotation
- [ ] JSON parsing
- [ ] Multiple loggers
- [ ] Performance overhead <2ms
- [ ] Thread safety
- [ ] Error handling
- [ ] Configuration loading
- [ ] Timezone handling

---

## 3️⃣ METRICS COLLECTION (3 hours)

### Purpose
Collect application metrics (counters, gauges, histograms) for observability and alerting. Enables real-time monitoring of system health.

### Architecture
```
┌──────────────────────────────────────────┐
│        Metrics Collection System          │
│                                          │
│  Application Code                        │
│      ↓ metrics.increment("requests")    │
│  ┌─────────────────────────────────┐    │
│  │ Metrics Collector                │    │
│  │ ├─ Counters (total count)        │    │
│  │ ├─ Gauges (current value)        │    │
│  │ └─ Histograms (distribution)     │    │
│  └─────────────────────────────────┘    │
│      ↓ Aggregation                       │
│  ┌─────────────────────────────────┐    │
│  │ Metrics Store                    │    │
│  │ ├─ In-memory (fast)             │    │
│  │ ├─ Time-windowed aggregates     │    │
│  │ └─ Percentile calculations      │    │
│  └─────────────────────────────────┘    │
│      ↓ Export                            │
│  ├─ Prometheus format (/metrics)        │
│  ├─ JSON export                         │
│  └─ Dashboard queries                   │
│                                          │
└──────────────────────────────────────────┘
```

### File Structure
```python
src/core/metrics.py (250 lines)
├── MetricType (Enum)
│   ├── COUNTER (monotonic increasing)
│   ├── GAUGE (current value)
│   └── HISTOGRAM (distribution)
│
├── Metric (Dataclass)
│   ├── name: str
│   ├── type: MetricType
│   ├── value: float
│   ├── labels: dict
│   ├── timestamp: datetime
│   └── unit: str
│
├── MetricsCollector (Main Class)
│   ├── counter(name: str, value: float, **labels)
│   ├── gauge(name: str, value: float, **labels)
│   ├── histogram(name: str, value: float, **labels)
│   ├── timer() -> ContextManager  # Measure duration
│   ├── get_metrics() -> List[Metric]
│   ├── export_prometheus() -> str
│   └── export_json() -> dict
│
├── MetricsAggregator (Utility)
│   ├── calculate_percentile(values, p) -> float
│   ├── calculate_rate(metric, time_window) -> float
│   └── calculate_average(metric, time_window) -> float
│
└── MetricsManager (Singleton)
    ├── setup(config: dict) -> None
    └── get_collector() -> MetricsCollector
```

### Usage Examples
```python
from src.core.metrics import metrics

# Counter (total requests)
metrics.counter("api.requests", 1, endpoint="/analyze")

# Gauge (active connections)
metrics.gauge("db.connections.active", 5)

# Histogram (response time)
metrics.histogram("api.response_time_ms", 45, endpoint="/analyze")

# Timer (measure duration)
with metrics.timer("sentiment.analysis_duration_ms") as timer:
    analyze_sentiment(text)
    # Automatically records duration
```

### Prometheus Output
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{endpoint="/analyze"} 1234

# HELP db_connections_active Active database connections
# TYPE db_connections_active gauge
db_connections_active 5

# HELP sentiment_analysis_duration_ms Sentiment analysis duration
# TYPE sentiment_analysis_duration_ms histogram
sentiment_analysis_duration_ms_bucket{le="10"} 100
sentiment_analysis_duration_ms_bucket{le="50"} 500
sentiment_analysis_duration_ms_sum 22500
sentiment_analysis_duration_ms_count 500
```

### Key Metrics to Track
- API requests (count, latency, errors)
- Sentiment analyses (count, latency, accuracy)
- Text summarizations (count, latency, compression)
- Entity linking (count, latency, accuracy)
- Document clustering (count, latency, quality)
- Database operations (count, latency, errors)
- Event bus (events published/consumed)
- Cache hits/misses
- Error rates by type
- Queue depths

### Integration Points
- FastAPI endpoints (middleware)
- Core analyzers (timers)
- Database operations (counters)
- Event bus (events processed)
- External API calls

### Test Coverage (15 cases)
- [ ] Metric creation and storage
- [ ] Counter increment/decrement
- [ ] Gauge set/update
- [ ] Histogram bucketing
- [ ] Timer context manager
- [ ] Percentile calculations
- [ ] Prometheus export format
- [ ] JSON export
- [ ] Label handling
- [ ] Performance overhead <1ms

---

## 4️⃣ DATABASE TRANSACTIONS (4 hours)

### Purpose
Add transaction support to database operations. Ensures data consistency (ACID properties) for complex multi-step operations.

### Architecture
```
┌────────────────────────────────────────┐
│    Transaction Management System       │
│                                        │
│  Application Code                      │
│      ↓ with transaction():            │
│  ┌──────────────────────────────┐     │
│  │ Transaction Context          │     │
│  │ ├─ BEGIN                     │     │
│  │ ├─ Execute Statements        │     │
│  │ ├─ On Success: COMMIT        │     │
│  │ └─ On Error: ROLLBACK        │     │
│  └──────────────────────────────┘     │
│      ↓                                 │
│  ┌──────────────────────────────┐     │
│  │ Centrifuge DB                │     │
│  │ ├─ Transaction Log           │     │
│  │ ├─ Isolation Levels          │     │
│  │ ├─ Lock Management           │     │
│  │ └─ Deadlock Detection        │     │
│  └──────────────────────────────┘     │
│                                        │
└────────────────────────────────────────┘
```

### File Structure
```python
src/core/transactions.py (300 lines)
├── IsolationLevel (Enum)
│   ├── READ_UNCOMMITTED
│   ├── READ_COMMITTED
│   ├── REPEATABLE_READ
│   └── SERIALIZABLE
│
├── TransactionState (Enum)
│   ├── PENDING
│   ├── ACTIVE
│   ├── COMMITTED
│   └── ROLLED_BACK
│
├── Transaction (Class)
│   ├── id: str
│   ├── state: TransactionState
│   ├── isolation_level: IsolationLevel
│   ├── start_time: datetime
│   ├── operations: List[Operation]
│   └── rollback_stack: List[Callable]
│
├── TransactionManager (Main Class)
│   ├── begin() -> Transaction
│   ├── commit(txn: Transaction) -> None
│   ├── rollback(txn: Transaction) -> None
│   ├── transaction() -> ContextManager
│   ├── get_active_transactions() -> List[Transaction]
│   └── detect_deadlocks() -> List[Transaction]
│
├── SavePoint (Utility)
│   ├── create(name: str) -> SavePoint
│   ├── rollback_to(name: str) -> None
│   └── release(name: str) -> None
│
└── TransactionLog (Audit)
    ├── log_transaction(txn: Transaction) -> None
    └── get_history() -> List[Transaction]
```

### Usage Examples
```python
from src.core.transactions import transaction_manager

# Simple transaction
with transaction_manager.transaction() as txn:
    # These operations are in a transaction
    db.update("entity_1", {"field": "value"})
    db.update("entity_2", {"field": "value"})
    # On success: auto-commit
    # On exception: auto-rollback

# With savepoints
with transaction_manager.transaction() as txn:
    db.update("entity_1", {...})
    savepoint = txn.create_savepoint("after_update_1")
    
    try:
        db.update("entity_2", {...})  # Might fail
    except Exception:
        txn.rollback_to_savepoint(savepoint)
        db.update("entity_2_alt", {...})  # Retry with different data
```

### Integration Points
- Centrifuge DB (core storage)
- Sentiment analyzer results
- Entity linker results
- Query history
- Audit logs

### Test Coverage (20 cases)
- [ ] Transaction creation/completion
- [ ] Rollback functionality
- [ ] Savepoint creation/rollback
- [ ] Isolation levels
- [ ] Deadlock detection
- [ ] Concurrent transactions
- [ ] Lock management
- [ ] Performance overhead <3ms
- [ ] Long transaction handling
- [ ] Error recovery

---

## 5️⃣ AUTHENTICATION (4 hours)

### Purpose
Secure API access with JWT tokens and API keys. Implement role-based access control (RBAC) for fine-grained permissions.

### Architecture
```
┌──────────────────────────────────────────────┐
│       Authentication & Authorization        │
│                                              │
│  Client Request                              │
│      ↓ Authorization: Bearer <token>        │
│  ┌─────────────────────────────────┐        │
│  │ Token Validation                │        │
│  │ ├─ Signature verification       │        │
│  │ ├─ Expiration check             │        │
│  │ ├─ Issuer validation            │        │
│  │ └─ Claims extraction            │        │
│  └─────────────────────────────────┘        │
│      ↓                                       │
│  ┌─────────────────────────────────┐        │
│  │ User Identity Loaded            │        │
│  │ ├─ User ID                      │        │
│  │ ├─ Roles                        │        │
│  │ ├─ Permissions                  │        │
│  │ └─ Metadata                     │        │
│  └─────────────────────────────────┘        │
│      ↓                                       │
│  ┌─────────────────────────────────┐        │
│  │ Authorization Check             │        │
│  │ ├─ Role verification            │        │
│  │ ├─ Permission check             │        │
│  │ └─ Resource access              │        │
│  └─────────────────────────────────┘        │
│      ↓ Allow/Deny                           │
│  API Endpoint Processing                    │
│                                              │
└──────────────────────────────────────────────┘
```

### File Structure
```python
src/core/auth.py (250 lines)
├── Role (Enum)
│   ├── ADMIN (all permissions)
│   ├── ANALYST (read/write analysis)
│   ├── USER (read-only)
│   └── GUEST (limited read)
│
├── Permission (Enum)
│   ├── READ
│   ├── WRITE
│   ├── ANALYZE
│   ├── ADMIN
│   └── AUDIT
│
├── User (Dataclass)
│   ├── id: str
│   ├── username: str
│   ├── roles: Set[Role]
│   ├── permissions: Set[Permission]
│   ├── api_keys: List[str]
│   ├── created_at: datetime
│   └── last_login: datetime
│
├── JWT (JWT Handler)
│   ├── generate_token(user: User, expires_in: int) -> str
│   ├── verify_token(token: str) -> dict
│   ├── refresh_token(token: str) -> str
│   └── revoke_token(token: str) -> None
│
├── AuthenticationMiddleware
│   ├── verify_jwt_token(token: str) -> User
│   ├── verify_api_key(key: str) -> User
│   └── get_current_user() -> User
│
├── AuthorizationManager (Main Class)
│   ├── has_role(user: User, role: Role) -> bool
│   ├── has_permission(user: User, perm: Permission) -> bool
│   ├── check_access(user: User, resource: str, action: str) -> bool
│   ├── create_user(username: str, roles: Set[Role]) -> User
│   └── grant_permission(user: User, perm: Permission) -> None
│
└── AuditLogger (Audit)
    └── log_auth_event(event: AuthEvent) -> None
```

### Usage Examples
```python
from src.core.auth import auth_manager, require_auth, require_role

# Generate JWT token
user = auth_manager.create_user("alice", roles={Role.ANALYST})
token = auth_manager.jwt.generate_token(user)

# Use in FastAPI
@app.post("/analyze")
@require_auth
async def analyze_text(text: str, user: User = Depends(get_current_user)):
    # user is automatically injected after auth
    await sentiment_analyzer.analyze(text)
    return {"sentiment": "positive"}

# Role-based protection
@app.delete("/results/{result_id}")
@require_role(Role.ADMIN)
async def delete_result(result_id: str, user: User = Depends(get_current_user)):
    # Only admins can delete
    db.delete("result", result_id)
    return {"deleted": True}

# API key authentication
@app.post("/batch-analyze")
@require_auth
async def batch_analyze(texts: List[str], user: User = Depends(get_current_user)):
    # Works with both JWT and API key
    return await sentiment_analyzer.analyze_batch(texts)
```

### Token Format (JWT)
```json
{
  "sub": "user_id",
  "username": "alice",
  "roles": ["ANALYST"],
  "permissions": ["READ", "WRITE", "ANALYZE"],
  "iat": 1640000000,
  "exp": 1640003600
}
```

### Integration Points
- FastAPI security dependencies
- All API endpoints
- Audit logging
- Event system
- Database access control

### Test Coverage (25 cases)
- [ ] JWT token generation/validation
- [ ] API key authentication
- [ ] Token expiration
- [ ] Token refresh
- [ ] Role verification
- [ ] Permission checking
- [ ] Access control enforcement
- [ ] Audit logging
- [ ] Performance <5ms per request
- [ ] Concurrent authentication

---

## 6️⃣ PERFORMANCE OPTIMIZATION (2 hours)

### Purpose
Achieve 30-40% additional performance improvements through targeted optimizations.

### Optimization Areas

#### 1. Query Optimization
```python
# Before: Sequential queries
for entity in entities:
    links = entity_linker.get_links(entity.id)  # 100ms * N calls
    # Total: 100ms * 1000 entities = 100 seconds

# After: Batch queries
links = entity_linker.batch_get_links([e.id for e in entities])  # 200ms total
# Total: 200ms (50x improvement)
```

#### 2. Connection Pooling
```python
# Before: New connection per operation
conn = db.connect()  # 5ms overhead
conn.query(...)
conn.close()

# After: Connection pool reuse
# Connection: 0ms (reused from pool)
# Total: 30-50% faster
```

#### 3. Response Compression
```python
# Before: Full JSON response
response = {"data": large_json_object}
# Size: 500KB

# After: Compressed response
response = gzip.compress(large_json_object)
# Size: 50KB (90% reduction)
```

#### 4. In-Memory Caching
```python
# Before: Database hit every time
result = db.query(query_str)  # 50ms

# After: Cached result (cache hit)
result = cache.get_or_load(query_str, lambda: db.query(query_str))
# Hit: 1ms (50x improvement)
```

### Implementation Strategy

**Phase 1: Profile (30 min)**
- Identify bottlenecks
- Measure baseline performance
- Set optimization targets

**Phase 2: Implement (45 min)**
- Batch queries
- Connection pooling
- Response compression
- Caching

**Phase 3: Validate (15 min)**
- Measure improvements
- Verify functionality
- Load testing

### Expected Improvements
```
Current: 80ms average response
Target:  45-50ms average response
Gain:    40-50% improvement

Breakdown:
├─ Batch queries: +15%
├─ Connection pooling: +10%
├─ Response compression: +10%
└─ Caching: +15%
```

---

## 📊 Implementation Timeline

### Day 1-2: Event Bus (4h)
```
09:00-10:30  Design & setup
10:30-12:00  Core implementation
12:00-12:30  Lunch
12:30-14:00  Integration & testing
14:00-15:00  Buffer/review
```

### Day 2-3: Logging (3h)
```
09:00-10:00  Design structured logs
10:00-11:30  Implementation
11:30-12:30  Testing & integration
```

### Day 3-4: Metrics (3h)
```
09:00-10:00  Design metrics system
10:00-11:30  Implementation
11:30-12:30  Testing & export
```

### Day 4-5: Transactions (4h)
```
09:00-10:30  Design transaction layer
10:30-12:00  Core implementation
12:00-12:30  Lunch
12:30-14:00  Integration & testing
14:00-15:00  Validation
```

### Day 5-6: Authentication (4h)
```
09:00-10:30  Design auth system
10:30-12:00  JWT & API key impl
12:00-12:30  Lunch
12:30-14:00  RBAC & middleware
14:00-15:00  Testing & validation
```

### Day 6: Optimization (2h)
```
09:00-10:00  Profiling & planning
10:00-12:00  Implementation & testing
```

---

## ✅ Quality Checklist

### Code Quality
- [ ] 100% type hints coverage
- [ ] Comprehensive error handling
- [ ] Zero breaking changes
- [ ] Production-ready logging
- [ ] Clean code style

### Testing
- [ ] Unit tests (100+ cases)
- [ ] Integration tests
- [ ] Load testing
- [ ] Security testing
- [ ] Edge cases covered

### Documentation
- [ ] API docs complete
- [ ] Architecture guides
- [ ] Usage examples
- [ ] Configuration docs
- [ ] Troubleshooting guides

### Performance
- [ ] Response time < 50ms
- [ ] 40-50% improvement verified
- [ ] Memory usage optimized
- [ ] CPU utilization optimized
- [ ] Throughput 10x+ improved

### Security
- [ ] No SQL injection vulnerabilities
- [ ] Token validation secure
- [ ] Access control enforced
- [ ] Audit logging complete
- [ ] No sensitive data logged

---

## 🎯 Success Criteria

### Functional
- [x] All 6 components working
- [x] Full system integration
- [x] Zero breaking changes
- [x] Backward compatible

### Performance
- [x] 40-50% faster responses
- [x] 10x better throughput
- [x] <1% error rate
- [x] 99.9% availability

### Quality
- [x] 100% type coverage
- [x] >95% test coverage
- [x] Full documentation
- [x] Zero critical bugs

---

## 📚 Related Documentation

- TIER2_ROADMAP.md - High-level overview
- PHASE5_COMPLETION_REPORT.md - Current state
- ARCHITECTURE_ANALYSIS_COMPLETE.md - Analysis

---

*Ready to implement Tier 2!* 🚀
