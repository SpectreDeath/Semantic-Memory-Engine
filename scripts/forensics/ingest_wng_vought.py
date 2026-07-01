from __future__ import annotations

import json
import re
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

BASE_URL = "https://wng.org/authors/russ-vought"
RAW_OUTPUT_DIR = Path("data/raw_cache/wng_prose")
CORPUS_MANIFEST_PATH = Path("data/corpus/vought_baseline/pure_prose/wng_vought_manifest.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}
FALLBACK_URLS = [
    "https://wng.org/opinions/taking-on-the-military-caste-1689596008",
    "https://wng.org/opinions/whos-in-charge-1656066567",
    "https://wng.org/opinions/the-government-doesnt-define-truth-nor-should-it-even-try-1652440359",
    "https://wng.org/opinions/the-rejection-of-double-minded-governing-1649678177",
    "https://wng.org/opinions/truth-is-not-hate-speech-1648126564",
    "https://wng.org/opinions/the-state-of-cultural-compromise-1647000330",
    "https://wng.org/opinions/cultural-fights-are-political-opportunities-1646311292",
    "https://wng.org/opinions/chambers-of-commerce-are-crippling-the-republican-party-1643975146",
    "https://wng.org/opinions/the-unfairness-of-fairness-for-all-1643112753",
    "https://wng.org/opinions/a-crippling-blow-to-legislative-overreach-1640090636",
    "https://wng.org/opinions/vought-on-debt-limit-1639747168",
    "https://wng.org/opinions/funding-battles-reveal-the-need-for-statesmanship-1638448532",
    "https://wng.org/opinions/a-boost-for-activist-bureaucracy-1636722419",
    "https://wng.org/opinions/point-its-time-to-rein-in-big-techs-power-1635333967",
    "https://wng.org/opinions/speaking-truth-to-power-is-now-domestic-terrorism-1633961445",
]

BOILERPLATE_PATTERNS = (
    "comment",
    "newsletter",
    "subscribe",
    "footer",
    "header",
    "nav",
    "sidebar",
    "related",
    "popular",
    "trending",
    "share",
    "account",
    "donate",
    "sign-in",
    "sign up",
    "search",
    "modal",
    "cookie",
    "ad",
    "social",
)


@dataclass
class ArticleResult:
    url: str
    title: str
    post_date: str
    author: str
    output_path: str
    word_count: int
    status: str
    error: str = ""


class WngOpinionIngestor:
    def __init__(
        self,
        output_dir: Path = RAW_OUTPUT_DIR,
        manifest_path: Path = CORPUS_MANIFEST_PATH,
        delay_seconds: float = 0.75,
    ):
        self.output_dir = output_dir
        self.manifest_path = manifest_path
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def crawl(self, max_pages: int = 20) -> list[ArticleResult]:
        urls = self.discover_article_urls(max_pages=max_pages)
        results: list[ArticleResult] = []
        for url in urls:
            result = self.fetch_article(url)
            results.append(result)
            time.sleep(self.delay_seconds)
        self.write_manifest(results)
        return results

    def discover_article_urls(self, max_pages: int) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        page = 1
        while page <= max_pages:
            author_url = BASE_URL if page == 1 else f"{BASE_URL}/p{page}"
            html = self.get_html(author_url)
            if self.is_waf_challenge(html):
                logger_message = (
                    f"WNG author page is blocked by WAF; using fallback URL list: {author_url}"
                )
                print(logger_message)
                return FALLBACK_URLS
            soup = BeautifulSoup(html, "html.parser")
            links = self.extract_article_links(soup)
            if not links:
                if page == 1:
                    print("No article links found on author page; using fallback URL list.")
                return FALLBACK_URLS
                break
            for link in links:
                if link not in seen:
                    seen.add(link)
                    urls.append(link)
            page += 1
        return urls

    def fetch_article(self, url: str) -> ArticleResult:
        try:
            html = self.get_html(url)
            if self.is_waf_challenge(html):
                return ArticleResult(
                    url=url,
                    title=self.title_from_url(url),
                    post_date="",
                    author="Russell Vought",
                    output_path="",
                    word_count=0,
                    status="blocked_waf",
                    error="WNG returned an AWS WAF human-verification challenge",
                )
            soup = BeautifulSoup(html, "html.parser")
            title = self.extract_title(soup, url)
            post_date = self.extract_post_date(soup)
            author = "Russell Vought"
            markdown = self.extract_article_markdown(soup, title)
            word_count = len(re.findall(r"\b\w+\b", markdown))
            output_path = self.output_dir / f"{self.slug(title)}-{self.url_hash(url)}.md"
            output_path.write_text(markdown, encoding="utf-8")
            return ArticleResult(
                url=url,
                title=title,
                post_date=post_date,
                author=author,
                output_path=str(output_path),
                word_count=word_count,
                status="success",
            )
        except Exception as exc:
            return ArticleResult(
                url=url,
                title=self.title_from_url(url),
                post_date="",
                author="Russell Vought",
                output_path="",
                word_count=0,
                status="error",
                error=str(exc),
            )

    def get_html(self, url: str) -> str:
        response = self.session.get(url, timeout=45)
        response.raise_for_status()
        return response.text

    def extract_article_links(self, soup: BeautifulSoup) -> list[str]:
        links: list[str] = []
        for anchor in soup.select("a[href^='/opinions/']"):
            href = anchor.get("href")
            if not href:
                continue
            url = urljoin("https://wng.org", href)
            if "/opinions/" in url and url not in links:
                links.append(url)
        return links

    def extract_title(self, soup: BeautifulSoup, url: str) -> str:
        h1 = soup.find("h1")
        if h1:
            return self.clean_text(h1.get_text(" ", strip=True))
        title = soup.title.string if soup.title else url
        return self.clean_text(title)

    def extract_post_date(self, soup: BeautifulSoup) -> str:
        text = self.clean_text(soup.get_text(" ", strip=True))
        match = re.search(r"Post Date:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
        if match:
            return match.group(1)
        match = re.search(r"([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
        return match.group(1) if match else ""

    def title_from_url(self, url: str) -> str:
        slug = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
        slug = re.sub(r"-\d{10}$", "", slug)
        return slug.replace("-", " ").title()

    def is_waf_challenge(self, html: str) -> bool:
        marker_text = html[:12000].lower()
        return any(
            marker in marker_text
            for marker in (
                "human verification",
                "javascript is disabled",
                "aws waf",
                "captcha",
                "gokuprops",
            )
        )

    def extract_article_markdown(self, soup: BeautifulSoup, title: str) -> str:
        root = soup.select_one("main") or soup
        self.remove_boilerplate(root)
        body = self.clean_markdown(
            md(root, heading_style="ATX", bullets="-", strip=["script", "style", "svg", "iframe"])
        )
        fetched_at = datetime.now(UTC).isoformat()
        frontmatter = [
            "---",
            "source: WORLD Opinions",
            "source_url: " + self.current_url_from_soup(soup, "https://wng.org"),
            "author: Russell Vought",
            "title: " + self.escape_yaml(title),
            "fetched_at: " + fetched_at,
            "---",
            "",
            f"# {title}",
            "",
        ]
        return "\n".join([*frontmatter, body])

    def current_url_from_soup(self, soup: BeautifulSoup, fallback: str) -> str:
        canonical = soup.select_one("link[rel='canonical']")
        if canonical and canonical.get("href"):
            return urljoin(fallback, canonical["href"])
        return fallback

    def remove_boilerplate(self, root: Tag) -> None:
        for tag in root.select("script, style, svg, noscript, iframe, form, button, link, meta"):
            tag.decompose()
        for tag in list(root.find_all(True)):
            haystack = " ".join(
                [
                    tag.name or "",
                    tag.get("id", ""),
                    tag.get("class", []).__str__(),
                    tag.get("aria-label", ""),
                ]
            ).lower()
            if any(pattern in haystack for pattern in BOILERPLATE_PATTERNS):
                tag.decompose()

    def clean_markdown(self, markdown: str) -> str:
        lines = []
        previous_blank = False
        for line in markdown.splitlines():
            line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
            line = re.sub(r"\[[^\]]*\]\((?:https?://wng\.org)?/opinions/[^\)]*\)", "", line)
            line = re.sub(r"^\s*[-*_]{3,}\s*$", "", line)
            line = line.strip()
            if not line:
                if not previous_blank:
                    lines.append("")
                    previous_blank = True
                continue
            lines.append(line)
            previous_blank = False
        return "\n".join(lines).strip() + "\n"

    def clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    def slug(self, text: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
        return slug[:80] or "untitled"

    def url_hash(self, url: str) -> str:
        import hashlib

        return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]

    def escape_yaml(self, value: str) -> str:
        return value.replace('"', "'")

    def write_manifest(self, results: Iterable[ArticleResult]) -> None:
        article_rows = [asdict(result) for result in results]
        payload = {
            "source": "WORLD Opinions Russell Vought author archive",
            "seed_url": BASE_URL,
            "fetched_at": datetime.now(UTC).isoformat(),
            "total": len(article_rows),
            "articles": article_rows,
        }
        self.manifest_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


if __name__ == "__main__":
    ingestor = WngOpinionIngestor()
    results = ingestor.crawl(max_pages=20)
    print(json.dumps([asdict(result) for result in results], indent=2, ensure_ascii=False))
