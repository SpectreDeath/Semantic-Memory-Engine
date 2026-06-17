from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PROSE_DIR = Path("data/corpus/vought_baseline/pure_prose")
MANIFEST_PATH = PROSE_DIR / "wng_vought_manifest.json"
STAGING_DIR = Path("data/raw_cache/wng_prose")
AUTHOR = "Russell Vought"
SOURCE = "WORLD Opinions"

BOILERPLATE_PATTERNS = (
    "get markdown chrome extension",
    "harish garg",
    "markdown extracted by",
    "share this article",
    "comments",
    "newsletter",
    "subscribe",
    "footer",
    "header",
    "sidebar",
    "related",
    "popular",
    "trending",
    "search",
    "cookie",
    "social",
)

URL_RE = re.compile(r"https?://\S+")
SOURCE_URL_RE = re.compile(r"^\*\*URL:\*\*\s*(https?://\S+)", re.MULTILINE)
SOURCE_RE = re.compile(r"^\*\*Source:\*\*\s*(.+)$", re.MULTILINE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)")
IMAGE_RE = re.compile(r"!?\[[^\]]*\]\((?:[^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")
WORD_RE = re.compile(r"\b[\w’']+\b")


@dataclass
class LocalImportResult:
    source_path: str
    output_path: str
    title: str
    source_url: str
    status: str
    word_count: int
    error: str = ""


class LocalMarkdownProcessor:
    def __init__(self, staging_dir: Path = STAGING_DIR, prose_dir: Path = PROSE_DIR, manifest_path: Path = MANIFEST_PATH):
        self.staging_dir = staging_dir
        self.prose_dir = prose_dir
        self.manifest_path = manifest_path
        self.prose_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def process_batch(self) -> list[LocalImportResult]:
        manifest = self.load_manifest()
        results: list[LocalImportResult] = []

        for source_path in sorted(self.staging_dir.glob("*.md")):
            result = self.process_file(source_path, manifest)
            results.append(result)

        self.write_manifest(manifest)
        self.log_results(results)
        return results

    def load_manifest(self) -> dict[str, object]:
        if not self.manifest_path.exists():
            return {"source": "WORLD Opinions Russell Vought author archive", "seed_url": "https://wng.org/authors/russ-vought", "articles": []}

        with self.manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        if not isinstance(manifest, dict):
            return {"source": "WORLD Opinions Russell Vought author archive", "seed_url": "https://wng.org/authors/russ-vought", "articles": []}

        manifest.setdefault("source", "WORLD Opinions Russell Vought author archive")
        manifest.setdefault("seed_url", "https://wng.org/authors/russ-vought")
        manifest.setdefault("articles", [])
        return manifest

    def write_manifest(self, manifest: dict[str, object]) -> None:
        articles = manifest.get("articles")
        if isinstance(articles, list):
            manifest["total"] = len(articles)
        manifest["processed_local_markdown_at"] = datetime.now(UTC).isoformat()
        self.manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    def process_file(self, source_path: Path, manifest: dict[str, object]) -> LocalImportResult:
        try:
            raw_text = source_path.read_text(encoding="utf-8")
            cleaned_body = self.clean_markdown_content(raw_text)
            if self.is_waf_challenge(cleaned_body):
                return LocalImportResult(
                    source_path=str(source_path),
                    output_path="",
                    title=self.title_from_filename(source_path),
                    source_url="",
                    status="blocked_waf",
                    word_count=0,
                    error="Local markdown contains AWS WAF human-verification challenge text",
                )

            word_count = len(WORD_RE.findall(cleaned_body))
            if word_count == 0:
                return LocalImportResult(
                    source_path=str(source_path),
                    output_path="",
                    title=self.title_from_filename(source_path),
                    source_url="",
                    status="empty",
                    word_count=0,
                    error="No extractable prose found after cleaning",
                )

            raw_source = self.extract_source(raw_text)
            raw_source_url = self.extract_source_url(raw_text)
            matched_entry = self.match_manifest_entry(source_path, cleaned_body, raw_source_url, manifest)
            source_url = str(matched_entry.get("url", "")) if matched_entry else raw_source_url
            source = str(matched_entry.get("source", raw_source)) if matched_entry else raw_source
            title = self.extract_title(raw_text, source_path, matched_entry)
            target_path = self.prose_dir / self.output_filename(source_path)
            target_path.write_text(self.build_output_markdown(title, source, source_url, cleaned_body), encoding="utf-8")

            if matched_entry:
                matched_entry["status"] = "success_local_markdown"
                matched_entry["word_count"] = word_count
                matched_entry["local_path"] = str(target_path)
                matched_entry["output_path"] = str(target_path)
                matched_entry["title"] = title
                matched_entry["source"] = source
                matched_entry["error"] = ""
            else:
                self.add_new_manifest_entry(manifest, title, source, source_url, word_count, target_path)

            return LocalImportResult(
                source_path=str(source_path),
                output_path=str(target_path),
                title=title,
                source_url=source_url,
                status="success_local_markdown",
                word_count=word_count,
            )
        except UnicodeDecodeError as exc:
            return LocalImportResult(
                source_path=str(source_path),
                output_path="",
                title=self.title_from_filename(source_path),
                source_url="",
                status="error",
                word_count=0,
                error=str(exc),
            )

    def clean_markdown_content(self, text: str) -> str:
        text = FRONTMATTER_RE.sub("", text)
        text = re.sub(r"^#\s+.+$", "", text, count=1, flags=re.MULTILINE)
        text = re.sub(r"^\*\*(By|Source|URL|Saved):\*\*\s*.+$", "", text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r"^---\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^_Markdown extracted by .*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
        text = MARKDOWN_LINK_RE.sub(r"\1", text)
        text = URL_RE.sub("", text)
        text = IMAGE_RE.sub("", text)
        for pattern in BOILERPLATE_PATTERNS:
            text = re.sub(re.escape(pattern), "", text, flags=re.IGNORECASE)
        text = re.sub(r"^\s*[*#_-]{2,}\s*$", "", text, flags=re.MULTILINE)
        text = WHITESPACE_RE.sub(" ", text)
        return text.strip()

    def is_waf_challenge(self, text: str) -> bool:
        haystack = text[:12000].lower()
        return any(marker in haystack for marker in ("human verification", "javascript is disabled", "aws waf", "captcha", "gokuprops"))

    def match_manifest_entry(self, source_path: Path, cleaned_body: str, source_url: str, manifest: dict[str, object]) -> dict[str, object]:
        slug = self.slug(source_path.stem)
        title_guess = self.title_from_filename(source_path)
        candidates = [slug, title_guess.lower(), self.slug(title_guess)]
        articles = manifest.get("articles", [])
        if not isinstance(articles, list):
            return {}

        for entry in articles:
            if not isinstance(entry, dict):
                continue
            url = str(entry.get("url", "")).lower()
            title = str(entry.get("title", "")).lower()
            if source_url and source_url.lower() == url:
                return entry
            if any(candidate and candidate in url for candidate in candidates):
                return entry
            if any(candidate and candidate in title for candidate in candidates):
                return entry
            if title_guess.lower() in title or slug in title:
                return entry
        return {}

    def add_new_manifest_entry(self, manifest: dict[str, object], title: str, source: str, source_url: str, word_count: int, target_path: Path) -> None:
        articles = manifest.setdefault("articles", [])
        if not isinstance(articles, list):
            manifest["articles"] = []
            articles = manifest["articles"]
        articles.insert(0, {
            "title": title,
            "source": source,
            "url": source_url,
            "post_date": "",
            "author": AUTHOR,
            "local_path": str(target_path),
            "output_path": str(target_path),
            "word_count": word_count,
            "status": "success_local_markdown",
            "error": "",
        })

    def build_output_markdown(self, title: str, source: str, source_url: str, cleaned_body: str) -> str:
        frontmatter = [
            "---",
            f"source: {self.escape_yaml(source)}",
            f"source_url: {source_url}",
            f"author: {AUTHOR}",
            f"title: {self.escape_yaml(title)}",
            f"processed_at: {datetime.now(UTC).isoformat()}",
            "---",
            "",
            f"# {title}",
            "",
            cleaned_body,
            "",
        ]
        return "\n".join(frontmatter)

    def extract_source(self, raw_text: str) -> str:
        match = SOURCE_RE.search(raw_text)
        return self.clean_text(match.group(1)) if match else SOURCE

    def extract_source_url(self, raw_text: str) -> str:
        match = SOURCE_URL_RE.search(raw_text)
        return match.group(1) if match else ""

    def extract_title(self, raw_text: str, source_path: Path, matched_entry: dict[str, object]) -> str:
        if matched_entry and matched_entry.get("title"):
            return str(matched_entry["title"])
        heading_match = re.search(r"^#\s+(.+)$", raw_text, flags=re.MULTILINE)
        if heading_match:
            return self.clean_text(heading_match.group(1))
        return self.title_from_filename(source_path)

    def output_filename(self, source_path: Path) -> Path:
        stem = source_path.stem
        if not stem.startswith("wng_processed_"):
            stem = f"wng_processed_{stem}"
        return Path(f"{stem}.md")

    def title_from_filename(self, source_path: Path) -> str:
        stem = source_path.stem
        stem = re.sub(r"^wng_processed_", "", stem)
        stem = stem.replace("_", " ").replace("-", " ")
        stem = re.sub(r"\s+\d{10}$", "", stem)
        return self.clean_text(stem).title()

    def slug(self, value: str) -> str:
        slug = value.lower().replace("_", "-").replace(" ", "-")
        slug = re.sub(r"-{2,}", "-", slug)
        return slug.strip("-")

    def clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def escape_yaml(self, value: str) -> str:
        value = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{value}"' if any(char in value for char in ":#{}[]&*?|-<>=!%@`") else value

    def log_results(self, results: list[LocalImportResult]) -> None:
        if not results:
            logging.info("No markdown files found in %s", self.staging_dir)
            return
        for result in results:
            if result.status == "success_local_markdown":
                logging.info("Synced %s -> %s words", result.output_path, result.word_count)
            else:
                logging.warning("Skipped %s: %s", result.source_path, result.status or result.error)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    processor = LocalMarkdownProcessor()
    processor.process_batch()


if __name__ == "__main__":
    main()
