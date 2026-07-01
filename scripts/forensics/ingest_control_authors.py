from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.robotparser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify as md

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RAW_DIR = PROJECT_ROOT / "data/raw_cache/control_raw"
OUTPUT_DIR = PROJECT_ROOT / "data/corpus/control_authors"
METADATA_DIR = PROJECT_ROOT / "data/metadata"
METADATA_CSV = METADATA_DIR / "control_author_sources.csv"
METADATA_JSON = METADATA_DIR / "control_author_sources.json"
USER_AGENT = "SME-Control-Author-Ingestion/1.0 (+https://github.com/Kilo-Org/kilocode)"
MIN_WORDS = 500
REQUEST_TIMEOUT = 30


@dataclass(frozen=True)
class SourceSpec:
    author: str
    title: str
    source: str
    url: str
    publication_date: str
    source_type: str
    project_2025_chapter: str
    output_stem: str


SOURCE_SPECS = [
    SourceSpec(
        author="Lindsey M. Burke",
        title="Lindsey Burke: Universal school choice is needed – Your address shouldn’t limit your child’s future",
        source="Fox News",
        url="https://www.foxnews.com/opinion/lindsey-burke-universal-school-choice-is-needed-separate-housing-from-education",
        publication_date="2019-08-30",
        source_type="signed_opinion",
        project_2025_chapter="Department of Education",
        output_stem="control_burke_prose_01",
    ),
    SourceSpec(
        author="Lindsey M. Burke",
        title="Lindsey Burke: Coronavirus school closings should prompt states to pay parents to educate kids in other ways",
        source="Fox News",
        url="https://www.foxnews.com/opinion/lindsey-burke-coronavirus-disruption-in-k-12-a-short-term-necessity-or-lasting-shift",
        publication_date="2020-03-28",
        source_type="signed_opinion",
        project_2025_chapter="Department of Education",
        output_stem="control_burke_prose_02",
    ),
    SourceSpec(
        author="Christopher C. Miller",
        title="US Army Special Forces Need To Go 'Back To Basics' For Great Power Competition",
        source="Task & Purpose",
        url="https://taskandpurpose.com/news/army-special-forces-back-to-basics-oped/",
        publication_date="2020-10-19",
        source_type="signed_op_ed",
        project_2025_chapter="Department of Defense",
        output_stem="control_miller_prose_01",
    ),
    SourceSpec(
        author="Christopher C. Miller",
        title="Statement for Committee on Oversight and Reform",
        source="DocumentCloud / U.S. House Committee on Oversight and Reform",
        url="https://s3.documentcloud.org/documents/20705853/christopher-c-miller-statement-5122021.pdf",
        publication_date="2021-05-12",
        source_type="signed_public_statement",
        project_2025_chapter="Department of Defense",
        output_stem="control_miller_prose_02",
    ),
    SourceSpec(
        author="Ken Cuccinelli",
        title="DeSantis is right: Rhetoric won’t stop cartels at our borders, only force",
        source="The Hill",
        url="https://digital-dev.thehill.com/opinion/immigration/4202741-desantis-is-right-rhetoric-wont-stop-cartels-at-our-borders-only-force/",
        publication_date="2023-09-15",
        source_type="signed_opinion",
        project_2025_chapter="Department of Homeland Security",
        output_stem="control_cuccinelli_prose_01",
    ),
    SourceSpec(
        author="Ken Cuccinelli",
        title="Abbott’s DC Caravan Gimmick Won’t Secure The Border, But This Will",
        source="The Federalist",
        url="https://thefederalist.com/2022/04/12/gov-abbotts-d-c-caravan-gimmick-wont-secure-the-border-heres-what-will/",
        publication_date="2022-04-12",
        source_type="signed_opinion",
        project_2025_chapter="Department of Homeland Security",
        output_stem="control_cuccinelli_prose_02",
    ),
]


def sanitize_author(author: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", author).strip("_").lower()
    return value or "unknown_author"


def robots_allowed(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return True
    return parser.can_fetch(USER_AGENT, url)


def fetch_bytes(url: str) -> bytes:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.content


def fetch_text(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(content)
    tmp_path.replace(path)


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def clean_markdown(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    drop_lines = {
        "Subscribe",
        "Sign In",
        "Ad-Free",
        "Related Topics",
        "More from",
        "Share",
        "Print",
        "Comment",
        "Show comments",
        "Hide comments",
        "Log In",
        "Register",
    }
    lines = []
    skip_next_author_bio = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped in drop_lines or stripped.startswith("©"):
            continue
        if stripped.startswith("By ") and " | " not in stripped and len(stripped) < 160:
            continue
        if stripped.startswith("-") and " is " in stripped and len(stripped) > 120:
            skip_next_author_bio = True
            continue
        if skip_next_author_bio:
            skip_next_author_bio = False
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for selector in [
        "script",
        "style",
        "noscript",
        "svg",
        "form",
        "header",
        "footer",
        "nav",
        "aside",
    ]:
        for tag in soup.select(selector):
            tag.decompose()
    for tag in soup.find_all(True):
        attrs = getattr(tag, "attrs", None) or {}
        classes = " ".join(attrs.get("class") or [])
        ident = str(attrs.get("id") or "")
        haystack = f"{classes} {ident}".lower()
        if any(
            token in haystack
            for token in [
                "advert",
                "sidebar",
                "newsletter",
                "related",
                "comment",
                "share",
                "bio",
                "author",
            ]
        ):
            if tag.name not in {"article", "main"}:
                tag.decompose()
    root = soup.find("article") or soup.find("main") or soup.body or soup
    for child in list(root.children):
        if isinstance(child, NavigableString) and not str(child).strip():
            child.extract()
    markdown = md(str(root), heading_style="ATX", bullets="-")
    return clean_markdown(markdown)


def extract_schema_article_body(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text("")
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        body_items: list[str] = []

        def collect(value: object, collected: list[str]) -> None:
            if isinstance(value, dict):
                article_body = value.get("ArticleBody")
                if isinstance(article_body, str) and article_body.strip():
                    collected.append(article_body.strip())
                for nested in value.values():
                    collect(nested, collected)
            elif isinstance(value, list):
                for nested in value:
                    collect(nested, collected)

        collect(data, body_items)
        if body_items:
            return clean_markdown("\n\n".join(body_items))
    return ""


def convert_html_to_markdown(html: str) -> str:
    markdown = html_to_markdown(html)
    if len(re.findall(r"\b\w+\b", markdown)) >= MIN_WORDS:
        return markdown
    schema_body = extract_schema_article_body(html)
    return schema_body or markdown


def pdf_to_markdown(pdf_path: Path) -> str:
    from markitdown import MarkItDown

    result = MarkItDown().convert(str(pdf_path))
    return clean_markdown(getattr(result, "text_content", str(result)))


def build_front_matter(
    spec: SourceSpec, retrieved_at: str, raw_path: Path, output_path: Path, word_count: int
) -> str:
    metadata = {
        "author": spec.author,
        "title": spec.title,
        "source": spec.source,
        "url": spec.url,
        "publication_date": spec.publication_date,
        "retrieved_at": retrieved_at,
        "source_type": spec.source_type,
        "project_2025_chapter": spec.project_2025_chapter,
        "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
        "output_path": str(output_path.relative_to(PROJECT_ROOT)),
        "word_count": word_count,
    }
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, str) and any(char in value for char in [":", "#", "\n"]):
            value = json.dumps(value, ensure_ascii=False)
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def process_source(spec: SourceSpec) -> dict[str, object]:
    author_dir = OUTPUT_DIR / sanitize_author(spec.author)
    output_path = author_dir / f"{spec.output_stem}.md"
    raw_path = RAW_DIR / f"{spec.output_stem}.raw"
    retrieved_at = datetime.now(timezone.utc).isoformat()  # noqa: UP017
    record: dict[str, object] = {
        "author": spec.author,
        "title": spec.title,
        "source": spec.source,
        "url": spec.url,
        "publication_date": spec.publication_date,
        "retrieved_at": retrieved_at,
        "source_type": spec.source_type,
        "project_2025_chapter": spec.project_2025_chapter,
        "output_path": str(output_path.relative_to(PROJECT_ROOT)),
        "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
        "status": "pending",
        "reason": "",
        "word_count": 0,
    }
    if output_path.exists():
        words = count_words(output_path.read_text(encoding="utf-8", errors="replace"))
        record.update(
            {"status": "skipped_existing", "reason": "output already exists", "word_count": words}
        )
        return record
    if not robots_allowed(spec.url):
        record.update({"status": "skipped_robots", "reason": "robots.txt disallows this URL"})
        return record
    try:
        if spec.url.lower().endswith(".pdf"):
            raw_bytes = fetch_bytes(spec.url)
            write_bytes_atomic(raw_path, raw_bytes)
            body = pdf_to_markdown(raw_path)
        else:
            html = fetch_text(spec.url)
            write_atomic(raw_path.with_suffix(".html"), html)
            raw_path.write_text(html, encoding="utf-8")
            body = convert_html_to_markdown(html)
        body = clean_markdown(body)
        words = re.findall(r"\b\w+\b", body)
        if len(words) < MIN_WORDS:
            record.update(
                {"status": "skipped_short", "reason": f"only {len(words)} words extracted"}
            )
            return record
        front_matter = build_front_matter(spec, retrieved_at, raw_path, output_path, len(words))
        write_atomic(output_path, front_matter + "\n\n" + body)
        record.update({"status": "success", "reason": "", "word_count": len(words)})
    except Exception as exc:
        record.update({"status": "failed", "reason": f"{type(exc).__name__}: {exc}"})
    return record


def write_metadata(records: list[dict[str, object]]) -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    with METADATA_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(records[0].keys()) if records else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    write_atomic(METADATA_JSON, json.dumps(records, indent=2, ensure_ascii=False))


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for index, spec in enumerate(SOURCE_SPECS):
        print(f"[{index + 1}/{len(SOURCE_SPECS)}] {spec.author} — {spec.title}")
        record = process_source(spec)
        records.append(record)
        print(f"  {record['status']}: {record['reason'] or record['output_path']}")
        time.sleep(1.0)
    write_metadata(records)
    print(
        f"\nMetadata written to {METADATA_CSV.relative_to(PROJECT_ROOT)} and {METADATA_JSON.relative_to(PROJECT_ROOT)}"
    )


if __name__ == "__main__":
    main()
