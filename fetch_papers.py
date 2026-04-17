"""Fetch latest papers from configured journal RSS feeds and build a daily digest.

If ANTHROPIC_API_KEY is set, each paper abstract is summarized in Korean using
Claude. Otherwise, the raw abstract from the feed is used.

Output: papers/YYYY-MM-DD.md
"""
from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

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


def summarize_with_claude(paper: Paper, client) -> str:
    prompt = (
        "다음은 학술 논문의 초록입니다. 비전공자도 이해할 수 있도록 "
        "3-4 문장의 한국어로 핵심 내용을 요약하세요. "
        "연구의 배경, 방법, 주요 발견, 의의 순서로 간결하게 작성하세요. "
        "불필요한 수식어는 제외하고 사실 위주로 서술하세요.\n\n"
        f"제목: {paper.title}\n"
        f"저널: {paper.journal}\n"
        f"초록: {paper.abstract or '(초록 없음)'}"
    )
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if block.type == "text").strip()


def build_summaries(papers: Iterable[Paper]) -> dict[str, str]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    summaries: dict[str, str] = {}
    if not api_key:
        print("[info] ANTHROPIC_API_KEY not set, falling back to raw abstracts", file=sys.stderr)
        for p in papers:
            summaries[p.link or p.title] = p.abstract or "(초록이 제공되지 않았습니다.)"
        return summaries

    try:
        import anthropic
    except ImportError:
        print("[warn] anthropic package not installed, using raw abstracts", file=sys.stderr)
        for p in papers:
            summaries[p.link or p.title] = p.abstract or "(초록이 제공되지 않았습니다.)"
        return summaries

    client = anthropic.Anthropic(api_key=api_key)
    for p in papers:
        key = p.link or p.title
        if not p.abstract:
            summaries[key] = "(초록이 제공되지 않았습니다.)"
            continue
        for attempt in range(3):
            try:
                summaries[key] = summarize_with_claude(p, client)
                break
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] summarize retry {attempt+1}: {exc}", file=sys.stderr)
                time.sleep(2 ** attempt)
        else:
            summaries[key] = p.abstract
    return summaries


def format_digest(date_kst: datetime, grouped: dict[str, list[Paper]], summaries: dict[str, str]) -> str:
    lines: list[str] = []
    lines.append(f"# 📚 일일 논문 다이제스트 — {date_kst.strftime('%Y-%m-%d')} (KST)")
    lines.append("")
    total = sum(len(v) for v in grouped.values())
    lines.append(f"**수집 저널 수**: {len(grouped)}개 · **논문 수**: {total}편")
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
            summary = summaries.get(p.link or p.title, p.abstract or "")
            lines.append(f"**요약**: {summary}")
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

    all_papers: list[Paper] = []
    grouped: dict[str, list[Paper]] = {}
    for entry in journals:
        name = entry["name"]
        url = entry["url"]
        print(f"[info] fetching: {name}", file=sys.stderr)
        papers = fetch_journal(name, url, per_journal_limit, cutoff)
        if not papers:
            continue
        grouped[name] = papers
        all_papers.extend(papers)

    if not all_papers:
        print("[info] no new papers found in lookback window", file=sys.stderr)

    summaries = build_summaries(all_papers)

    now_kst = datetime.now(KST)
    digest = format_digest(now_kst, grouped, summaries)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{now_kst.strftime('%Y-%m-%d')}.md"
    out_path.write_text(digest, encoding="utf-8")
    print(f"[done] wrote {out_path}", file=sys.stderr)

    latest = OUTPUT_DIR / "latest.md"
    latest.write_text(digest, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
