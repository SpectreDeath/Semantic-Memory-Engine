import json
import logging
import os
import re
from collections.abc import Callable
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("SME.CodeQuality")

SECRET_PATTERNS = [
    (r'api[_-]?key["\s:=]+["\']?sk[-_]?[a-zA-Z0-9]{20,}', "hardcoded API key", "critical"),
    (r'secret["\s:=]+["\']?[^"\s]{8,}', "hardcoded secret", "critical"),
    (r'password["\s:=]+["\']?[^"\s]{6,}', "hardcoded password", "critical"),
    (r'token["\s:=]+["\']?eyJ[a-zA-Z0-9_-]{10,}', "JWT token", "critical"),
    (r"-----BEGIN (RSA|PRIVATE|EC) KEY-----", "private key", "critical"),
]

SQL_INJECTION_PATTERNS = [
    (r'execute\s*\(\s*f["\'].*\{.*\}', "f-string SQL injection", "critical"),
    (r'\.format\s*\(\s*["\'].*\%', "format SQL injection", "critical"),
    (r'".*SELECT.*\$', "string interpolation SQL", "critical"),
]

PERFORMANCE_PATTERNS = [
    (r"for\s+\w+\s+in\s+\w+:\s*\n\s*for\s+\w+\s+in", "nested loops (potential N+1)", "warning"),
    (r"\.all\(\)\s*\n\s*for\s+", "loading all then iterating", "warning"),
    (r'db\.\w+\s*\(\s*f["\'].*\{.*\}', "query in loop", "warning"),
]

ERROR_HANDLING_PATTERNS = [
    (r"except:\s*\n\s*pass", "bare except with pass", "warning"),
    (r"except.*:\s*\n\s*pass", "exception swallowed", "warning"),
    (r"except.*:\s*\n\s*print", "exception printed only", "warning"),
]

CODE_COMPLEXITY_PATTERNS = [
    (r"if\s+.*\s+and\s+.*\s+and\s+.*\s+and\s+", "excessive conditions", "warning"),
    (r"else:\s*\n\s*if\s+.*:", "nested else-if chain", "warning"),
]


def scan_file(file_path: str) -> list[dict[str, Any]]:
    """Scan a single file for quality issues."""
    issues = []
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
    except Exception:
        return issues

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()

        for pattern, desc, severity in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(
                    {
                        "file": file_path,
                        "line": i,
                        "issue": desc,
                        "category": "security",
                        "severity": severity,
                        "code": line_stripped[:80],
                    }
                )

        for pattern, desc, severity in SQL_INJECTION_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(
                    {
                        "file": file_path,
                        "line": i,
                        "issue": desc,
                        "category": "security",
                        "severity": severity,
                        "code": line_stripped[:80],
                    }
                )

        for pattern, desc, severity in PERFORMANCE_PATTERNS:
            if re.search(pattern, line):
                issues.append(
                    {
                        "file": file_path,
                        "line": i,
                        "issue": desc,
                        "category": "performance",
                        "severity": severity,
                        "code": line_stripped[:80],
                    }
                )

        for pattern, desc, severity in ERROR_HANDLING_PATTERNS:
            if re.search(pattern, line):
                issues.append(
                    {
                        "file": file_path,
                        "line": i,
                        "issue": desc,
                        "category": "error_handling",
                        "severity": severity,
                        "code": line_stripped[:80],
                    }
                )

    return issues


class CodeQualityExtension(BasePlugin):
    """Enhanced code quality scanning extension."""

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Code Quality scanner initialized")

    def get_tools(self) -> list[Callable]:
        return [
            self.scan_security,
            self.scan_performance,
            self.scan_codebase,
            self.check_quality_report,
        ]

    async def scan_security(self, path: str = "src") -> str:
        """Scan for security vulnerabilities."""
        issues = []

        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith((".py", ".js", ".ts")):
                    file_path = os.path.join(root, file)
                    file_issues = scan_file(file_path)
                    issues.extend(file_issues)

        critical = [i for i in issues if i["severity"] == "critical"]
        warnings = [i for i in issues if i["severity"] == "warning"]

        return json.dumps(
            {
                "scan_type": "security",
                "total_issues": len(issues),
                "critical": len(critical),
                "warnings": len(warnings),
                "issues": issues[:20],
            },
            indent=2,
        )

    async def scan_performance(self, path: str = "src") -> str:
        """Scan for performance anti-patterns."""
        issues = []

        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    file_issues = scan_file(file_path)
                    perf_issues = [i for i in file_issues if i["category"] == "performance"]
                    issues.extend(perf_issues)

        return json.dumps(
            {"scan_type": "performance", "total_issues": len(issues), "issues": issues[:20]},
            indent=2,
        )

    async def scan_codebase(self, path: str = "src", category: str = "all") -> str:
        """Full codebase scan."""
        issues = []

        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                    file_path = os.path.join(root, file)
                    file_issues = scan_file(file_path)

                    if category != "all":
                        file_issues = [i for i in file_issues if i["category"] == category]

                    issues.extend(file_issues)

        critical = [i for i in issues if i["severity"] == "critical"]
        warnings = [i for i in issues if i["severity"] == "warning"]

        return json.dumps(
            {
                "scan_type": category,
                "total_issues": len(issues),
                "critical": len(critical),
                "warning": len(warnings),
                "issues": issues,
            },
            indent=2,
        )

    async def check_quality_report(self, path: str = "src") -> str:
        """Generate full quality report."""
        issues = []

        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    issues.extend(scan_file(file_path))

        by_category = {}
        by_severity = {"critical": 0, "warning": 0}

        for issue in issues:
            cat = issue["category"]
            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[issue["severity"]] += 1

        debt_hours = by_severity["critical"] * 2 + by_severity["warning"] * 0.5

        return json.dumps(
            {
                "quality_report": {
                    "total_issues": len(issues),
                    "by_category": by_category,
                    "by_severity": by_severity,
                    "technical_debt_hours": debt_hours,
                }
            },
            indent=2,
        )


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return CodeQualityExtension(manifest, nexus_api)
