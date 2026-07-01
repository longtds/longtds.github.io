#!/usr/bin/env python3
"""Generate /news pages for the MkDocs handbook.

功能:
- 从 RSS/Atom 技术源抓取云原生 / AI 基础设施 / AIOps / 可观测性相关新闻
- 为每篇文章生成本地内容页: docs/news/YYYY-MM-DD/<slug>.md
- 重建 docs/news/index.md，按文章日期从新到旧排序
- 可选执行 mkdocs build、git commit、push

依赖: Python 3.11 stdlib only。
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import html
import os
import re
import subprocess
import sys
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
NEWS_DIR = DOCS / "news"
INDEX_FILE = NEWS_DIR / "index.md"

SOURCES = [
    ("Kubernetes Blog", "https://kubernetes.io/feed.xml"),
    ("CNCF Blog", "https://www.cncf.io/feed/"),
    ("CNCF News", "https://www.cncf.io/news/feed/"),
    ("The New Stack", "https://thenewstack.io/feed/"),
    ("NVIDIA Technical Blog", "https://developer.nvidia.com/blog/feed/"),
    ("AWS Containers Blog", "https://aws.amazon.com/blogs/containers/feed/"),
    ("AWS ML Blog", "https://aws.amazon.com/blogs/machine-learning/feed/"),
    ("Google Cloud Blog", "https://cloudblog.withgoogle.com/rss/"),
    ("Red Hat Blog", "https://www.redhat.com/en/rss/blog"),
]

KEYWORDS = [
    # Cloud native
    "kubernetes", "k8s", "cncf", "cloud native", "container", "containers", "docker", "helm", "istio",
    "linkerd", "envoy", "argo", "gitops", "platform engineering", "serverless", "ebpf", "cilium",
    # AI infra / LLMOps
    "ai", "llm", "genai", "inference", "vllm", "sglang", "kserve", "llm-d", "ray", "kueue", "kaito",
    "gpu", "nvidia", "cuda", "tensorrt", "model", "agent", "mcp", "rag", "mlops", "llmops",
    # AIOps / observability
    "aiops", "observability", "opentelemetry", "otel", "prometheus", "grafana", "sre", "incident",
    "anomaly", "apm", "tracing", "metrics", "logs",
    # Infra / hardware
    "datacenter", "data center", "dpu", "cxl", "rdma", "infiniband", "liquid cooling", "confidential computing",
    # Chinese
    "云原生", "容器", "可观测", "智能运维", "大模型", "推理", "算力", "数据中心", "液冷", "信创",
]

DOMAIN_RULES = [
    ("云原生", ["kubernetes", "k8s", "cncf", "cloud native", "container", "docker", "helm", "istio", "linkerd", "envoy", "argo", "gitops", "platform engineering", "cilium", "serverless", "云原生", "容器"]),
    ("AI 基础设施", ["llm", "genai", "inference", "vllm", "sglang", "kserve", "llm-d", "ray", "kueue", "kaito", "gpu", "nvidia", "cuda", "tensorrt", "model", "agent", "mcp", "rag", "mlops", "llmops", "大模型", "推理", "算力"]),
    ("AIOps / 可观测性", ["aiops", "observability", "opentelemetry", "otel", "prometheus", "grafana", "sre", "incident", "anomaly", "apm", "tracing", "metrics", "logs", "可观测", "智能运维"]),
    ("数据中心 / 硬件", ["datacenter", "data center", "dpu", "cxl", "rdma", "infiniband", "liquid cooling", "confidential computing", "数据中心", "液冷", "信创"]),
]


@dataclass
class Article:
    title: str
    url: str
    source: str
    published: dt.datetime
    summary: str
    domain: str


def now_cn() -> dt.datetime:
    return dt.datetime.now(TZ)


def strip_html(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def text_of(elem: ET.Element | None) -> str:
    if elem is None:
        return ""
    return strip_html("".join(elem.itertext()))


def child(elem: ET.Element, name: str) -> ET.Element | None:
    for c in list(elem):
        if c.tag.split("}")[-1] == name:
            return c
    return None


def children(elem: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in list(elem) if c.tag.split("}")[-1] == name]


def parse_date(value: str) -> dt.datetime:
    value = (value or "").strip()
    if not value:
        return now_cn()
    try:
        d = email.utils.parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(TZ)
    except Exception:
        pass
    try:
        value2 = value.replace("Z", "+00:00")
        d = dt.datetime.fromisoformat(value2)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(TZ)
    except Exception:
        return now_cn()


def classify(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    for domain, words in DOMAIN_RULES:
        if any(w.lower() in text for w in words):
            return domain
    return "技术动态"


def relevant(article: Article) -> bool:
    text = f"{article.title} {article.summary}".lower()
    return any(k.lower() in text for k in KEYWORDS)


def fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "longtds-tech-handbook-news-bot/1.0 (+https://longtds.github.io)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_feed(source: str, url: str) -> list[Article]:
    try:
        raw = fetch(url)
    except Exception as e:
        print(f"[warn] fetch failed: {source}: {e}", file=sys.stderr)
        return []
    try:
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"[warn] parse failed: {source}: {e}", file=sys.stderr)
        return []

    articles: list[Article] = []
    # RSS items
    for item in root.findall(".//item"):
        title = text_of(child(item, "title"))
        link = text_of(child(item, "link"))
        pub = text_of(child(item, "pubDate")) or text_of(child(item, "date"))
        summary = text_of(child(item, "description")) or text_of(child(item, "summary"))
        if title and link:
            articles.append(Article(title, link, source, parse_date(pub), summary[:700], classify(title, summary)))

    # Atom entries (namespace agnostic via manual traversal)
    for entry in [e for e in root.iter() if e.tag.split("}")[-1] == "entry"]:
        title = text_of(child(entry, "title"))
        link = ""
        for l in children(entry, "link"):
            href = l.attrib.get("href")
            rel = l.attrib.get("rel", "alternate")
            if href and rel in ("alternate", ""):
                link = href
                break
        if not link:
            link = text_of(child(entry, "link"))
        pub = text_of(child(entry, "published")) or text_of(child(entry, "updated"))
        summary = text_of(child(entry, "summary")) or text_of(child(entry, "content"))
        if title and link:
            articles.append(Article(title, link, source, parse_date(pub), summary[:700], classify(title, summary)))
    return articles


def slugify(title: str, url: str) -> str:
    ascii_title = title.encode("ascii", "ignore").decode("ascii").lower()
    ascii_title = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    if not ascii_title:
        ascii_title = "article"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{ascii_title[:70].strip('-')}-{digest}"


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").strip()


def article_path(article: Article) -> Path:
    day = article.published.strftime("%Y-%m-%d")
    return NEWS_DIR / day / f"{slugify(article.title, article.url)}.md"


def read_existing_urls() -> set[str]:
    urls: set[str] = set()
    if not NEWS_DIR.exists():
        return urls
    for p in NEWS_DIR.rglob("*.md"):
        if p.name == "index.md":
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.search(r"^url:\s*(.+)$", s, flags=re.M)
        if m:
            urls.add(m.group(1).strip())
    return urls


def write_article(article: Article) -> Path:
    p = article_path(article)
    p.parent.mkdir(parents=True, exist_ok=True)
    date_s = article.published.strftime("%Y-%m-%d %H:%M %Z")
    summary = article.summary or "RSS/Atom 源未提供摘要，请点击原文查看完整内容。"
    content = f"""<!-- news-meta
created_by: generate_daily_news.py
date: {article.published.isoformat()}
source: {article.source}
domain: {article.domain}
url: {article.url}
-->

# {article.title}

| 字段 | 内容 |
|:---|:---|
| 日期 | {date_s} |
| 领域 | {article.domain} |
| 来源 | {article.source} |
| 原文 | [打开原文]({article.url}) |

## 摘要

{summary}

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 原文为外部来源，本站仅做技术动态归档与摘要索引，完整信息以原文为准。

[返回新闻列表](../index.md)
"""
    p.write_text(content, encoding="utf-8")
    return p


def parse_meta(path: Path) -> dict[str, str] | None:
    try:
        s = path.read_text(encoding="utf-8")
    except Exception:
        return None
    block = re.search(r"<!-- news-meta\n([\s\S]*?)\n-->", s)
    if not block:
        return None
    meta: dict[str, str] = {"path": str(path)}
    for line in block.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    title = ""
    m = re.search(r"^#\s+(.+)$", s, flags=re.M)
    if m:
        title = m.group(1).strip()
    meta["title"] = title or path.stem
    return meta


def rebuild_index() -> int:
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    metas: list[dict[str, str]] = []
    for p in NEWS_DIR.rglob("*.md"):
        if p.name == "index.md":
            continue
        m = parse_meta(p)
        if m:
            metas.append(m)
    metas.sort(key=lambda x: x.get("date", ""), reverse=True)

    rows = []
    for m in metas:
        p = Path(m["path"])
        rel = p.relative_to(NEWS_DIR).as_posix()
        day = (m.get("date", "")[:10] or p.parent.name)
        rows.append(
            f"| {day} | {md_escape(m.get('domain','技术动态'))} | [{md_escape(m['title'])}]({rel}) | {md_escape(m.get('source',''))} |"
        )

    body = "\n".join(rows) if rows else "| - | - | 暂无文章 | - |"
    count_by_domain: dict[str, int] = {}
    for m in metas:
        d = m.get("domain", "技术动态")
        count_by_domain[d] = count_by_domain.get(d, 0) + 1
    domain_line = " · ".join(f"{k} {v}" for k, v in sorted(count_by_domain.items())) or "暂无"

    content = f"""# 技术新闻

> 每日自动汇聚 **云原生 / AI 基础设施 / AIOps / 可观测性 / 数据中心硬件** 等方向的技术动态。列表按发布时间从新到旧排序，点击标题进入对应内容页。

## 统计

- 文章总数：{len(metas)}
- 领域分布：{domain_line}
- 更新时间：{now_cn().strftime('%Y-%m-%d %H:%M:%S %Z')}

## 最新文章

| 日期 | 领域 | 标题 | 来源 |
|:---|:---|:---|:---|
{body}

## 自动更新说明

- 生成脚本：`scripts/generate_daily_news.py`
- 文章路径：`docs/news/YYYY-MM-DD/<article-slug>.md`
- 索引规则：扫描 `docs/news/**/*.md` 的 `news-meta` 元数据，按 `date` 倒序重建本页。
- 发布流程：脚本生成内容 → `mkdocs build --strict` → commit → `git push origin main:master` → GitHub Pages 自动部署。
"""
    old = INDEX_FILE.read_text(encoding="utf-8") if INDEX_FILE.exists() else ""
    INDEX_FILE.write_text(content, encoding="utf-8")
    return 1 if content != old else 0


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check)


def git_dirty(paths: list[str]) -> bool:
    r = run(["git", "status", "--porcelain", "--"] + paths, check=True)
    return bool(r.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-items", type=int, default=12, help="max new articles per run")
    ap.add_argument("--days", type=int, default=14, help="prefer articles published within N days")
    ap.add_argument("--build", action="store_true", help="run mkdocs build --strict")
    ap.add_argument("--commit", action="store_true", help="commit docs/news changes")
    ap.add_argument("--push", action="store_true", help="push main:master after commit")
    args = ap.parse_args()

    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    existing = read_existing_urls()
    all_articles: list[Article] = []
    for source, url in SOURCES:
        all_articles.extend(parse_feed(source, url))

    # 去重 + 过滤
    seen: set[str] = set(existing)
    unique: list[Article] = []
    for a in sorted(all_articles, key=lambda x: x.published, reverse=True):
        if a.url in seen or not relevant(a):
            continue
        seen.add(a.url)
        unique.append(a)

    cutoff = now_cn() - dt.timedelta(days=args.days)
    recent = [a for a in unique if a.published >= cutoff]
    selected = (recent or unique)[: args.max_items]

    written: list[Path] = []
    for a in selected:
        written.append(write_article(a))
    index_changed = rebuild_index()

    if args.build:
        print("[build] mkdocs build --strict")
        try:
            out = run(["uv", "run", "--with", "mkdocs", "--with", "mkdocs-material", "mkdocs", "build", "--strict"])
            print(out.stdout[-3000:])
        except subprocess.CalledProcessError as e:
            print(e.stdout)
            return e.returncode

    if args.commit:
        if git_dirty(["docs/news"]):
            run(["git", "add", "docs/news"])
            msg = f"news: 每日技术新闻 {now_cn().strftime('%Y-%m-%d')} (+{len(written)})"
            out = run(["git", "commit", "-m", msg])
            print(out.stdout)
            if args.push:
                out = run(["git", "push", "origin", "main:master"])
                print(out.stdout)
        else:
            print("[noop] docs/news has no changes")

    print(f"[done] new_articles={len(written)}, index_changed={index_changed}, total_feed_items={len(all_articles)}")
    for p in written:
        print(f" - {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
