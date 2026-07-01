#!/usr/bin/env python3
"""Generate /news pages for the MkDocs handbook.

功能:
- 从 RSS/Atom 技术源抓取云原生 / AI 基础设施 / AIOps / 可观测性相关新闻
- 抓取原文页面，抽取正文，格式化为 Markdown
- 非中文正文自动翻译为中文展示，同时保留原文链接和原文标题
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
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
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

CONTENT_SELECTORS = [
    r'<article\b[^>]*>[\s\S]*?</article>',
    r'<main\b[^>]*>[\s\S]*?</main>',
    r'<div\b[^>]+(?:class|id)=["\'][^"\']*(?:article-body|article__body|post-content|post__content|entry-content|blog-post|blog-content|td-post-content|single-post|main-content|content-body|story-body|rich-text|body-copy)[^"\']*["\'][^>]*>[\s\S]*?</div>',
    r'<section\b[^>]+(?:class|id)=["\'][^"\']*(?:article|post|content|body)[^"\']*["\'][^>]*>[\s\S]*?</section>',
]

JUNK_PATTERNS = [
    r'<!--.*?-->',
    r'<script\b[\s\S]*?</script>',
    r'<style\b[\s\S]*?</style>',
    r'<noscript\b[\s\S]*?</noscript>',
    r'<svg\b[\s\S]*?</svg>',
    r'<form\b[\s\S]*?</form>',
    r'<iframe\b[\s\S]*?</iframe>',
    r'<header\b[\s\S]*?</header>',
    r'<nav\b[\s\S]*?</nav>',
    r'<footer\b[\s\S]*?</footer>',
    r'<aside\b[\s\S]*?</aside>',
    r'<div\b[^>]+(?:class|id)=["\'][^"\']*(?:cookie|newsletter|subscribe|signup|advert|ad-|social|share|related|comments|promo|modal|breadcrumb|author-card|toc)[^"\']*["\'][^>]*>[\s\S]*?</div>',
]


@dataclass
class Article:
    title: str
    url: str
    source: str
    published: dt.datetime
    summary: str
    domain: str


@dataclass
class RenderedArticle:
    title_zh: str
    original_title: str
    summary_zh: str
    content_zh: str
    original_language: str
    extraction_status: str


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


def fetch(url: str, timeout: int = 25, accept: str = "*/*") -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 longtds-tech-handbook-news-bot/1.0",
            "Accept": accept,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def decode_bytes(raw: bytes, content_type: str = "") -> str:
    m = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
    encodings = []
    if m:
        encodings.append(m.group(1))
    head = raw[:2000].decode("ascii", "ignore")
    m2 = re.search(r'<meta[^>]+charset=["\']?([\w.-]+)', head, flags=re.I)
    if m2:
        encodings.append(m2.group(1))
    encodings += ["utf-8", "utf-8-sig", "gb18030", "latin-1"]
    for enc in encodings:
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "ignore")


def parse_feed(source: str, url: str) -> list[Article]:
    try:
        raw, _ = fetch(url, accept="application/rss+xml, application/atom+xml, application/xml, text/xml, */*")
    except Exception as e:
        print(f"[warn] fetch failed: {source}: {e}", file=sys.stderr)
        return []
    try:
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"[warn] parse failed: {source}: {e}", file=sys.stderr)
        return []

    articles: list[Article] = []
    for item in root.findall(".//item"):
        title = text_of(child(item, "title"))
        link = text_of(child(item, "link"))
        pub = text_of(child(item, "pubDate")) or text_of(child(item, "date"))
        summary = text_of(child(item, "description")) or text_of(child(item, "summary"))
        if title and link:
            articles.append(Article(title, link, source, parse_date(pub), summary[:1200], classify(title, summary)))

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
            articles.append(Article(title, link, source, parse_date(pub), summary[:1200], classify(title, summary)))
    return articles


def slugify(title: str, url: str) -> str:
    ascii_title = title.encode("ascii", "ignore").decode("ascii").lower()
    ascii_title = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")
    if not ascii_title:
        ascii_title = "article"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{ascii_title[:70].strip('-')}-{digest}"


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def article_path(article: Article) -> Path:
    day = article.published.strftime("%Y-%m-%d")
    digest = hashlib.sha1(article.url.encode("utf-8")).hexdigest()[:8]
    day_dir = NEWS_DIR / day
    if day_dir.exists():
        # URL digest 是稳定标识。若标题变化，沿用旧文件，避免产生重复详情页。
        matches = sorted(day_dir.glob(f"*-{digest}.md"))
        if matches:
            return matches[0]
    return day_dir / f"{slugify(article.title, article.url)}.md"


def clean_html_for_content(html_text: str) -> str:
    s = html_text
    for pat in JUNK_PATTERNS:
        s = re.sub(pat, "\n", s, flags=re.I)
    s = re.sub(r"\s+", " ", s)
    return s


def candidate_score(fragment: str) -> int:
    text = strip_html(fragment)
    words = re.findall(r"[A-Za-z\u4e00-\u9fff]{2,}", text)
    boilerplate_penalty = len(re.findall(r"subscribe|newsletter|cookie|privacy|advertisement|related|share", text, flags=re.I)) * 80
    return len(text) + len(words) * 5 - boilerplate_penalty


def pick_content_html(html_text: str) -> str:
    html_text = clean_html_for_content(html_text)
    candidates: list[str] = []
    for pat in CONTENT_SELECTORS:
        candidates.extend(re.findall(pat, html_text, flags=re.I))
    if candidates:
        return max(candidates, key=candidate_score)
    m = re.search(r"<body\b[^>]*>([\s\S]*?)</body>", html_text, flags=re.I)
    return m.group(1) if m else html_text


class MarkdownHTMLParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.out: list[str] = []
        self.skip_depth = 0
        self.href_stack: list[str | None] = []
        self.in_pre = False
        self.in_inline_code = False
        self.in_table_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.table_rows: list[list[str]] = []

    def emit(self, text: str) -> None:
        if self.skip_depth:
            return
        if self.in_table_cell:
            self.current_cell.append(text)
        else:
            self.out.append(text)

    def newline(self, n: int = 1) -> None:
        self.emit("\n" * n)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_d = {k.lower(): v or "" for k, v in attrs}
        if tag in {"script", "style", "noscript", "svg", "form", "iframe"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in {"p", "div", "section", "article", "main"}:
            self.newline(2)
        elif tag in {"br"}:
            self.newline(1)
        elif re.fullmatch(r"h[1-6]", tag):
            level = int(tag[1])
            self.newline(2)
            self.emit("#" * min(level + 1, 6) + " ")  # 页面标题占 H1，原文 h1 从 h2 开始
        elif tag == "li":
            self.newline(1)
            self.emit("- ")
        elif tag in {"ul", "ol"}:
            self.newline(1)
        elif tag == "blockquote":
            self.newline(2)
            self.emit("> ")
        elif tag == "pre":
            self.newline(2)
            self.emit("```\n")
            self.in_pre = True
        elif tag == "code" and not self.in_pre:
            self.emit("`")
            self.in_inline_code = True
        elif tag == "a":
            href = attrs_d.get("href")
            if href:
                href = urllib.parse.urljoin(self.base_url, href)
            self.href_stack.append(href)
            if href:
                self.emit("[")
        elif tag == "img":
            alt = attrs_d.get("alt", "").strip()
            src = attrs_d.get("src", "").strip()
            if src and alt:
                self.newline(1)
                self.emit(f"![{alt}]({urllib.parse.urljoin(self.base_url, src)})")
        elif tag == "tr":
            self.current_row = []
        elif tag in {"td", "th"}:
            self.in_table_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "form", "iframe"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "a":
            href = self.href_stack.pop() if self.href_stack else None
            if href:
                self.emit(f"]({href})")
        elif tag == "code" and self.in_inline_code:
            self.emit("`")
            self.in_inline_code = False
        elif tag == "pre" and self.in_pre:
            self.emit("\n```")
            self.in_pre = False
            self.newline(2)
        elif tag in {"p", "div", "section", "article", "main", "blockquote"}:
            self.newline(2)
        elif re.fullmatch(r"h[1-6]", tag):
            self.newline(2)
        elif tag in {"td", "th"}:
            cell = re.sub(r"\s+", " ", "".join(self.current_cell)).strip()
            self.current_row.append(cell)
            self.current_cell = []
            self.in_table_cell = False
        elif tag == "tr":
            if self.current_row:
                self.table_rows.append(self.current_row)
        elif tag == "table":
            if self.table_rows:
                self.newline(2)
                width = max(len(r) for r in self.table_rows)
                rows = [r + [""] * (width - len(r)) for r in self.table_rows]
                self.emit("| " + " | ".join(md_escape(c) for c in rows[0]) + " |\n")
                self.emit("|" + "|".join([":---"] * width) + "|\n")
                for r in rows[1:]:
                    self.emit("| " + " | ".join(md_escape(c) for c in r) + " |\n")
                self.table_rows = []
                self.newline(1)

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_pre:
            self.emit(data)
        else:
            self.emit(re.sub(r"\s+", " ", data))

    def get_markdown(self) -> str:
        s = "".join(self.out)
        s = html.unescape(s)
        # 修正链接空白: [ text ](url) -> [text](url)
        s = re.sub(r"\[\s+", "[", s)
        s = re.sub(r"\s+\]\(", "](", s)
        s = re.sub(r"[ \t]+\n", "\n", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        # 删除常见尾部垃圾行
        lines = []
        for line in s.splitlines():
            t = line.strip()
            if not t:
                lines.append("")
                continue
            if re.fullmatch(r"(share|subscribe|advertisement|related posts?|read more|sign up|newsletter)", t, flags=re.I):
                continue
            lines.append(t if t.startswith(("#", "- ", ">", "|", "```")) else t)
        s = "\n".join(lines)
        s = re.sub(r"\n{3,}", "\n\n", s).strip()
        return s


def html_to_markdown(html_fragment: str, base_url: str) -> str:
    parser = MarkdownHTMLParser(base_url)
    try:
        parser.feed(html_fragment)
        parser.close()
    except Exception:
        return strip_html(html_fragment)
    return parser.get_markdown()


def extract_meta_content(html_text: str, names: list[str]) -> str:
    for name in names:
        patterns = [
            rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']',
        ]
        for pat in patterns:
            m = re.search(pat, html_text, flags=re.I)
            if m:
                return html.unescape(m.group(1)).strip()
    return ""


def wordpress_api_content(url: str) -> tuple[str, str] | None:
    """Fetch clean WordPress content via REST API when available."""
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.rstrip("/").split("/")[-1]
    if not slug:
        return None
    api_url = f"{parsed.scheme}://{parsed.netloc}/wp-json/wp/v2/posts?slug={urllib.parse.quote(slug)}"
    try:
        raw, ctype = fetch(api_url, timeout=25, accept="application/json, */*")
        data = json.loads(decode_bytes(raw, ctype))
        if not data:
            return None
        item = data[0]
        title = strip_html(item.get("title", {}).get("rendered", ""))
        content = item.get("content", {}).get("rendered", "")
        if content and len(strip_html(content)) > 300:
            return content, title
    except Exception:
        return None
    return None


def extract_jsonld_article(html_text: str) -> tuple[str, str] | None:
    """Extract articleBody/headline from JSON-LD if present."""
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', html_text, flags=re.I):
        raw = html.unescape(m.group(1)).strip()
        try:
            data = json.loads(raw)
        except Exception:
            continue
        nodes: list[dict] = []
        if isinstance(data, dict):
            if isinstance(data.get("@graph"), list):
                nodes.extend(x for x in data["@graph"] if isinstance(x, dict))
            nodes.append(data)
        elif isinstance(data, list):
            nodes.extend(x for x in data if isinstance(x, dict))
        for node in nodes:
            typ = node.get("@type")
            types = typ if isinstance(typ, list) else [typ]
            if any(t in {"NewsArticle", "Article", "BlogPosting", "TechArticle"} for t in types):
                body = node.get("articleBody") or ""
                headline = node.get("headline") or ""
                if isinstance(body, str) and len(body.strip()) > 300:
                    paras = [p.strip() for p in re.split(r"\n{2,}|(?<=[.!?])\s+(?=[A-Z])", body) if p.strip()]
                    return "\n\n".join(f"<p>{html.escape(p)}</p>" for p in paras), strip_html(str(headline))
    return None


def clean_markdown_boilerplate(md: str) -> str:
    bad_exact = {
        "电子邮件地址", "必填", "重新订阅", "名字", "姓氏", "公司名称", "国家", "邮政编码", "很高兴认识你！",
        "接下来是什么？", "建筑", "工程", "运营", "频道", "新堆栈", "newsletter", "subscribe", "advertisement",
        "发表于", "相关文章", "###### 相关文章", "立即尝试 Gemini Enterprise 商业版", "工作场所人工智能的大门", "[立即尝试]",
    }
    bad_contains = [
        "您之前似乎已经取消订阅", "请回答几个简单的问题", "以下哪一项最能描述", "选择...", "在您最喜爱的社交媒体网络上关注",
        "成为 LinkedIn 上的", "最新的精选和热门故事", "This field is required", "Sign up", "Subscribe",
        "shareArticle", "sharer.php", "intent/tweet", "mailto:?subject", "utm_source=cloud.google.com/blog",
    ]
    truncate_markers = {
        "发表于", "相关文章", "###### 相关文章", "Related posts", "Related articles", "More from",
        "Tags", "Categories", "About the author", "Learn more about",
    }
    lines: list[str] = []
    skipping = False
    for line in md.splitlines():
        t = line.strip()
        if t in truncate_markers:
            break
        if re.fullmatch(r"-\s*\[\]\([^)]*\)", t):
            continue
        if re.fullmatch(r"!\[[^\]]*\]\(([^)]+)\)\s*!\[[^\]]*\]\(\1\)", t):
            # 部分站点同一图片连续输出两次，去重保留一张。
            t = re.sub(r"\)\s*!\[", ")\n![", t).splitlines()[0]
            line = t
        if t in bad_exact or any(x.lower() in t.lower() for x in bad_contains):
            skipping = True
            continue
        if skipping and (t.startswith("## ") or len(t) > 80):
            skipping = False
        if skipping and (not t or len(t) < 80):
            continue
        if re.fullmatch(r"[✓0%\s]+", t):
            continue
        lines.append(line)
    s = "\n".join(lines)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s


def cjk_ratio(text: str) -> float:
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    cjk = sum(1 for c in chars if "\u4e00" <= c <= "\u9fff")
    return cjk / max(len(chars), 1)


def looks_chinese(text: str) -> bool:
    return cjk_ratio(text[:4000]) > 0.18


def protect_urls(text: str) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}

    def repl(m: re.Match[str]) -> str:
        key = f"__URL_{len(mapping)}__"
        mapping[key] = m.group(0)
        return key

    text = re.sub(r"https?://[^\s)\]]+", repl, text)
    return text, mapping


def restore_urls(text: str, mapping: dict[str, str]) -> str:
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def google_translate(text: str, target: str = "zh-CN", retries: int = 3) -> str:
    if not text.strip():
        return text
    protected, mapping = protect_urls(text)
    qs = urllib.parse.urlencode({"client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": protected})
    url = "https://translate.googleapis.com/translate_a/single?" + qs
    last_err = None
    for attempt in range(retries):
        try:
            raw, _ = fetch(url, timeout=30, accept="application/json, text/plain, */*")
            data = json.loads(raw.decode("utf-8"))
            translated = "".join(part[0] for part in data[0] if part and part[0])
            return restore_urls(translated, mapping)
        except Exception as e:
            last_err = e
            time.sleep(0.6 * (attempt + 1))
    print(f"[warn] translate failed: {last_err}", file=sys.stderr)
    return restore_urls(protected, mapping)


def split_markdown_blocks(md: str, max_chars: int = 2400) -> list[str]:
    blocks = re.split(r"(\n\s*\n)", md)
    chunks: list[str] = []
    buf = ""
    for b in blocks:
        if len(buf) + len(b) <= max_chars:
            buf += b
        else:
            if buf.strip():
                chunks.append(buf)
            if len(b) > max_chars:
                # 大段硬切，避免翻译接口 URL 过长
                for i in range(0, len(b), max_chars):
                    chunks.append(b[i:i + max_chars])
                buf = ""
            else:
                buf = b
    if buf.strip():
        chunks.append(buf)
    return chunks


def translate_markdown_to_zh(md: str) -> str:
    # 保留代码块原样；其余 Markdown 块逐块翻译。
    parts = re.split(r"(```[\s\S]*?```)", md)
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("```"):
            out.append(part)
            continue
        if looks_chinese(part):
            out.append(part)
            continue
        translated_chunks = []
        for chunk in split_markdown_blocks(part):
            translated_chunks.append(google_translate(chunk))
            time.sleep(0.15)
        out.append("".join(translated_chunks))
    s = "".join(out)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return normalize_translation_terms(s)


def normalize_translation_terms(text: str) -> str:
    """修正常见技术品牌/模型名被机器翻译误译的问题。"""
    replacements = {
        "人择": "Anthropic",
        "人类人工智能": "Anthropic AI",
        "人类的": "Anthropic 的",
        "神鬼寓言": "Fable",
        "寓言": "Fable",
        "神话": "Mythos",
        "克劳德": "Claude",
        "新堆栈": "The New Stack",
        "战争部": "国防部",
        "大型语言模型": "LLM",
        "可观察性": "可观测性",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    post_replacements = {
        "ClaudeFable": "Claude Fable",
        "AnthropicFable": "Anthropic Fable",
        "Anthropic现在": "Anthropic 现在",
        "Anthropic问题": "Anthropic 问题",
        "对Anthropic": "对 Anthropic",
        "的Anthropic": "的 Anthropic",
        "在Anthropic": "在 Anthropic",
        "与Anthropic": "与 Anthropic",
        "球在Anthropic": "球在 Anthropic",
        "Fable和": "Fable 和",
        "Mythos和": "Mythos 和",
        "和Mythos": "和 Mythos",
        "Fable的": "Fable 的",
        "Fable控制": "Fable 控制",
        "Fable实施": "Fable 实施",
        "对Fable": "对 Fable",
        "将Fable": "将 Fable",
        "人类与特朗普": "Anthropic 与特朗普",
    }
    for src, dst in post_replacements.items():
        text = text.replace(src, dst)
    # 修复标题级别在翻译后丢空格的问题：###标题 -> ### 标题
    text = re.sub(r"^(#{2,6})([^#\s])", r"\1 \2", text, flags=re.M)
    # 修复标题后紧贴列表的问题：#### 标题：- item -> #### 标题：\n\n- item
    text = re.sub(r"^(#{2,6}\s+[^\n]+?)\s*[-–]\s+", r"\1\n\n- ", text, flags=re.M)
    # 修复标题与正文粘连：#### Title正文 -> #### Title\n\n正文（保守处理常见站点标题）
    text = re.sub(r"^(#{2,6}\s+[^\n]{1,60}?)(BigQuery|AWS|Google|Amazon|Kubernetes|Claude|Gemini|AgentCore|Bedrock|NVIDIA|GPU|LLM|AI|现在|今天|如果|企业|该|这)", r"\1\n\n\2", text, flags=re.M)
    return text


def latin_ratio(text: str) -> float:
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    latin = sum(1 for c in chars if ("a" <= c.lower() <= "z"))
    return latin / max(len(chars), 1)


def should_translate_residual_line(line: str) -> bool:
    """Detect untranslated English/mixed Markdown lines after chunk translation."""
    t = line.strip()
    if not t or t.startswith("```"):
        return False
    # 表格分隔行 / 纯链接引用 / 纯技术 token 不处理。
    if re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?", t):
        return False
    plain = re.sub(r"https?://\S+", "", t)
    plain = re.sub(r"[`*_#>\[\]()|:-]", " ", plain)
    words = re.findall(r"[A-Za-z][A-Za-z'’\-]{2,}", plain)
    if len(words) < 4:
        return False
    # 只要有明显英文长句就二次翻译；保留 Kubernetes/GPU/LLM 等短技术词不误伤。
    return latin_ratio(plain) > 0.22 or cjk_ratio(plain) < 0.12


def translate_residual_english(md: str) -> str:
    """Second pass: translate lines that Google left partially/fully in English."""
    out: list[str] = []
    in_code = False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code or not should_translate_residual_line(line):
            out.append(line)
            continue
        translated = google_translate(line)
        out.append(normalize_translation_terms(translated))
        time.sleep(0.08)
    return "\n".join(out)


def fetch_and_render_article(article: Article, max_body_chars: int = 45000) -> RenderedArticle:
    original_title = article.title.strip()
    title_zh = original_title if looks_chinese(original_title) else normalize_translation_terms(google_translate(original_title))
    summary_zh = article.summary.strip()
    if summary_zh and not looks_chinese(summary_zh):
        summary_zh = normalize_translation_terms(google_translate(summary_zh))
    if not summary_zh:
        summary_zh = "RSS/Atom 源未提供摘要。"

    extraction_status = "full"
    try:
        content_title = ""
        wp = wordpress_api_content(article.url)
        if wp:
            content_html, content_title = wp
            extraction_status = "wordpress-api"
        else:
            raw, ctype = fetch(article.url, timeout=35, accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            html_text = decode_bytes(raw, ctype)
            content_title = extract_meta_content(html_text, ["og:title", "twitter:title"]) or original_title
            jsonld = extract_jsonld_article(html_text)
            if jsonld:
                content_html, jsonld_title = jsonld
                content_title = jsonld_title or content_title
                extraction_status = "json-ld"
            else:
                content_html = pick_content_html(html_text)
                extraction_status = "html-heuristic"
        if content_title:
            original_title = strip_html(content_title)
            title_zh = original_title if looks_chinese(original_title) else normalize_translation_terms(google_translate(original_title))
        content_md = html_to_markdown(content_html, article.url)
        content_md = clean_markdown_boilerplate(re.sub(r"\n{3,}", "\n\n", content_md).strip())
        # 太短说明正文抽取失败，退回 RSS 摘要。
        if len(strip_html(content_md)) < 500:
            extraction_status = "fallback-summary"
            content_md = article.summary or "原文页面未能自动抽取正文，请点击原文链接查看。"
    except Exception as e:
        extraction_status = f"fallback-summary ({type(e).__name__})"
        content_md = article.summary or "原文页面未能自动抽取正文，请点击原文链接查看。"

    if len(content_md) > max_body_chars:
        content_md = content_md[:max_body_chars].rsplit("\n", 1)[0] + "\n\n> 注：原文较长，本站已截取主要正文展示；完整内容请查看原文。"
        extraction_status += "+truncated"

    original_language = "zh" if looks_chinese(f"{original_title}\n{content_md}") else "non-zh"
    content_zh = content_md if original_language == "zh" else translate_markdown_to_zh(content_md)
    if original_language != "zh":
        content_zh = translate_residual_english(content_zh)
    content_zh = normalize_translation_terms(clean_markdown_boilerplate(content_zh))
    title_zh = normalize_translation_terms(title_zh)
    summary_zh = normalize_translation_terms(summary_zh)
    return RenderedArticle(title_zh, original_title, summary_zh, content_zh, original_language, extraction_status)


def read_existing_urls() -> set[str]:
    urls: set[str] = set()
    if not NEWS_DIR.exists():
        return urls
    for p in NEWS_DIR.rglob("*.md"):
        if p.name == "index.md":
            continue
        m = parse_meta(p)
        if m and m.get("url"):
            urls.add(m["url"].strip())
    return urls


def write_article(article: Article, *, overwrite: bool = True) -> Path:
    p = article_path(article)
    if p.exists() and not overwrite:
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    rendered = fetch_and_render_article(article)
    date_s = article.published.strftime("%Y-%m-%d %H:%M %Z")
    content = f"""<!-- news-meta
created_by: generate_daily_news.py
date: {article.published.isoformat()}
source: {article.source}
domain: {article.domain}
url: {article.url}
content_mode: full-translated
original_language: {rendered.original_language}
extraction_status: {rendered.extraction_status}
-->

# {rendered.title_zh}

| 字段 | 内容 |
|:---|:---|
| 日期 | {date_s} |
| 领域 | {article.domain} |
| 来源 | {article.source} |
| 原文标题 | {md_escape(rendered.original_title)} |
| 原文 | [打开原文]({article.url}) |
| 展示策略 | 原文正文格式化为 Markdown；非中文内容已自动翻译为中文 |
| 抽取状态 | {rendered.extraction_status} |

## 摘要

{rendered.summary_zh}

## 正文

{rendered.content_zh}

## 运维 / 架构关注点

- 关注它是否影响 **云原生平台、AI 推理/训练基础设施、AIOps/可观测性、数据中心硬件或安全合规**。
- 如果涉及 Kubernetes / GPU / 可观测性 / 推理框架，建议后续补充到对应章节的「发展与展望」或「最佳实践」。
- 本站对原文进行格式化归档；非中文内容自动翻译为中文。技术细节、数字和引用以原文为准。

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
    # 兼容旧页面：从表格/正文里恢复摘要
    summary = ""
    sm = re.search(r"## 摘要\s+([\s\S]*?)(?:\n## |\Z)", s)
    if sm:
        summary = sm.group(1).strip()
    meta["summary"] = summary
    original_title = ""
    tm = re.search(r"\| 原文标题 \|\s*(.*?)\s*\|", s)
    if tm:
        original_title = tm.group(1).strip().replace("\\|", "|")
    meta["original_title"] = original_title or meta.get("title", "")
    return meta


def article_from_meta(meta: dict[str, str]) -> Article | None:
    if not meta.get("url"):
        return None
    title = meta.get("original_title") or meta.get("title") or Path(meta["path"]).stem
    date = parse_date(meta.get("date", ""))
    return Article(
        title=title,
        url=meta["url"],
        source=meta.get("source", "未知来源"),
        published=date,
        summary=meta.get("summary", ""),
        domain=meta.get("domain", "技术动态"),
    )


def existing_articles_needing_refresh(force: bool = False) -> list[Article]:
    articles: list[Article] = []
    for p in sorted(NEWS_DIR.rglob("*.md")) if NEWS_DIR.exists() else []:
        if p.name == "index.md":
            continue
        meta = parse_meta(p)
        if not meta:
            continue
        if force or meta.get("content_mode") != "full-translated":
            a = article_from_meta(meta)
            if a:
                articles.append(a)
    articles.sort(key=lambda x: x.published, reverse=True)
    return articles


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

> 每日自动汇聚 **云原生 / AI 基础设施 / AIOps / 可观测性 / 数据中心硬件** 等方向的技术动态。列表按发布时间从新到旧排序，点击标题进入对应内容页。详情页会抽取原文正文并格式化展示；非中文原文自动翻译为中文。

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
- 内容规则：抓取原文页面 → 抽取正文 → 转 Markdown → 非中文自动翻译为中文 → 写入详情页。
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
    ap.add_argument("--refresh-existing", action="store_true", help="rewrite existing summary-only pages as full translated pages")
    ap.add_argument("--force-refresh", action="store_true", help="refresh all existing news pages even if already full-translated")
    ap.add_argument("--max-refresh", type=int, default=200, help="max existing pages to refresh in one run")
    ap.add_argument("--build", action="store_true", help="run mkdocs build --strict")
    ap.add_argument("--commit", action="store_true", help="commit docs/news changes")
    ap.add_argument("--push", action="store_true", help="push main:master after commit")
    args = ap.parse_args()

    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    existing = read_existing_urls()
    all_articles: list[Article] = []
    for source, url in SOURCES:
        all_articles.extend(parse_feed(source, url))

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

    refreshed: list[Path] = []
    if args.refresh_existing or args.force_refresh:
        for a in existing_articles_needing_refresh(force=args.force_refresh)[: args.max_refresh]:
            print(f"[refresh] {a.title} <- {a.url}")
            refreshed.append(write_article(a, overwrite=True))

    written: list[Path] = []
    for a in selected:
        print(f"[new] {a.title} <- {a.url}")
        written.append(write_article(a, overwrite=True))

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
            msg = f"news: 每日技术新闻 {now_cn().strftime('%Y-%m-%d')} (+{len(written)}, refresh={len(refreshed)})"
            out = run(["git", "commit", "-m", msg])
            print(out.stdout)
            if args.push:
                out = run(["git", "push", "origin", "main:master"])
                print(out.stdout)
        else:
            print("[noop] docs/news has no changes")

    print(f"[done] new_articles={len(written)}, refreshed={len(refreshed)}, index_changed={index_changed}, total_feed_items={len(all_articles)}")
    for p in refreshed[:20]:
        print(f" - refreshed {p.relative_to(ROOT)}")
    if len(refreshed) > 20:
        print(f" - refreshed ... {len(refreshed) - 20} more")
    for p in written:
        print(f" - {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
