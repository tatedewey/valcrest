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

PRIMARY_AUTHOR = "Tate Dewey"
PARTNER = "Samuel Aureliano"

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

MIN_UNUSED_TOPICS = 10
TOPIC_BATCH_SIZE = 50


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:90]


def load_json(path: Path, default):
    if not path.exists():
        return default

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def save_json(path: Path, data) -> None:
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )


def normalize_topic(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def extract_json(raw: str):
    raw = raw.strip()

    if raw.startswith("```"):
        raw = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw,
        )
        raw = re.sub(
            r"\s*```$",
            "",
            raw,
        )

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    object_start = raw.find("{")
    array_start = raw.find("[")

    starts = [
        x
        for x in (
            object_start,
            array_start,
        )
        if x != -1
    ]

    if not starts:
        raise ValueError(
            "Model did not return valid JSON."
        )

    start = min(starts)

    if raw[start] == "[":
        end = raw.rfind("]")
    else:
        end = raw.rfind("}")

    if end == -1:
        raise ValueError(
            "Model did not return complete JSON."
        )

    return json.loads(
        raw[start : end + 1]
    )


def unused_topics(
    topics: list[dict],
    published: list[str],
) -> list[dict]:

    published_set = {
        normalize_topic(item)
        for item in published
    }

    return [
        topic
        for topic in topics
        if normalize_topic(
            topic["topic"]
        ) not in published_set
    ]


def generate_new_topics(
    existing_topics: list[dict],
    published: list[str],
    count: int = TOPIC_BATCH_SIZE,
) -> list[dict]:

    client = OpenAI()

    existing_names = [
        topic["topic"]
        for topic in existing_topics
        if isinstance(topic, dict)
        and "topic" in topic
    ]

    avoid_topics = list(
        dict.fromkeys(
            existing_names + published
        )
    )

    recent_avoid = avoid_topics[-250:]

    prompt = f"""
Generate {count} NEW SEO article topics for Valcrest Capital.

ABOUT VALCREST:
Valcrest Capital is a commercial real estate capital advisory firm.

The firm works with commercial real estate sponsors,
owners and developers on capital raises and financing
assignments involving acquisitions, developments,
recapitalizations and refinancings.

PRIMARY SEO OBJECTIVES:

1. Attract commercial real estate sponsors,
developers, owners and capital providers who could
realistically become Valcrest clients or counterparties.

2. Build strong search-engine association between
Tate Dewey and commercial real estate, CRE capital
markets, institutional equity and financing.

Every eventual article will visibly show:
Tate Dewey, Co-Founder of Valcrest Capital.

The goal is NOT to create articles about Tate personally.
The goal is to consistently establish Tate Dewey as a
commercial real estate capital-markets professional through
useful, authoritative CRE content.

TARGET SEARCHERS:
- commercial real estate sponsors
- real estate developers
- owner/operators
- multifamily sponsors
- industrial sponsors
- commercial property owners
- real estate private equity professionals
- family offices
- institutional real estate investors
- equity capital providers
- lenders
- borrowers seeking CRE capital

TOPIC PRIORITIES:

1. JV EQUITY AND LP EQUITY

Examples of useful search intent:
- multifamily JV equity
- real estate joint venture equity
- LP equity for real estate acquisitions
- institutional equity for commercial real estate
- CRE equity capital
- equity partner for real estate development
- family office equity for real estate
- real estate sponsor equity partner

2. CAPITAL RAISING AND CAPITAL STACK

Examples:
- how to raise equity for a multifamily acquisition
- commercial real estate capital stack
- sponsor co-invest requirements
- GP equity vs LP equity
- equity gap financing
- recapitalization capital
- institutional equity requirements
- real estate sponsor capital raising

3. DEBT AND FINANCING

Examples:
- construction financing
- bridge loans
- acquisition financing
- permanent financing
- refinancing
- CRE maturity financing
- debt sizing
- financing transitional properties
- construction loan requirements
- commercial real estate refinance options

4. DEAL-SPECIFIC PROBLEMS

Examples:
- replacing an equity investor before closing
- funding a multifamily acquisition with low occupancy
- financing offline units
- recapitalizing a property after business plan delays
- solving a refinance gap
- financing lease-up
- raising capital on a tight closing timeline
- financing a distressed acquisition
- capitalizing a value-add multifamily deal

5. PROPERTY TYPES

Prioritize:
- multifamily
- industrial
- retail
- mixed-use
- office when the topic has clear capital-markets relevance

6. GEOGRAPHIC SEARCH INTENT

Selectively include commercially useful market-specific
topics involving:
- Texas
- Dallas
- DFW
- San Antonio
- Houston
- Austin
- Florida
- Miami
- Orlando
- Tampa
- Kansas City
- Midwest
- Southeast
- Sun Belt

7. HIGH-INTENT QUESTIONS

Create topics around questions a real sponsor might search
immediately before hiring an advisor or beginning a capital raise.

Examples:
- how much sponsor equity is required in a real estate deal
- how to find an equity partner for a multifamily acquisition
- how institutional investors evaluate real estate sponsors
- what family offices look for in real estate deals
- how to structure JV equity for commercial real estate
- how long does a CRE equity raise take
- what investors need before reviewing a real estate deal
- when to use preferred equity vs common equity

AVOID:
- generic CRE trends articles
- vague economic predictions
- broad macro commentary
- residential real estate
- home mortgages
- consumer investing
- generic definitions with no commercial relevance
- clickbait
- topics designed only for traffic
- duplicate keyword variations
- celebrity or entertainment references
- movie-related topics
- content about Tate Dewey's entertainment background

SEO RULES:
- Each topic should target a clear search query or keyword cluster.
- Favor long-tail keywords with commercial intent.
- Mix educational, comparison, problem-solving and geographic queries.
- Avoid keyword stuffing.
- Topics should be evergreen whenever possible.
- Do not require proprietary or live market data.
- Do not fabricate statistics or market facts.
- Favor topics that can credibly demonstrate expertise in CRE capital markets.

DO NOT REPEAT OR CLOSELY DUPLICATE THESE PREVIOUS TOPICS:

{json.dumps(recent_avoid, indent=2)}

OUTPUT:

Return ONLY a valid JSON array with exactly {count} objects.

Each object must contain:

- "topic"
  Natural-language SEO topic/title concept.

- "category"
  Short category.

- "summary"
  1-2 sentence article angle.

- "primary_keyword"
  Main search phrase.

- "search_intent"
  One of:
  "commercial"
  "informational-commercial"
  "comparison"
  "problem-solving"

Example:

{{
  "topic": "How Sponsors Raise LP Equity for Multifamily Acquisitions",
  "category": "Equity Capital",
  "summary": "Explain how institutional and family-office LP equity is typically evaluated, what sponsors should prepare and where deals commonly stall.",
  "primary_keyword": "LP equity for multifamily acquisitions",
  "search_intent": "commercial"
}}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    generated = extract_json(
        response.output_text
    )

    if isinstance(generated, dict):
        generated = generated.get(
            "topics",
            [],
        )

    if not isinstance(generated, list):
        raise ValueError(
            "Topic generator did not return a JSON array."
        )

    existing_normalized = {
        normalize_topic(topic)
        for topic in avoid_topics
    }

    clean_topics = []
    seen = set()

    for item in generated:

        if not isinstance(item, dict):
            continue

        required = {
            "topic",
            "category",
            "summary",
            "primary_keyword",
            "search_intent",
        }

        if not required.issubset(item):
            continue

        normalized = normalize_topic(
            item["topic"]
        )

        if not normalized:
            continue

        if normalized in existing_normalized:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)

        clean_topics.append(item)

    if not clean_topics:
        raise RuntimeError(
            "Topic generator returned no usable new topics."
        )

    return clean_topics


def replenish_topics_if_needed(
    topics: list[dict],
    published: list[str],
) -> list[dict]:

    remaining = unused_topics(
        topics,
        published,
    )

    print(
        f"{len(remaining)} unused topics remain."
    )

    if len(remaining) >= MIN_UNUSED_TOPICS:
        return topics

    print(
        f"Topic reserve below {MIN_UNUSED_TOPICS}. "
        f"Generating {TOPIC_BATCH_SIZE} new SEO topics..."
    )

    new_topics = generate_new_topics(
        existing_topics=topics,
        published=published,
        count=TOPIC_BATCH_SIZE,
    )

    topics.extend(new_topics)

    save_json(
        TOPICS_FILE,
        topics,
    )

    print(
        f"Added {len(new_topics)} new topics."
    )

    return topics


def pick_topic(
    topics: list[dict],
    published: list[str],
) -> dict:

    available = unused_topics(
        topics,
        published,
    )

    if not available:
        raise RuntimeError(
            "No unused topics available after replenishment."
        )

    return available[0]


def generate(topic: dict) -> dict:

    client = OpenAI()

    primary_keyword = topic.get(
        "primary_keyword",
        topic["topic"],
    )

    search_intent = topic.get(
        "search_intent",
        "informational-commercial",
    )

    prompt = f"""
Write an original commercial real estate capital-markets article
for Valcrest Capital.

PRIMARY AUTHOR:
Tate Dewey, Co-Founder of Valcrest Capital.

SECONDARY VALCREST PROFESSIONAL:
Samuel Aureliano, Managing Partner of Valcrest Capital.

AUTHORSHIP RULES:

Tate Dewey MUST always be the primary named author.

The article should reinforce a clear entity association between:
- Tate Dewey
- Valcrest Capital
- commercial real estate
- CRE capital markets
- institutional equity
- financing
- acquisitions
- developments
- recapitalizations

Do this naturally.

Do NOT make the article about Tate personally.

Do NOT mention movies, acting, entertainment or any unrelated
background.

Samuel Aureliano may be naturally mentioned in some articles when
his inclusion makes sense.

Do not force Samuel's name into the article body.

If Samuel is included:
- Tate must still be the primary author.
- Present Samuel as part of Valcrest Capital.
- Do not invent quotations from Samuel.
- Do not attribute fabricated transactions, statistics or opinions
  to him.

TOPIC:
{topic['topic']}

PRIMARY SEO KEYWORD:
{primary_keyword}

SEARCH INTENT:
{search_intent}

CATEGORY:
{topic['category']}

ANGLE:
{topic['summary']}

BUSINESS OBJECTIVE:

The article should rank for commercially relevant CRE searches while
demonstrating that Tate Dewey and Valcrest Capital understand how
commercial real estate sponsors and capital providers evaluate
transactions.

The article should genuinely answer the searcher's question.

A reader with an active transaction should naturally understand why
speaking with a commercial real estate capital advisor could be useful.

SEO REQUIREMENTS:

- Answer the likely search query early.
- Use the primary keyword naturally.
- Use related CRE terminology naturally.
- Do not keyword-stuff.
- Use clear descriptive H2 and H3 headings.
- Make individual sections understandable on their own.
- Favor direct answers and useful specifics.
- Use lists where appropriate.
- Structure content so both traditional search engines and AI search
  systems can easily interpret it.
- Do not mention SEO, rankings or keywords.
- Do not fabricate market statistics.
- Do not cite fake reports, surveys or studies.
- Evergreen content is preferred.
- Avoid unnecessary dates unless relevant.

VOICE:

- Insider and practical.
- Sophisticated enough for CRE sponsors and investors.
- Clear, direct language.
- Confident but not boastful.
- Based on patterns commonly observed in conversations between
  sponsors and institutional capital providers.
- Avoid generic corporate jargon.
- Avoid repetitive AI-style filler.
- Avoid fake personal anecdotes.
- Avoid claiming direct experience that has not been established.

COMPLIANCE AND ACCURACY:

- Do not invent statistics.
- Do not invent Valcrest transactions.
- Do not invent investor names.
- Do not invent lender names.
- Do not invent quotations.
- Do not invent performance.
- Do not invent the number of investors or firms contacted.
- Do not imply Valcrest invests its own capital.
- Do not imply Valcrest guarantees funding.
- Do not imply investors will participate.
- Do not promise financing availability.
- Do not give legal advice.
- Do not give tax advice.
- Do not give securities advice.
- Do not give investment advice.
- Clearly distinguish hypothetical examples from actual transactions.

ARTICLE LENGTH:

Aim for approximately 1,000-1,400 words.

Prioritize usefulness over hitting an exact word count.

OUTPUT:

Return ONLY one valid JSON object with these keys:

"title"
Compelling SEO-aware title.
Ideally 45-68 characters.

"meta_description"
Approximately 140-160 characters.
Useful and click-worthy without sounding promotional.

"dek"
One-sentence introduction.

"category"
Short category.

"excerpt"
25-40 words.

"body_html"
Clean HTML using ONLY:

p
h2
h3
ul
ol
li
strong
em
blockquote

No h1.
No links.

The article should include:

- a direct opening explanation
- useful H2 and H3 sections
- actionable considerations
- investor or lender decision points where relevant
- common mistakes where relevant
- a concise practical conclusion

The article must be useful, specific and free of keyword stuffing.
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    return extract_json(
        response.output_text
    )


def quality_check(article: dict) -> None:

    required = {
        "title",
        "meta_description",
        "dek",
        "category",
        "excerpt",
        "body_html",
    }

    missing = required.difference(article)

    if missing:
        raise ValueError(
            f"Missing fields: {sorted(missing)}"
        )

    plain = re.sub(
        r"<[^>]+>",
        " ",
        article["body_html"],
    )

    words = re.findall(
        r"\b[\w'-]+\b",
        plain,
    )

    if len(words) < 850:
        raise ValueError(
            f"Article too short: {len(words)} words"
        )

    prohibited = [
        "guaranteed funding",
        "guaranteed return",
        "we invest our capital",
        "risk-free",
    ]

    lower = plain.lower()

    hits = [
        term
        for term in prohibited
        if term in lower
    ]

    if hits:
        raise ValueError(
            f"Prohibited claims found: {hits}"
        )

    article["meta_description"] = article["meta_description"].strip()

    if len(article["meta_description"]) > 170:
        article["meta_description"] = (
            article["meta_description"][:167].rsplit(" ", 1)[0] + "..."
        )


def article_template(
    article: dict,
    slug: str,
    today: date,
) -> str:

    title = html.escape(
        article["title"]
    )

    meta = html.escape(
        article["meta_description"],
        quote=True,
    )

    dek = html.escape(
        article["dek"]
    )

    category = html.escape(
        article["category"]
    )

    published = today.strftime(
        "%B %-d, %Y"
    )

    canonical = (
        f"{SITE_URL}/blog/{slug}.html"
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article["title"],
        "description": article["meta_description"],
        "datePublished": today.isoformat(),
        "dateModified": today.isoformat(),
        "mainEntityOfPage": canonical,
        "author": {
    "@type": "Person",
    "name": PRIMARY_AUTHOR,
    "url": f"{SITE_URL}/tate-dewey",
    "jobTitle": "Co-Founder",
    "worksFor": {
        "@type": "Organization",
        "name": "Valcrest Capital",
        "url": SITE_URL,
    },
},
        "publisher": {
            "@type": "Organization",
            "name": "Valcrest Capital",
            "url": SITE_URL,
        },
    }

    return f'''<!doctype html>
<html lang="en">

<head>

<meta charset="utf-8">

<meta name="viewport" content="width=device-width,initial-scale=1">

<title>{title} | Valcrest Capital</title>

<meta name="description" content="{meta}">

<link rel="canonical" href="{canonical}">

<script type="application/ld+json">
{json.dumps(schema, separators=(",", ":"))}
</script>

<style>

:root{{
--ink:#161b1e;
--muted:#6f6a61;
--paper:#f4efe5;
--white:#fff;
--line:rgba(22,27,30,.18);
--gold:#b89454;
--forest:#0e171b
}}

*{{
box-sizing:border-box
}}

body{{
margin:0;
background:var(--paper);
color:var(--ink);
font-family:Inter,ui-sans-serif,system-ui,-apple-system,
BlinkMacSystemFont,"Segoe UI",sans-serif;
line-height:1.75
}}

a{{
color:inherit
}}

.wrap{{
width:min(820px,calc(100% - 36px));
margin:auto
}}

.header{{
background:var(--forest);
color:#fff;
padding:25px 0
}}

.nav{{
display:flex;
justify-content:space-between;
align-items:center
}}

.nav a{{
text-decoration:none;
font-size:13px;
font-weight:850;
text-transform:uppercase
}}

.hero{{
padding:78px 0 50px;
border-bottom:1px solid var(--line)
}}

.tag{{
font-size:11px;
font-weight:900;
letter-spacing:.14em;
text-transform:uppercase;
color:#8a6c38
}}

.hero h1{{
font-family:Georgia,serif;
font-size:clamp(40px,7vw,68px);
line-height:1.04;
margin:14px 0 20px
}}

.dek{{
font-size:20px;
color:var(--muted)
}}

.byline{{
margin-top:26px;
font-size:13px;
font-weight:800
}}

.article{{
padding:55px 0 85px
}}

.article p,
.article li{{
font-size:18px
}}

.article h2{{
font-family:Georgia,serif;
font-size:34px;
line-height:1.18;
margin:48px 0 14px
}}

.article h3{{
font-size:22px;
margin:32px 0 8px
}}

.article blockquote{{
margin:38px 0;
padding:26px 28px;
background:#fff;
border-left:4px solid var(--gold)
}}

.author{{
margin-top:60px;
padding:30px;
background:#fff;
border:1px solid var(--line)
}}

.author h2{{
margin:0 0 8px;
font-size:26px
}}

.team-note{{
margin-top:22px;
padding-top:20px;
border-top:1px solid var(--line)
}}

.cta{{
margin-top:30px;
padding:30px;
background:var(--forest);
color:#fff
}}

.cta a{{
color:#fff;
font-weight:850
}}

footer{{
background:var(--forest);
color:#ddd;
padding:35px 0;
font-size:13px
}}

@media(max-width:700px){{
.article p,
.article li{{
font-size:17px
}}
}}

</style>

</head>

<body>

<header class="header">

<div class="wrap nav">

<a href="/">
Valcrest Capital
</a>

<a href="/blog/">
Insights
</a>

</div>

</header>

<main>

<section class="hero">

<div class="wrap">

<div class="tag">
{category}
</div>

<h1>
{title}
</h1>

<p class="dek">
{dek}
</p>

<div class="byline">
By <a href="/tate-dewey">{PRIMARY_AUTHOR}</a>, Co-Founder of Valcrest Capital · {published}
</div>

</div>

</section>

<article class="article">

<div class="wrap">

{article['body_html']}

<section class="author">

<h2>
About {PRIMARY_AUTHOR}
</h2>

<p>
{PRIMARY_AUTHOR} is Co-Founder of Valcrest Capital, where he works
with commercial real estate sponsors on institutional equity,
financing, acquisitions, developments and recapitalizations.
</p>

<div class="team-note">

<strong>
Valcrest Capital
</strong>

<p>
{PRIMARY_AUTHOR} works alongside {PARTNER}, Managing Partner of
Valcrest Capital, on commercial real estate capital advisory
assignments.
</p>

</div>

</section>

<section class="cta">

<strong>
Evaluating the capital strategy for a commercial real estate opportunity?
</strong>

<p>
Visit
<a href="/">
Valcrest Capital
</a>
to learn more about our capital advisory work.
</p>

</section>

</div>

</article>

</main>

<footer>

<div class="wrap">

© {today.year} Valcrest Capital.
This material is for general informational purposes and is not an
offer to sell or a solicitation to purchase any security.

</div>

</footer>

</body>

</html>'''


def update_index(
    article: dict,
    slug: str,
    today: date,
) -> None:

    text = INDEX_FILE.read_text(
        encoding="utf-8"
    )

    marker = "<!-- ARTICLES_START -->"

    card = f'''
      <a class="card" href="/blog/{slug}.html">

        <span class="tag">
          {html.escape(article['category'])}
        </span>

        <h2>
          {html.escape(article['title'])}
        </h2>

        <p>
          {html.escape(article['excerpt'])}
        </p>

        <span class="meta">
          By {PRIMARY_AUTHOR} · {today.strftime("%B %-d, %Y")}
        </span>

      </a>'''

    if f'/blog/{slug}.html' not in text:

        text = text.replace(
            marker,
            marker + card,
            1,
        )

        INDEX_FILE.write_text(
            text,
            encoding="utf-8",
        )


def update_sitemap(
    slug: str,
    today: date,
) -> None:

    sitemap = BLOG_DIR / "sitemap.xml"

    urls = [
        f"{SITE_URL}/",
        f"{SITE_URL}/blog/",
    ]

    urls.extend(
        f"{SITE_URL}/blog/{p.name}"
        for p in sorted(
            BLOG_DIR.glob("*.html")
        )
        if p.name != "index.html"
    )

    body = "\n".join(
        f"  <url><loc>{url}</loc><lastmod>{today.isoformat()}</lastmod></url>"
        for url in urls
    )

    sitemap.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n",
        encoding="utf-8",
    )


def main() -> None:

    topics = load_json(
        TOPICS_FILE,
        [],
    )

    published = load_json(
        PUBLISHED_FILE,
        [],
    )

    topics = replenish_topics_if_needed(
        topics,
        published,
    )

    topic = pick_topic(
        topics,
        published,
    )

    print(
        f"Selected topic: {topic['topic']}"
    )

    article = generate(
        topic
    )

    quality_check(
        article
    )

    today = date.today()

    slug = slugify(
        article["title"]
    )

    destination = (
        BLOG_DIR / f"{slug}.html"
    )

    if destination.exists():
        raise FileExistsError(
            destination
        )

    destination.write_text(
        article_template(
            article,
            slug,
            today,
        ),
        encoding="utf-8",
    )

    update_index(
        article,
        slug,
        today,
    )

    update_sitemap(
        slug,
        today,
    )

    published.append(
        topic["topic"]
    )

    save_json(
        PUBLISHED_FILE,
        published,
    )

    print(
        f"Published {destination.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
