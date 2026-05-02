"""
Web Intelligence Service — automated company scanning.

Steps per scan:
  1. News & press search via Serper API (parallel queries)
  2. JSE stock data via yfinance + SENS search
  3. Company website scrape (leadership, LinkedIn URL)
  4. AI synthesis → intelligence_summary, key_signals, timing, approach
  5. AI contact discovery → role recommendations, departments
  6. LinkedIn URL generation
  7. Contact source map + publicly found contacts

Each step fails silently — a partial failure never kills the full scan.
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

import httpx

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Company, ContactDiscovery, WebIntelligenceReport
from sqlalchemy import select

try:
    from bs4 import BeautifulSoup  # type: ignore
    _BS4 = True
except ImportError:
    _BS4 = False

try:
    import yfinance as yf  # type: ignore
    _YFINANCE = True
except ImportError:
    _YFINANCE = False


# ── Constants ─────────────────────────────────────────────────────────────────

_SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WavyOS/1.0; research-bot)"
}
_LEADERSHIP_PATHS = [
    "/about", "/about-us", "/team", "/leadership",
    "/management", "/executive-team", "/our-team", "/board",
]
_KNOWN_JSE_TICKERS = {
    "kumba iron ore": "KIO.JO",
    "exxaro resources": "EXX.JO",
    "exxaro": "EXX.JO",
    "harmony gold": "HAR.JO",
    "harmony gold mining": "HAR.JO",
    "grindrod": "GND.JO",
    "santam": "SNT.JO",
}

_INTEL_SYSTEM = (
    "You are a senior B2B sales intelligence analyst working for a founder who sells "
    "accounts receivable and cash-flow management solutions to South African corporates. "
    "You have been given raw intelligence gathered from public sources about a target company. "
    "Synthesise this into a concise, actionable brief.\n\n"
    "Prioritise: signals that suggest cash-flow timing pressure, receivables cycle changes, "
    "expansion into new markets (which stretches working capital), leadership changes "
    "(new CFOs are often open to new solutions), cost reduction initiatives, and any public "
    "statements about financial performance challenges.\n\n"
    "Be specific. Reference actual sources where possible. Do not pad. Do not use generic "
    "language. Do not say 'AI-powered.' Return only valid JSON."
)

_CONTACT_SYSTEM = (
    "You are a B2B sales targeting advisor. Based on the company profile and intelligence "
    "below, identify the most likely decision-makers and influencers for a solution that "
    "improves accounts receivable visibility and cash-flow management. Prioritise by "
    "likelihood to care about this problem. Be specific about why each role matters at "
    "this company specifically. Return only valid JSON."
)


# ── Entry point ───────────────────────────────────────────────────────────────

async def run_full_scan(company_id: int) -> None:
    """
    Background task entry point.
    Opens its own DB session — safe to run as FastAPI BackgroundTask.
    """
    async with AsyncSessionLocal() as db:
        # Find or create the report record
        result = await db.execute(
            select(WebIntelligenceReport)
            .where(WebIntelligenceReport.company_id == company_id)
            .order_by(WebIntelligenceReport.created_at.desc())
            .limit(1)
        )
        report = result.scalar_one_or_none()

        if not report:
            report = WebIntelligenceReport(
                company_id=company_id,
                scan_triggered_by="auto",
            )
            db.add(report)

        report.scan_status = "running"
        report.scan_started_at = datetime.utcnow()
        report.scan_error = None
        await db.commit()
        await db.refresh(report)

        company = await db.get(Company, company_id)
        if not company:
            report.scan_status = "failed"
            report.scan_error = "Company not found"
            await db.commit()
            return

        try:
            # ── Parallel gathering ───────────────────────────────────────────
            news_coro = _search_news(company.name) if settings.SERPER_API_KEY else _noop([])
            jse_coro = _fetch_jse_data(company.name) if settings.JSE_DATA_ENABLED else _noop(None)
            web_coro = (
                _scrape_website(company.website)
                if (company.website and settings.WEBSITE_SCRAPE_ENABLED)
                else _noop({})
            )

            news_res, jse_res, web_res = await asyncio.gather(
                news_coro, jse_coro, web_coro,
                return_exceptions=True,
            )

            # ── Persist partial results ──────────────────────────────────────
            news = news_res if not isinstance(news_res, Exception) else []
            jse = jse_res if not isinstance(jse_res, Exception) else None
            web = web_res if not isinstance(web_res, Exception) else {}

            report.news_articles = json.dumps(news)
            report.press_releases = json.dumps([])
            report.public_financial_signals = json.dumps([])
            report.company_website_url = company.website

            if jse:
                report.is_jse_listed = jse.get("is_listed", False)
                report.jse_ticker = jse.get("ticker")
                sd = jse.get("stock_data")
                report.latest_stock_data = json.dumps(sd) if sd else None
                report.sens_announcements = json.dumps(jse.get("sens", []))
            else:
                report.sens_announcements = json.dumps([])

            report.linkedin_company_url = web.get("linkedin_url")
            report.leadership_page_url = web.get("leadership_page_url")
            report.leadership_mentions = json.dumps(web.get("leadership_mentions", []))

            await db.commit()

            # ── AI Synthesis ─────────────────────────────────────────────────
            synthesis = await _synthesise(
                company_name=company.name,
                industry=company.industry or "",
                news=news,
                sens=jse.get("sens", []) if jse else [],
                leadership=web.get("leadership_mentions", []) if web else [],
            )

            report.intelligence_summary = synthesis.get("intelligence_summary")
            report.key_signals = json.dumps(synthesis.get("key_signals", []))
            report.timing_assessment = synthesis.get("timing_assessment")
            report.recommended_approach = synthesis.get("recommended_approach")
            report.is_demo = synthesis.get("is_demo", False)
            await db.commit()

            # ── Contact Discovery ─────────────────────────────────────────────
            contact_data = await _discover_contacts(
                company_name=company.name,
                industry=company.industry or "",
                country=company.country or "South Africa",
                summary=synthesis.get("intelligence_summary", ""),
                signals=synthesis.get("key_signals", []),
            )

            # Save / update ContactDiscovery
            disc_result = await db.execute(
                select(ContactDiscovery)
                .where(ContactDiscovery.company_id == company_id)
                .order_by(ContactDiscovery.created_at.desc())
                .limit(1)
            )
            cd = disc_result.scalar_one_or_none()
            if not cd:
                cd = ContactDiscovery(company_id=company_id)
                db.add(cd)

            cd.web_intelligence_id = report.id
            cd.recommended_roles = json.dumps(contact_data.get("recommended_roles", []))
            cd.recommended_departments = json.dumps(contact_data.get("recommended_departments", []))
            cd.linkedin_search_urls = json.dumps(
                _build_linkedin_urls(company.name, contact_data.get("recommended_roles", []))
            )
            cd.linkedin_company_page = web.get("linkedin_url") if web else None
            cd.contact_sources = json.dumps(
                _build_contact_sources(company, report, jse.get("sens", []) if jse else [])
            )
            cd.publicly_listed_contacts = json.dumps(
                _extract_public_contacts(
                    web.get("leadership_mentions", []) if web else [],
                    news,
                )
            )
            cd.is_demo = synthesis.get("is_demo", False)
            await db.commit()

            report.scan_status = "complete"
            report.scan_completed_at = datetime.utcnow()
            await db.commit()

        except Exception as exc:
            report.scan_status = "failed"
            report.scan_error = str(exc)[:500]
            report.scan_completed_at = datetime.utcnow()
            await db.commit()


async def _noop(value):
    return value


# ── Step 1: News search ───────────────────────────────────────────────────────

async def _search_news(company_name: str) -> list:
    if not settings.SERPER_API_KEY:
        return []

    queries = [
        f"{company_name} news 2024 2025",
        f"{company_name} financial results annual report",
        f"{company_name} press release expansion deal acquisition",
        f"{company_name} SENS announcement JSE",
        f"{company_name} CEO CFO leadership appointment",
        f"{company_name} receivables cash flow working capital",
    ]

    results: list = []
    seen_urls: set = set()

    async with httpx.AsyncClient(timeout=15) as client:
        tasks = [
            client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": settings.SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"q": q, "num": 5},
            )
            for q in queries
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for resp in responses:
        if isinstance(resp, Exception):
            continue
        try:
            data = resp.json()
            for item in data.get("organic", []):
                url = item.get("link", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                results.append({
                    "title": item.get("title", ""),
                    "url": url,
                    "source": item.get("source", ""),
                    "snippet": item.get("snippet", ""),
                    "published_at": item.get("date"),
                })
        except Exception:
            continue

    return results[: settings.MAX_NEWS_RESULTS]


# ── Step 2: JSE / yfinance ────────────────────────────────────────────────────

async def _fetch_jse_data(company_name: str) -> dict:
    ticker = _resolve_jse_ticker(company_name)

    # Try Serper search for ticker if not in known map
    if not ticker and settings.SERPER_API_KEY:
        ticker = await _search_jse_ticker(company_name)

    jse_result: dict = {"is_listed": bool(ticker), "ticker": None, "stock_data": None, "sens": []}

    if ticker:
        jse_result["ticker"] = ticker.replace(".JO", "")
        if _YFINANCE:
            jse_result["stock_data"] = await _yfinance_fetch(ticker)

        if settings.SERPER_API_KEY:
            jse_result["sens"] = await _search_sens(company_name)

    return jse_result


def _resolve_jse_ticker(name: str) -> Optional[str]:
    return _KNOWN_JSE_TICKERS.get(name.lower().strip())


async def _search_jse_ticker(company_name: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": f"{company_name} JSE ticker symbol listed JSE:", "num": 5},
            )
            data = resp.json()
            for item in data.get("organic", []):
                text = (item.get("title", "") + " " + item.get("snippet", "")).upper()
                m = re.search(r"\bJSE:\s*([A-Z]{2,6})\b", text)
                if m:
                    return f"{m.group(1)}.JO"
                m = re.search(r"\b([A-Z]{2,6}):SJ\b", text)
                if m:
                    return f"{m.group(1)}.JO"
    except Exception:
        pass
    return None


async def _yfinance_fetch(ticker: str) -> Optional[dict]:
    try:
        loop = asyncio.get_event_loop()

        def _sync_fetch():
            t = yf.Ticker(ticker)
            info = t.info
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            prev = info.get("regularMarketPreviousClose")
            chg = round((price - prev) / prev * 100, 2) if price and prev else None
            mc = info.get("marketCap")
            mc_str = (
                f"R{mc/1e9:.1f}bn" if mc and mc >= 1e9
                else (f"R{mc/1e6:.0f}m" if mc else None)
            )
            return {
                "price": price,
                "change_pct": chg,
                "market_cap": mc_str,
                "currency": info.get("currency", "ZAR"),
                "week_52_high": info.get("fiftyTwoWeekHigh"),
                "week_52_low": info.get("fiftyTwoWeekLow"),
                "last_updated": datetime.utcnow().isoformat(),
            }

        return await loop.run_in_executor(None, _sync_fetch)
    except Exception:
        return None


async def _search_sens(company_name: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": f"{company_name} SENS site:sens.co.za OR site:jse.co.za", "num": 10},
            )
            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "date": item.get("date"),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("organic", [])
            ][:10]
    except Exception:
        return []


# ── Step 3: Website scrape ────────────────────────────────────────────────────

async def _scrape_website(website_url: str) -> dict:
    if not _BS4 or not website_url:
        return {}

    base = website_url.rstrip("/")
    result = {"linkedin_url": None, "leadership_page_url": None, "leadership_mentions": []}
    fetched = 0

    async with httpx.AsyncClient(
        headers=_SCRAPE_HEADERS, timeout=10, follow_redirects=True
    ) as client:
        # Homepage
        try:
            resp = await client.get(base)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                result["linkedin_url"] = _find_linkedin(soup)
                fetched += 1
        except Exception:
            pass

        await asyncio.sleep(2)

        # Leadership pages
        for path in _LEADERSHIP_PATHS:
            if fetched >= 3:
                break
            try:
                resp = await client.get(f"{base}{path}")
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    people = _extract_people(soup)
                    if people:
                        result["leadership_mentions"].extend(people)
                        result["leadership_page_url"] = f"{base}{path}"
                        fetched += 1
                        if not result["linkedin_url"]:
                            result["linkedin_url"] = _find_linkedin(soup)
                        break
                await asyncio.sleep(2)
            except Exception:
                continue

    return result


def _find_linkedin(soup) -> Optional[str]:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com/company" in href:
            return href if href.startswith("http") else f"https://linkedin.com{href}"
    return None


def _extract_people(soup) -> list:
    people = []
    for el in soup.find_all(
        ["div", "article", "li", "section"],
        class_=lambda c: c and any(
            k in c.lower()
            for k in ["team", "member", "leader", "exec", "board", "director", "management", "person"]
        ) if c else False,
    ):
        texts = [t.strip() for t in el.stripped_strings if t.strip() and len(t.strip()) > 2]
        if len(texts) >= 2:
            name = texts[0]
            role = texts[1] if len(texts[1]) < 100 else None
            if name and role and 1 < len(name.split()) <= 5:
                people.append({"name": name, "role": role, "confidence": "high"})
    return people[:10]


# ── Step 4: AI Intelligence Synthesis ────────────────────────────────────────

async def _synthesise(
    company_name: str,
    industry: str,
    news: list,
    sens: list,
    leadership: list,
) -> dict:
    if not settings.OPENAI_API_KEY:
        return {
            "intelligence_summary": (
                f"{company_name} is a {industry} company in South Africa. "
                "Live intelligence is in demo mode — add OPENAI_API_KEY and SERPER_API_KEY "
                "to .env to enable full scanning."
            ),
            "key_signals": [
                {
                    "signal": "Demo mode — real signals appear after API keys are configured",
                    "relevance": "low",
                    "signal_type": "other",
                    "source_url": None,
                }
            ],
            "timing_assessment": (
                "Timing assessment requires live data. Configure OPENAI_API_KEY and "
                "SERPER_API_KEY to enable."
            ),
            "recommended_approach": (
                "Configure OPENAI_API_KEY and SERPER_API_KEY in your .env file to "
                "enable full AI synthesis."
            ),
            "is_demo": True,
        }

    import openai  # local import — only used when key present

    payload = json.dumps(
        {
            "company_name": company_name,
            "industry": industry,
            "news_articles": [
                {"title": n.get("title"), "snippet": n.get("snippet"),
                 "source": n.get("source"), "url": n.get("url")}
                for n in news[:10]
            ],
            "sens_announcements": [
                {"title": s.get("title"), "snippet": s.get("snippet"), "url": s.get("url")}
                for s in sens
            ],
            "leadership_mentions": leadership[:5],
        },
        indent=2,
    )

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _INTEL_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Synthesise intelligence for this company:\n\n{payload}\n\n"
                        "Return JSON with keys: intelligence_summary, key_signals "
                        "(array with signal, source_url, relevance, signal_type), "
                        "timing_assessment, recommended_approach"
                    ),
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as exc:
        return {
            "intelligence_summary": f"AI synthesis error: {str(exc)[:150]}",
            "key_signals": [],
            "timing_assessment": None,
            "recommended_approach": None,
        }


# ── Step 5: Contact Discovery ─────────────────────────────────────────────────

async def _discover_contacts(
    company_name: str,
    industry: str,
    country: str,
    summary: str,
    signals: list,
) -> dict:
    _demo = {
        "recommended_roles": [
            {
                "title": "Chief Financial Officer",
                "seniority": "C-suite",
                "department": "Finance",
                "why": "Ultimate owner of receivables risk and working capital strategy.",
                "priority": 1,
            },
            {
                "title": "Group Financial Manager",
                "seniority": "Senior Management",
                "department": "Finance",
                "why": "Day-to-day owner of cash-flow reporting and receivables tracking.",
                "priority": 2,
            },
            {
                "title": "Head of Treasury",
                "seniority": "Senior Management",
                "department": "Finance",
                "why": "Directly responsible for working capital optimisation.",
                "priority": 3,
            },
        ],
        "recommended_departments": [
            {
                "department": "Group Finance",
                "reason": "Primary buyer and user of receivables management solutions",
            },
            {
                "department": "Treasury",
                "reason": "Manages working capital and liquidity directly",
            },
        ],
    }

    if not settings.OPENAI_API_KEY:
        return _demo

    import openai

    payload = json.dumps(
        {
            "company_name": company_name,
            "industry": industry,
            "country": country,
            "intelligence_summary": summary,
            "key_signals": signals[:5],
        },
        indent=2,
    )

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _CONTACT_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Company profile:\n\n{payload}\n\n"
                        "Return JSON with keys: recommended_roles (array with title, seniority, "
                        "department, why, priority 1-3), recommended_departments (array with "
                        "department, reason)"
                    ),
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return _demo


# ── LinkedIn URL Builder ──────────────────────────────────────────────────────

def _build_linkedin_urls(company_name: str, roles: list) -> list:
    ec = quote_plus(company_name)
    urls = []

    for role in roles[:3]:
        title = role.get("title", "")
        et = quote_plus(title)
        urls.append({
            "label": f"{title} at {company_name}",
            "url": f"https://www.linkedin.com/search/results/people/?company={ec}&title={et}",
            "description": f"Direct search for {title}",
        })

    urls += [
        {
            "label": f"Finance leadership at {company_name}",
            "url": f"https://www.linkedin.com/search/results/people/?company={ec}&title=Finance+Director",
            "description": "Finance directors and senior finance managers",
        },
        {
            "label": f"Treasury & working capital at {company_name}",
            "url": f"https://www.linkedin.com/search/results/people/?company={ec}&keywords=treasury+working+capital",
            "description": "Treasury, working capital, and cash management roles",
        },
        {
            "label": f"All finance roles at {company_name}",
            "url": f"https://www.linkedin.com/search/results/people/?company={ec}&keywords=finance+CFO+treasury",
            "description": "Broad finance department search",
        },
    ]

    # Deduplicate
    seen: set = set()
    unique = []
    for u in urls:
        if u["url"] not in seen:
            seen.add(u["url"])
            unique.append(u)
    return unique


# ── Contact Sources ───────────────────────────────────────────────────────────

def _build_contact_sources(company, report: WebIntelligenceReport, sens: list) -> list:
    sources = []
    if company.website:
        sources.append({
            "source_type": "company_website",
            "url": company.website,
            "description": f"{company.name} official website — check About/Leadership/Team sections",
            "expected_contacts": "C-suite, divisional heads, board",
        })
    if report.leadership_page_url:
        sources.append({
            "source_type": "leadership_page",
            "url": report.leadership_page_url,
            "description": "Leadership page found during web scan",
            "expected_contacts": "Named executives with roles",
        })
    for s in sens[:3]:
        if s.get("url"):
            sources.append({
                "source_type": "sens_announcement",
                "url": s["url"],
                "description": s.get("title", "SENS announcement"),
                "expected_contacts": "May name specific executives",
            })
    return sources


# ── Public Contacts Extractor ─────────────────────────────────────────────────

def _extract_public_contacts(leadership_mentions: list, news: list) -> list:
    contacts = []
    seen: set = set()

    for m in leadership_mentions:
        name = m.get("name", "").strip()
        if name and name not in seen and len(name.split()) >= 2:
            seen.add(name)
            contacts.append({
                "name": name,
                "role": m.get("role"),
                "source_url": None,
                "source_type": "company_website",
                "confidence": "high",
            })

    _role_kw = [
        "CFO", "CEO", "CTO", "COO", "Director", "Manager",
        "Head", "Chief", "Officer", "President", "VP",
    ]
    for article in news[:5]:
        snippet = article.get("snippet", "")
        for kw in _role_kw:
            pat = (
                r"([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)"
                r"(?:,? (?:the |new |appointed |as )?(?:" + kw + r"))"
            )
            for match in re.findall(pat, snippet):
                name = match.strip()
                if name not in seen and len(name.split()) >= 2:
                    seen.add(name)
                    contacts.append({
                        "name": name,
                        "role": kw,
                        "source_url": article.get("url"),
                        "source_type": "news_article",
                        "confidence": "medium",
                    })

    return contacts[:10]
