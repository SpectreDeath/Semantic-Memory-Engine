---
name: code-quality
description: "Enhanced code quality checks beyond basic linting. Triggers: 'code quality', 'security scan', 'best practices', 'refactor suggestions', 'technical debt'. NOT for: syntax errors (use ruff), formatting (use ruff format)."
---

# Code Quality Enhancement

Extended code quality and security checks for the SME project.

## When to Use This Skill

Use this skill when:
- Security vulnerability scanning
- Best practice recommendations
- Technical debt identification
- Architecture quality评估
- Performance anti-patterns detection

Do NOT use this skill when:
- Basic linting (use `ruff check`)
- Formatting issues (use `ruff format`)
- Type checking (use mypy)

## Check Categories

### 1. Security Checks

- Hardcoded secrets detection
- SQL injection patterns
- Command injection
- Unvalidated redirects
- Weak cryptography

### 2. Performance Anti-patterns

- N+1 query detection
- Unnecessary loop iterations
- Inefficient data structures
- Memory leaks (open handles)

### 3. Architecture Quality

- Circular dependencies
- God classes/functions
- Missing abstractions
- Tight coupling

### 4. Best Practices

- Error handling completeness
- Logging standards
- Documentation coverage
- Test coverage gaps

## Input Format

```yaml
quality_request:
  action: string      # "scan", "report", "refactor_plan"
  path: string      # File or directory to analyze
  category: string # "security", "performance", "architecture", "all"
  severity: string # "critical", "warning", "info"
```

## SME Project Patterns

### Hardcoded Secrets (Critical)
```python
# BAD
api_key = "sk_live_xxx"
password = "admin123"

# GOOD - use environment
api_key = os.environ.get("API_KEY")
```

### N+1 Queries (Warning)
```python
# BAD
for user in users:
    posts = db.query(f"SELECT * FROM posts WHERE user_id = {user.id}")

# GOOD
posts = db.query("SELECT * FROM posts WHERE user_id IN (?)", [u.id for u in users])
```

### Error Handling (Warning)
```python
# BAD
try:
    something()
except:
    pass

# GOOD
try:
    something()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
```

## Output Format

```yaml
quality_report:
  issues:
    - file: string
      line: integer
      issue: string
      category: security|performance|architecture
      severity: critical|warning|info
      suggestion: string
  summary:
    critical_count: integer
    warning_count: integer
    info_count: integer
  technical_debt_hours: float
```

## Integration

Runs via `ruff check` then adds:
- Custom security rules
- Performance heuristics
- Architecture checks