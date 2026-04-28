import json
import time
import structlog
from typing import Optional

from app.config import settings

log = structlog.get_logger()

# ── Demo outputs ──────────────────────────────────────────────────────────────

DEMO_RESEARCH = {
    "overview": "This company operates in a capital-intensive sector with significant receivables exposure. Recent expansion activity and sector headwinds suggest cash cycle pressure may be building.",
    "recent_signals": [
        "Announced capacity expansion in Q1, likely stretching capex commitments",
        "Sector peers reporting 15–20% longer payment cycles from government clients",
        "New leadership in finance division — potential policy reset underway",
        "Rising input costs squeezing operating margins by an estimated 3–5%",
    ],
    "cashflow_pressure_points": [
        "Receivables from large clients often extend beyond 60 days",
        "Export revenue subject to FX volatility, affecting cash predictability",
        "Seasonal working capital demand peaks in Q2 and Q4",
        "Capex commitments may limit short-term liquidity flexibility",
    ],
    "buyer_personas": [
        {"title": "CFO", "why": "Controls treasury policy and approves receivables financing decisions"},
        {"title": "Financial Director", "why": "Manages day-to-day cash flow and works closely with banks"},
        {"title": "Head of Credit", "why": "Owns the receivables aging process and collection strategy"},
    ],
    "outreach_angle": "Position as a receivables acceleration partner during a period of working capital strain — highlight speed of access to cash without diluting equity or adding bank leverage.",
    "confidence_score": 0.72,
    "source_links": [],
    "is_demo": True,
}

DEMO_BRIEF = {
    "executive_signal": "The company is expanding operations while facing extended payment cycles from key clients — receivables are likely stretching beyond 60 days, creating a working capital gap.",
    "why_it_matters": "When receivables extend and capex commitments are active, the CFO faces a liquidity timing mismatch. This creates urgency around off-balance-sheet financing options. The window to engage is now, before they lock in a bank facility.",
    "receivables_blind_spots": [
        "Large client concentration may mask true receivables risk in aging reports",
        "FX-denominated receivables may be underhedged given recent volatility",
        "Internal collection targets may not reflect actual cash receipt timing",
    ],
    "operational_impact": "Delayed cash inflows during expansion phases force the business to either slow down investment or draw on revolving credit — both of which have direct cost implications the CFO will feel acutely.",
    "suggested_action": "Lead with a 10-minute discovery call framed around how peers in the sector are handling receivables timing — not a product pitch. Use sector benchmarks as the hook.",
    "conversation_opener": "Are you finding that your receivables cycle is lengthening as your largest clients tighten their own payment terms this year?",
    "is_demo": True,
}

DEMO_OUTREACH = {
    "linkedin_message": "Hi [Name] — noticed [Company] is navigating expansion while sector payment cycles lengthen. Worth a quick chat on receivables timing?",
    "email_subject": "Working capital timing during [Company]'s expansion phase",
    "email_body": "Hi [Name],\n\nI've been following [Company]'s growth and noticed the expansion activity coinciding with broader sector pressure on receivables cycles.\n\nWe work with finance leaders in your sector who are finding that receivables timing gaps are creating friction during exactly these periods.\n\nWould you be open to a 10-minute call to compare notes on how peers are handling it?\n\nBest,\n[Your Name]",
    "followup_message": "Hi [Name] — following up on my note from last week. Happy to share a brief on receivables benchmarks for your sector if useful. Let me know.",
    "gatekeeper_version": "Hi — I'm hoping to connect with [Name] regarding a working capital insight specific to [Company]'s sector. Could you point me in the right direction?",
    "technical_validator_version": "Hi [Name] — I understand you're involved in [Company]'s financial systems side. I'm reaching out about receivables cycle data and how finance teams are using it operationally. Would a brief exchange be useful?",
    "is_demo": True,
}


# ── AI calls ──────────────────────────────────────────────────────────────────

async def research_company(name: str, website: Optional[str] = None, industry: Optional[str] = None) -> dict:
    if not settings.OPENAI_API_KEY:
        return {**DEMO_RESEARCH, "is_demo": True}

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Company: {name}
Website: {website or 'not provided'}
Industry: {industry or 'not provided'}

Return a JSON object with exactly these keys:
- overview (string)
- recent_signals (array of strings, 3-5 items)
- cashflow_pressure_points (array of strings, 3-5 items)
- buyer_personas (array of objects with "title" and "why" keys)
- outreach_angle (string)
- confidence_score (float 0.0-1.0)
- source_links (array of strings, may be empty)
- is_demo (boolean, set to false)"""

        system = """You are a B2B sales intelligence analyst specializing in cash-flow and receivables risk signals. Your output helps a founder identify the right time and angle to approach a CFO or finance director. Be concise, specific, and avoid hype. Focus on: recent business signals, receivables exposure, payment cycle risk, operational cost pressure, and concentration risk. Do not say "AI-powered." Return only valid JSON matching the schema provided."""

        t0 = time.time()
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1200,
        )
        duration = time.time() - t0
        usage = resp.usage

        log.info("ai_research_complete", company=name, duration=round(duration, 2),
                 tokens=usage.total_tokens if usage else None)

        data = json.loads(resp.choices[0].message.content)
        data["is_demo"] = False
        return data

    except Exception as e:
        log.error("ai_research_failed", company=name, error=str(e))
        return {**DEMO_RESEARCH, "is_demo": True}


async def generate_signal_brief(company_name: str, research_data: dict) -> dict:
    if not settings.OPENAI_API_KEY:
        return {**DEMO_BRIEF, "is_demo": True}

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Company: {company_name}

Research context:
Overview: {research_data.get('overview', '')}
Recent signals: {json.dumps(research_data.get('recent_signals', []))}
Cashflow pressures: {json.dumps(research_data.get('cashflow_pressure_points', []))}
Outreach angle: {research_data.get('outreach_angle', '')}

Return a JSON object with exactly these keys:
- executive_signal (1-2 sentences)
- why_it_matters (2-3 sentences)
- receivables_blind_spots (array of strings, 2-4 items)
- operational_impact (string)
- suggested_action (string)
- conversation_opener (a single question or statement to open a CFO conversation)
- is_demo (boolean, set to false)"""

        system = """You are a CFO-level strategic advisor writing a private signal brief for a founder preparing to approach a finance decision-maker. Write with precision and restraint. Avoid buzzwords. Each point must be specific to the company's situation. The conversation opener must feel natural, not salesy. Return only valid JSON."""

        t0 = time.time()
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
        )
        duration = time.time() - t0
        usage = resp.usage

        log.info("ai_brief_complete", company=company_name, duration=round(duration, 2),
                 tokens=usage.total_tokens if usage else None)

        data = json.loads(resp.choices[0].message.content)
        data["is_demo"] = False
        return data

    except Exception as e:
        log.error("ai_brief_failed", company=company_name, error=str(e))
        return {**DEMO_BRIEF, "is_demo": True}


async def generate_outreach(contact_name: str, contact_role: str, company_name: str,
                             brief_data: dict, tone: str = "professional") -> dict:
    if not settings.OPENAI_API_KEY:
        return {**DEMO_OUTREACH, "is_demo": True}

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Contact: {contact_name}, {contact_role} at {company_name}
Tone: {tone}

Signal brief context:
Executive signal: {brief_data.get('executive_signal', '')}
Conversation opener: {brief_data.get('conversation_opener', '')}
Suggested action: {brief_data.get('suggested_action', '')}

Return a JSON object with exactly these keys:
- linkedin_message (string, under 200 characters)
- email_subject (string)
- email_body (string, max 6 lines)
- followup_message (string)
- gatekeeper_version (string)
- technical_validator_version (string)
- is_demo (boolean, set to false)"""

        system = """You are a B2B outreach specialist writing cold outreach for a founder approaching finance decision-makers. Messages must be concise, specific, non-salesy, and reference real business context. Never use phrases like "hope this finds you well" or "I'd love to connect." Return only valid JSON."""

        t0 = time.time()
        resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
        )
        duration = time.time() - t0
        usage = resp.usage

        log.info("ai_outreach_complete", contact=contact_name, company=company_name,
                 duration=round(duration, 2), tokens=usage.total_tokens if usage else None)

        data = json.loads(resp.choices[0].message.content)
        data["is_demo"] = False
        return data

    except Exception as e:
        log.error("ai_outreach_failed", contact=contact_name, error=str(e))
        return {**DEMO_OUTREACH, "is_demo": True}


async def score_lead(company_name: str, contact_role: str) -> float:
    return 0.65
