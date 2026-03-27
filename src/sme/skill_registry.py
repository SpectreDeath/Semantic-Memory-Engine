"""
Skill Registry Builder for SME

Parses SKILL.md specification files and builds a searchable JSON registry
that maps skill names to their SME source modules.
"""

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillMetadata:
    """Metadata extracted from a SKILL.md specification file."""

    name: str
    domain: str
    version: str
    complexity: str
    type: str
    category: str
    source_file: str
    source_exists: bool
    spec_path: str
    purpose: str
    description: str
    workflow: list = field(default_factory=list)
    source: str | None = None
    implementation_status: str = "unknown"


class SkillRegistryBuilder:
    """Builds a skill registry from SKILL.md specification files."""

    def __init__(self, skills_dir: str = "skills", sme_root: str = "."):
        self.skills_dir = Path(skills_dir)
        self.sme_root = Path(sme_root)

    def _parse_yaml_frontmatter(self, content: str) -> dict[str, str]:
        """Extract YAML frontmatter fields from SKILL.md content."""
        metadata = {}
        if not content.startswith("---"):
            return metadata

        parts = content.split("---", 2)
        if len(parts) < 3:
            return metadata

        frontmatter = parts[1]
        for line in frontmatter.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                if value:
                    metadata[key] = value

        return metadata

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content from a ## section header."""
        pattern = rf"## {re.escape(section_name)}\s*\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_workflow(self, content: str) -> list[str]:
        """Extract workflow steps from the Workflow section."""
        workflow_text = self._extract_section(content, "Workflow")
        if not workflow_text:
            return []

        steps = []
        for line in workflow_text.split("\n"):
            line = line.strip()
            # Match numbered steps like "1. **Step Name**: Description"
            match = re.match(r"\d+\.\s+\*\*(.+?)\*\*", line)
            if match:
                steps.append(match.group(1))
            elif line and not line.startswith("#"):
                # Plain numbered list
                match = re.match(r"\d+\.\s+(.+)", line)
                if match:
                    steps.append(match.group(1))
        return steps

    def _check_source_exists(self, source_file: str) -> bool:
        """Check if the referenced source file/directory exists in the SME."""
        if not source_file:
            return False

        # Normalize path separators
        source_path = Path(source_file.replace("/", os.sep).replace("\\", os.sep))

        # Check relative to SME root
        full_path = self.sme_root / source_path
        if full_path.exists():
            return True

        # Check without leading src/
        if str(source_path).startswith("src" + os.sep):
            alt_path = self.sme_root / source_path
            if alt_path.exists():
                return True

        # Check in extensions/
        if str(source_path).startswith("extensions" + os.sep):
            alt_path = self.sme_root / source_path
            if alt_path.exists():
                return True

        # Check in gateway/
        if str(source_path).startswith("gateway" + os.sep):
            alt_path = self.sme_root / source_path
            if alt_path.exists():
                return True

        return False

    def parse_skill_file(self, skill_path: Path) -> SkillMetadata | None:
        """Parse a single SKILL.md file and extract metadata."""
        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception:
            return None

        fm = self._parse_yaml_frontmatter(content)

        name = fm.get("name", skill_path.stem)
        domain = fm.get("domain", "SME_INTEGRATION")
        version = fm.get("version", "1.0.0")
        complexity = fm.get("complexity", "Unknown")
        skill_type = fm.get("type", "Tool")
        category = fm.get("category", "General")
        source_file = fm.get("source_file", "")
        source = fm.get("source", None)

        # Extract body sections
        purpose = self._extract_section(content, "Purpose")
        description = self._extract_section(content, "Description")
        workflow = self._extract_workflow(content)

        source_exists = self._check_source_exists(source_file)
        impl_status = "verified" if source_exists else "source_not_found"

        return SkillMetadata(
            name=name,
            domain=domain,
            version=version,
            complexity=complexity,
            type=skill_type,
            category=category,
            source_file=source_file,
            source_exists=source_exists,
            spec_path=str(skill_path),
            purpose=purpose[:200] if purpose else "",
            description=description[:200] if description else "",
            workflow=workflow,
            source=source,
            implementation_status=impl_status,
        )

    def build_registry(self) -> list[dict[str, Any]]:
        """Build the complete skill registry from all SKILL.md files."""
        registry = []

        if not self.skills_dir.exists():
            return registry

        for skill_file in sorted(self.skills_dir.glob("*.md")):
            if skill_file.name == "registry.json":
                continue
            metadata = self.parse_skill_file(skill_file)
            if metadata:
                registry.append(asdict(metadata))

        return registry

    def validate_skills(self) -> dict[str, list[str]]:
        """Validate all skills and return issues found."""
        issues: dict[str, list[str]] = {
            "missing_source": [],
            "missing_purpose": [],
            "missing_description": [],
            "missing_workflow": [],
            "parse_errors": [],
        }

        if not self.skills_dir.exists():
            issues["parse_errors"].append(f"Skills directory not found: {self.skills_dir}")
            return issues

        for skill_file in sorted(self.skills_dir.glob("*.md")):
            if skill_file.name == "registry.json":
                continue

            metadata = self.parse_skill_file(skill_file)
            if metadata is None:
                issues["parse_errors"].append(f"Failed to parse: {skill_file.name}")
                continue

            if not metadata.source_exists:
                issues["missing_source"].append(f"{metadata.name}: {metadata.source_file}")
            if not metadata.purpose:
                issues["missing_purpose"].append(metadata.name)
            if not metadata.description:
                issues["missing_description"].append(metadata.name)
            if not metadata.workflow:
                issues["missing_workflow"].append(metadata.name)

        return issues

    def export_registry(self, output_path: str = "skills/registry.json") -> int:
        """Build and export the registry to a JSON file. Returns entry count."""
        registry = self.build_registry()

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, default=str)

        return len(registry)

    def generate_report(self) -> dict[str, Any]:
        """Generate a summary report of the skill registry."""
        registry = self.build_registry()
        issues = self.validate_skills()

        categories: dict[str, int] = {}
        complexities: dict[str, int] = {}
        types: dict[str, int] = {}
        verified = 0

        for skill in registry:
            cat = skill.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1

            comp = skill.get("complexity", "Unknown")
            complexities[comp] = complexities.get(comp, 0) + 1

            typ = skill.get("type", "Unknown")
            types[typ] = types.get(typ, 0) + 1

            if skill.get("source_exists"):
                verified += 1

        return {
            "total_skills": len(registry),
            "verified_sources": verified,
            "unverified_sources": len(registry) - verified,
            "categories": categories,
            "complexities": complexities,
            "types": types,
            "issues": {k: len(v) for k, v in issues.items()},
            "total_issues": sum(len(v) for v in issues.values()),
        }


import os


def main():
    """CLI entry point for building the skill registry."""
    import argparse

    parser = argparse.ArgumentParser(description="Build SME skill registry")
    parser.add_argument(
        "--skills-dir", default="skills", help="Directory containing SKILL.md files"
    )
    parser.add_argument("--sme-root", default=".", help="SME repository root directory")
    parser.add_argument("--output", default="skills/registry.json", help="Output registry path")
    parser.add_argument("--report", action="store_true", help="Print summary report")
    parser.add_argument("--validate", action="store_true", help="Print validation issues")

    args = parser.parse_args()

    builder = SkillRegistryBuilder(args.skills_dir, args.sme_root)

    if args.validate:
        issues = builder.validate_skills()
        for category, items in issues.items():
            if items:
                print(f"\n{category} ({len(items)}):")
                for item in items[:10]:
                    print(f"  - {item}")
                if len(items) > 10:
                    print(f"  ... and {len(items) - 10} more")
        return

    count = builder.export_registry(args.output)
    print(f"Registry built: {count} skills written to {args.output}")

    if args.report:
        report = builder.generate_report()
        print(f"\nVerified sources: {report['verified_sources']}/{report['total_skills']}")
        print(f"Total issues: {report['total_issues']}")
        print("\nCategories:")
        for cat, cnt in sorted(report["categories"].items()):
            print(f"  {cat}: {cnt}")


if __name__ == "__main__":
    main()
