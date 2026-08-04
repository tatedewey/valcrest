from __future__ import annotations

import html
import json
import os
import re
from datetime import date
from pathlib import Path

from openai import OpenAI

BLOG_DIR = Path(__file__).resolve().parents[1]
ROOT = BLOG_DIR.parent
TOPICS_FILE = Path(__file__).with_name("topics.json")
PUBLISHED_FILE = Path(__file__).with_name("published.json")
INDEX_FILE = BLOG_DIR / "index.html"
SITE_URL = "https://www.valcrestcapital.com"
AUTHOR = "Tate Dewey"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:90]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pick_topic(topics: list[dict], published: list[str]) -> dict:
    published_lower = {item.lower() for item in published}
    for topic in topics:
        if topic["topic"].lower() not in published_lower:
            return topic
    raise RuntimeError("No unused topics remain. Add more topics to automation/topics.json.")


def extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON.")
    return json.loads(raw[start : end + 1])


def generate(topic: dict) -> dict:
    client = OpenAI()
    prompt = f"""
Write an original commercial real estate capital-markets article for Valcrest Capital.

AUTHOR: Tate Dewey, Co-Founder of Valcrest Capital
TOPIC: {topic['topic']}
CATEGORY: {topic['category']}
ANGLE: {topic['summary']}

VOICE:
- Insider and practical, based on patterns observed in conversations with sponsors and institutional capital providers.
- Confident but never boastful.
- Do not invent statistics, transactions, investor names, quotations, performance, or claims about the number of firms contacted.
- Do not imply Valcrest invests its own capital or guarantees financing.
- Do not give legal, tax, securities, or investment advice.
- Use clear language and useful specifics.

OUTPUT:
Return only one valid JSON object with these keys:
- title: compelling title, 45-68 characters
- meta_description: 140-160 characters
- dek: one-sentence introduction
- category: short category
- excerpt: 25-40 words
- body_html: 1200-1800 words of clean HTML using only p, h2, h3, ul, ol, li, strong, em and blockquote. No h1. No links. Include a concise practical conclusion.

The article must be genuinely useful and avoid keyword stuffing.
"""
    response = client.responses.create(model=MODEL, input=prompt)
    return extract_json(response.output_text)


def quality_check(article: dict) -> None:
    required = {"title", "meta_description", "dek", "category", "excerpt", "body_html"}
    missing = required.difference(article)
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")
    plain = re.sub(r"<[^>]+>", " ", article["body_html"])
    words = re.findall(r"\b[\w'-]+\b", plain)
    if len(words) < 1000:
        raise ValueError(f"Article too short: {len(words)} words")
    prohibited = ["guaranteed funding", "guaranteed return", "we invest our capital", "risk-free"]
    lower = plain.lower()
    hits = [term for term in prohibited if term in lower]
    if hits:
        raise ValueError(f"Prohibited claims found: {hits}")
    if not 120 <= len(article["meta_description"]) <= 170:
        raise ValueError("Meta description is outside acceptable length.")


def article_template(article: dict, slug: str, today: date) -> str:
    title = html.escape(article["title"])
    meta = html.escape(article["meta_description"], quote=True)
    dek = html.escape(article["dek"])
    category = html.escape(article["category"])
    published = today.strftime("%B %-d, %Y")
    canonical = f"{SITE_URL}/blog/{slug}.html"
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article["title"],
        "datePublished": today.isoformat(),
        "dateModified": today.isoformat(),
        "author": {"@type": "Person", "name": AUTHOR, "jobTitle": "Co-Founder", "worksFor": {"@type": "Organization", "name": "Valcrest Capital"}},
        "publisher": {"@type": "Organization", "name": "Valcrest Capital", "url": SITE_URL},
        "mainEntityOfPage": canonical,
    }
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | Valcrest Capital</title><meta name="description" content="{meta}"><link rel="canonical" href="{canonical}">
<script type="application/ld+json">{json.dumps(schema, separators=(",", ":"))}</script>
<style>:root{{--ink:#161b1e;--muted:#6f6a61;--paper:#f4efe5;--white:#fff;--line:rgba(22,27,30,.18);--gold:#b89454;--forest:#0e171b}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.75}}a{{color:inherit}}.wrap{{width:min(820px,calc(100% - 36px));margin:auto}}.header{{background:var(--forest);color:#fff;padding:25px 0}}.nav{{display:flex;justify-content:space-between;align-items:center}}.nav a{{text-decoration:none;font-size:13px;font-weight:850;text-transform:uppercase}}.hero{{padding:78px 0 50px;border-bottom:1px solid var(--line)}}.tag{{font-size:11px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;color:#8a6c38}}.hero h1{{font-family:Georgia,serif;font-size:clamp(40px,7vw,68px);line-height:1.04;margin:14px 0 20px}}.dek{{font-size:20px;color:var(--muted)}}.byline{{margin-top:26px;font-size:13px;font-weight:800}}.article{{padding:55px 0 85px}}.article p,.article li{{font-size:18px}}.article h2{{font-family:Georgia,serif;font-size:34px;line-height:1.18;margin:48px 0 14px}}.article h3{{font-size:22px;margin:32px 0 8px}}.article blockquote{{margin:38px 0;padding:26px 28px;background:#fff;border-left:4px solid var(--gold)}}.author{{margin-top:60px;padding:30px;background:#fff;border:1px solid var(--line)}}.author h2{{margin:0 0 8px;font-size:26px}}.cta{{margin-top:30px;padding:30px;background:var(--forest);color:#fff}}.cta a{{color:#fff;font-weight:850}}footer{{background:var(--forest);color:#ddd;padding:35px 0;font-size:13px}}@media(max-width:700px){{.article p,.article li{{font-size:17px}}}}</style></head>
<body><header class="header"><div class="wrap nav"><a href="/">Valcrest Capital</a><a href="/blog/">Insights</a></div></header><main>
<section class="hero"><div class="wrap"><div class="tag">{category}</div><h1>{title}</h1><p class="dek">{dek}</p><div class="byline">By Tate Dewey, Co-Founder of Valcrest Capital · {published}</div></div></section>
<article class="article"><div class="wrap">{article['body_html']}
<section class="author"><h2>About Tate Dewey</h2><p>Tate Dewey is Co-Founder of Valcrest Capital, where he works with commercial real estate sponsors seeking institutional equity and financing for acquisitions, developments and recapitalizations.</p></section>
<section class="cta"><strong>Evaluating the capital strategy for a commercial real estate opportunity?</strong><p>Visit <a href="/">Valcrest Capital</a> to learn more about our capital advisory work.</p></section></div></article></main>
<footer><div class="wrap">© {today.year} Valcrest Capital. This material is for general informational purposes and is not an offer to sell or a solicitation to purchase any security.</div></footer></body></html>'''


def update_index(article: dict, slug: str, today: date) -> None:
    text = INDEX_FILE.read_text(encoding="utf-8")
    marker = "<!-- ARTICLES_START -->"
    card = f'''\n      <a class="card" href="/blog/{slug}.html">
        <span class="tag">{html.escape(article['category'])}</span>
        <h2>{html.escape(article['title'])}</h2>
        <p>{html.escape(article['excerpt'])}</p>
        <span class="meta">By Tate Dewey · {today.strftime("%B %-d, %Y")}</span>
      </a>'''
    if f'/blog/{slug}.html' not in text:
        text = text.replace(marker, marker + card, 1)
        INDEX_FILE.write_text(text, encoding="utf-8")


def update_sitemap(slug: str, today: date) -> None:
    sitemap = BLOG_DIR / "sitemap.xml"
    urls = [f"{SITE_URL}/", f"{SITE_URL}/blog/"]
    urls.extend(f"{SITE_URL}/blog/{p.name}" for p in sorted(BLOG_DIR.glob("*.html")) if p.name != "index.html")
    body = "\n".join(f"  <url><loc>{u}</loc><lastmod>{today.isoformat()}</lastmod></url>" for u in urls)
    sitemap.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n', encoding="utf-8")


def main() -> None:
    topics = load_json(TOPICS_FILE)
    published = load_json(PUBLISHED_FILE)
    topic = pick_topic(topics, published)
    article = generate(topic)
    quality_check(article)
    today = date.today()
    slug = slugify(article["title"])
    destination = BLOG_DIR / f"{slug}.html"
    if destination.exists():
        raise FileExistsError(destination)
    destination.write_text(article_template(article, slug, today), encoding="utf-8")
    update_index(article, slug, today)
    update_sitemap(slug, today)
    published.append(topic["topic"])
    PUBLISHED_FILE.write_text(json.dumps(published, indent=2) + "\n", encoding="utf-8")
    print(f"Published {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
