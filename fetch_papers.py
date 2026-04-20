"""Fetch latest papers from configured journal RSS feeds and build a daily digest.

The digest is written with the raw English abstracts from the feeds.
Korean translation is done separately by Claude Code via the
`/translate-digest` slash command (no LLM API key required).

Output: papers/YYYY-MM-DD.md
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import yaml

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "journals.yml"
OUTPUT_DIR = ROOT / "papers"
KST = timezone(timedelta(hours=9))


@dataclass
class Paper:
    journal: str
    title: str
    authors: str
    link: str
    published: datetime | None
    abstract: str


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_entry_date(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def fetch_journal(name: str, url: str, limit: int, cutoff: datetime | None) -> list[Paper]:
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": "daily-paper/1.0"})
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] {name}: fetch failed: {exc}", file=sys.stderr)
        return []

    if feed.bozo and not feed.entries:
        print(f"[warn] {name}: feed parse error: {feed.bozo_exception}", file=sys.stderr)
        return []

    papers: list[Paper] = []
    for entry in feed.entries:
        published = parse_entry_date(entry)
        if cutoff and published and published < cutoff:
            continue

        authors = ""
        if entry.get("authors"):
            authors = ", ".join(a.get("name", "") for a in entry.authors if a.get("name"))
        elif entry.get("author"):
            authors = entry.author

        abstract = strip_html(
            entry.get("summary")
            or entry.get("description")
            or (entry.get("content", [{}])[0].get("value") if entry.get("content") else "")
            or ""
        )

        papers.append(
            Paper(
                journal=name,
                title=strip_html(entry.get("title", "(제목 없음)")),
                authors=authors,
                link=entry.get("link", ""),
                published=published,
                abstract=abstract,
            )
        )
        if len(papers) >= limit:
            break
    return papers


def format_digest(date_kst: datetime, grouped: dict[str, list[Paper]]) -> str:
    lines: list[str] = []
    lines.append(f"# 📚 일일 논문 다이제스트 — {date_kst.strftime('%Y-%m-%d')} (KST)")
    lines.append("")
    total = sum(len(v) for v in grouped.values())
    lines.append(f"**수집 저널 수**: {len(grouped)}개 · **논문 수**: {total}편")
    lines.append("")
    lines.append(
        "> 영문 초록은 RSS 원본입니다. Claude Code 에서 `/translate-digest` 로 한국어 요약을 채워 넣으세요."
    )
    lines.append("")
    lines.append("## 목차")
    for journal in grouped:
        anchor = re.sub(r"[^a-z0-9가-힣\- ]", "", journal.lower()).replace(" ", "-")
        lines.append(f"- [{journal}](#{anchor}) ({len(grouped[journal])}편)")
    lines.append("")

    for journal, papers in grouped.items():
        lines.append(f"## {journal}")
        lines.append("")
        for p in papers:
            lines.append(f"### {p.title}")
            meta = []
            if p.authors:
                meta.append(f"**저자**: {p.authors}")
            if p.published:
                meta.append(f"**게재일**: {p.published.astimezone(KST).strftime('%Y-%m-%d')}")
            if p.link:
                meta.append(f"[원문 링크]({p.link})")
            if meta:
                lines.append(" · ".join(meta))
                lines.append("")
            lines.append(f"**Abstract (EN)**: {p.abstract or '(초록이 제공되지 않았습니다.)'}")
            lines.append("")
            lines.append("**한국어 요약**: _대기 중 — `/translate-digest` 실행 시 채워집니다._")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    config = load_config()
    journals = config.get("journals", [])
    per_journal_limit = int(config.get("per_journal_limit", 5))
    lookback_days = int(config.get("lookback_days", 2))

    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    grouped: dict[str, list[Paper]] = {}
    for entry in journals:
        name = entry["name"]
        url = entry["url"]
        print(f"[info] fetching: {name}", file=sys.stderr)
        papers = fetch_journal(name, url, per_journal_limit, cutoff)
        if papers:
            grouped[name] = papers

    if not grouped:
        print("[info] no new papers found in lookback window", file=sys.stderr)

    now_kst = datetime.now(KST)
    digest = format_digest(now_kst, grouped)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{now_kst.strftime('%Y-%m-%d')}.md"
    out_path.write_text(digest, encoding="utf-8")
    print(f"[done] wrote {out_path}", file=sys.stderr)

    latest = OUTPUT_DIR / "latest.md"
    latest.write_text(digest, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
