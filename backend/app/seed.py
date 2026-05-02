import json
from datetime import datetime, timedelta, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import PipelineStage, Company, Contact, ResearchReport, SignalBrief, Task, OutreachDraft, WeeklySnapshot, WebIntelligenceReport, ContactDiscovery

PIPELINE_STAGES = [
    {"name": "Target Identified", "order_index": 1, "color": "#64748B"},
    {"name": "Researched", "order_index": 2, "color": "#3B82F6"},
    {"name": "Message Drafted", "order_index": 3, "color": "#8B5CF6"},
    {"name": "Contacted", "order_index": 4, "color": "#F59E0B"},
    {"name": "Replied", "order_index": 5, "color": "#10B981"},
    {"name": "Call Booked", "order_index": 6, "color": "#00C9A7"},
    {"name": "Brief Sent", "order_index": 7, "color": "#06B6D4"},
    {"name": "Pilot Proposed", "order_index": 8, "color": "#F97316"},
    {"name": "Won", "order_index": 9, "color": "#22C55E"},
    {"name": "Lost", "order_index": 10, "color": "#EF4444"},
]

SEED_COMPANIES = [
    {
        "name": "Kumba Iron Ore",
        "industry": "Mining",
        "country": "South Africa",
        "website": "https://www.angloamericankumba.com",
        "stage_name": "Researched",
    },
    {
        "name": "Exxaro Resources",
        "industry": "Mining",
        "country": "South Africa",
        "website": "https://www.exxaro.com",
        "stage_name": "Target Identified",
    },
    {
        "name": "Santam",
        "industry": "Insurance",
        "country": "South Africa",
        "website": "https://www.santam.co.za",
        "stage_name": "Message Drafted",
    },
    {
        "name": "Grindrod",
        "industry": "Logistics",
        "country": "South Africa",
        "website": "https://www.grindrod.co.za",
        "stage_name": "Contacted",
    },
    {
        "name": "Harmony Gold",
        "industry": "Mining",
        "country": "South Africa",
        "website": "https://www.harmony.co.za",
        "stage_name": "Target Identified",
    },
]

DEMO_RESEARCH_TEMPLATE = {
    "overview": "{name} operates in the {industry} sector in South Africa with significant revenue from commodity exports. The business faces working capital cycles tied to commodity price fluctuations and extended payment terms from major off-takers.",
    "signals": ["Reported 8% increase in operating costs in latest annual results", "New capital allocation framework announced — finance team under scrutiny", "Sector peers reporting longer receivables cycles from government contracts", "Currency hedging costs rising as ZAR volatility increases"],
    "cashflow_pressures": ["Export receivables typically extend 45–75 days depending on counterparty", "Commodity price swings create unpredictable cash flow windows", "Working capital strain during ramp-up phases of expansion projects", "Bank facility drawdowns increasing — cost of debt rising"],
    "buyer_personas": [{"title": "CFO", "why": "Controls receivables financing strategy and approves off-balance-sheet solutions"}, {"title": "Treasury Manager", "why": "Manages day-to-day liquidity and working capital facilities"}, {"title": "Financial Director", "why": "Bridges strategic and operational finance decisions"}],
    "outreach_angle": "Approach as a working capital timing partner during a period of expansion pressure — frame receivables acceleration as speed without leverage.",
    "confidence_score": 0.74,
    "source_links": [],
}

DEMO_BRIEF_TEMPLATE = {
    "executive_signal": "{name}'s expansion activity combined with rising input costs is creating a receivables timing gap — cash coming in slower than commitments going out.",
    "why_it_matters": "When receivables extend during a capex cycle, the CFO is caught between growth commitments and cash availability. This is precisely when off-balance-sheet working capital tools become attractive. The conversation needs to happen before they sign the next bank facility.",
    "receivables_blind_spots": ["Large customer concentration masks true aging risk in management accounts", "FX-denominated receivables may be underhedged given ZAR volatility", "Internal collection KPIs may not reflect actual cash receipt timing"],
    "operational_impact": "Delayed cash inflows during expansion slow reinvestment velocity and force drawdowns on revolving credit facilities — directly increasing finance charges at the worst possible time.",
    "suggested_action": "Lead with a sector benchmark comparison call. Use 10 minutes to surface how peers are managing receivables timing — don't pitch a product.",
    "conversation_opener": "Are you finding that your largest clients are stretching payment terms just as your own capex commitments are peaking this cycle?",
}

DEMO_CONTACTS = [
    {"name": "Thabo Nkosi", "role": "CFO", "contact_type": "Buyer"},
    {"name": "Lerato Dlamini", "role": "Financial Director", "contact_type": "Influencer"},
    {"name": "Sipho Mokoena", "role": "Treasury Manager", "contact_type": "Technical Validator"},
    {"name": "Zanele Khumalo", "role": "Executive Assistant to CFO", "contact_type": "Gatekeeper"},
    {"name": "Bongani Sithole", "role": "Head of Finance", "contact_type": "Buyer"},
]

DEMO_TASKS = [
    "Follow up with CFO contact within 48 hours",
    "Review latest annual report before outreach",
    "Draft signal brief and get it approved",
    "Send LinkedIn connection request to Financial Director",
    "Research latest results presentation",
]


async def run_seed():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing = await db.scalar(select(PipelineStage).limit(1))
        if existing:
            return

        # Create pipeline stages
        stage_map = {}
        for stage_data in PIPELINE_STAGES:
            stage = PipelineStage(**stage_data)
            db.add(stage)
            await db.flush()
            stage_map[stage.name] = stage.id

        await db.flush()

        # Create seed companies with demo data
        for i, company_data in enumerate(SEED_COMPANIES):
            stage_id = stage_map.get(company_data["stage_name"])
            company = Company(
                name=company_data["name"],
                industry=company_data["industry"],
                country=company_data["country"],
                website=company_data["website"],
                status="active",
                pipeline_stage_id=stage_id,
            )
            db.add(company)
            await db.flush()

            # Demo research report
            overview = DEMO_RESEARCH_TEMPLATE["overview"].format(
                name=company.name, industry=company.industry
            )
            research = ResearchReport(
                company_id=company.id,
                overview=overview,
                signals=json.dumps(DEMO_RESEARCH_TEMPLATE["signals"]),
                cashflow_pressures=json.dumps(DEMO_RESEARCH_TEMPLATE["cashflow_pressures"]),
                buyer_personas=json.dumps(DEMO_RESEARCH_TEMPLATE["buyer_personas"]),
                outreach_angle=DEMO_RESEARCH_TEMPLATE["outreach_angle"],
                confidence_score=DEMO_RESEARCH_TEMPLATE["confidence_score"],
                source_links=json.dumps([]),
                is_demo=True,
            )
            db.add(research)
            await db.flush()

            # Demo signal brief
            executive_signal = DEMO_BRIEF_TEMPLATE["executive_signal"].format(name=company.name)
            brief = SignalBrief(
                company_id=company.id,
                research_id=research.id,
                executive_signal=executive_signal,
                why_it_matters=DEMO_BRIEF_TEMPLATE["why_it_matters"],
                receivables_blind_spots=json.dumps(DEMO_BRIEF_TEMPLATE["receivables_blind_spots"]),
                operational_impact=DEMO_BRIEF_TEMPLATE["operational_impact"],
                suggested_action=DEMO_BRIEF_TEMPLATE["suggested_action"],
                conversation_opener=DEMO_BRIEF_TEMPLATE["conversation_opener"],
                is_demo=True,
            )
            db.add(brief)

            # Demo contact
            contact_data = DEMO_CONTACTS[i % len(DEMO_CONTACTS)]
            contact = Contact(
                company_id=company.id,
                name=contact_data["name"],
                role=contact_data["role"],
                contact_type=contact_data["contact_type"],
                outreach_status="Not contacted",
                is_demo=False,
            )
            db.add(contact)

            # Demo task
            task = Task(
                company_id=company.id,
                description=DEMO_TASKS[i % len(DEMO_TASKS)],
                due_date=datetime.utcnow() + timedelta(days=2),
                status="pending",
                task_type="follow_up",
                is_demo=True,
            )
            db.add(task)
            await db.flush()

            # For the first company (Kumba), create a demo outreach draft that was sent 3 days ago
            # This triggers AL03 (follow-up overdue) on the demo scoreboard
            if i == 0:
                draft = OutreachDraft(
                    contact_id=contact.id,
                    company_id=company.id,
                    brief_id=brief.id,
                    linkedin_message=f"Hi {contact.name} — noticed {company.name} is navigating expansion while sector payment cycles lengthen. Worth a quick chat on receivables timing?",
                    email_subject=f"Working capital timing during {company.name}'s expansion phase",
                    email_body=f"Hi {contact.name},\n\nI've been following {company.name}'s growth and noticed the expansion activity coinciding with broader sector pressure on receivables cycles.\n\nWould you be open to a 10-minute call?\n\nBest,\n[Your Name]",
                    followup_message=f"Hi {contact.name} — following up on my note from last week. Let me know if useful.",
                    gatekeeper_version=f"Hi — I'm hoping to connect with {contact.name} regarding a working capital insight for {company.name}.",
                    technical_validator_version=f"Hi {contact.name} — reaching out about receivables cycle data.",
                    status="sent",
                    marked_sent_at=datetime.utcnow() - timedelta(days=3),
                    followup_due_at=datetime.utcnow() - timedelta(days=1),
                    contact_status_after="Not contacted",
                    is_demo=True,
                )
                db.add(draft)

        # ── Demo Web Intelligence + Contact Discovery ──────────────────────
        await db.flush()
        await _seed_web_intelligence(db)

        # Seed current WeeklySnapshot with amber-state values (below threshold but > 0)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        snapshot = WeeklySnapshot(
            week_start_date=week_start,
            messages_sent=4,        # amber: threshold is 5
            followups_sent=2,       # amber: threshold is 3
            briefs_sent=1,          # green: threshold is 1
            calls_requested=0,      # red: threshold is 1
            replies_received=1,
            companies_researched=3,
        )
        db.add(snapshot)

        await db.commit()


# ── Demo Web Intelligence ─────────────────────────────────────────────────────

_DEMO_INTEL = {
    "Kumba Iron Ore": {
        "is_jse_listed": True, "jse_ticker": "KIO",
        "latest_stock_data": {"price": 412.50, "change_pct": -0.8, "market_cap": "R132bn", "currency": "ZAR", "week_52_high": 520.00, "week_52_low": 380.00, "last_updated": "2026-05-02T09:00:00"},
        "intelligence_summary": "Kumba Iron Ore is navigating a challenging iron ore price environment while managing significant capital commitments at Sishen and Kolomela mines. Operating costs rose 11% in the latest annual results, driven by labour and energy, while iron ore export volumes declined 4% due to Transnet rail constraints. The Finance Director position changed hands in late 2024 — a new incumbent is likely still mapping current tools and relationships.",
        "key_signals": [
            {"signal": "New Finance Director appointed Q4 2024 — early tenure receptivity window", "relevance": "high", "signal_type": "leadership_change", "source_url": None},
            {"signal": "Operating costs up 11% — margin compression driving cost review", "relevance": "high", "signal_type": "financial_pressure", "source_url": None},
            {"signal": "Transnet rail constraints delaying export receipts by 15-30 days", "relevance": "high", "signal_type": "financial_pressure", "source_url": None},
            {"signal": "Sishen mine expansion capex commitments increasing working capital draw", "relevance": "medium", "signal_type": "expansion", "source_url": None},
        ],
        "timing_assessment": "Strong timing. New Finance Director is 5 months in — early enough to be evaluating existing tools, late enough to understand the specific pain points. The rail constraint issue directly creates receivables timing gaps.",
        "recommended_approach": "Lead with the Transnet delay angle — every missed export shipment is a receivables gap. Frame as a timing bridge, not a financing product. Reference the Finance Director's likely focus on cash flow predictability given the cost environment.",
    },
    "Exxaro Resources": {
        "is_jse_listed": True, "jse_ticker": "EXX",
        "latest_stock_data": {"price": 148.20, "change_pct": 1.2, "market_cap": "R48bn", "currency": "ZAR", "week_52_high": 185.00, "week_52_low": 130.00, "last_updated": "2026-05-02T09:00:00"},
        "intelligence_summary": "Exxaro is in a strategic pivot — diversifying beyond coal into renewables while managing declining thermal coal demand from traditional customers. This dual-track strategy creates unusual working capital dynamics: coal revenues are lumpy and customer base is contracting, while renewable project receivables have different timing profiles. The CFO noted 'cash flow optimisation' as a key 2025 priority in the latest results presentation.",
        "key_signals": [
            {"signal": "CFO named 'cash flow optimisation' as 2025 priority in results presentation", "relevance": "high", "signal_type": "financial_pressure", "source_url": None},
            {"signal": "Renewable energy division scaling — new receivables profile", "relevance": "medium", "signal_type": "expansion", "source_url": None},
            {"signal": "Coal customer base contracting — concentration risk increasing", "relevance": "medium", "signal_type": "financial_pressure", "source_url": None},
        ],
        "timing_assessment": "Good timing. The CFO has publicly flagged cash flow as a priority — this is the rare case where you can reference the executive's own words back to them.",
        "recommended_approach": "Reference the CFO's public statement on cash flow optimisation. Position as a tool that gives the finance team better visibility on receivables timing across both legacy coal and new renewable contracts — two very different payment cycles.",
    },
    "Santam": {
        "is_jse_listed": True, "jse_ticker": "SNT",
        "latest_stock_data": {"price": 338.00, "change_pct": 0.3, "market_cap": "R41bn", "currency": "ZAR", "week_52_high": 365.00, "week_52_low": 295.00, "last_updated": "2026-05-02T09:00:00"},
        "intelligence_summary": "Santam is South Africa's largest short-term insurer with significant premium receivables across commercial and personal lines. The business has been managing elevated claims from climate-related events while maintaining underwriting discipline. Premium collections from commercial clients — particularly SME brokers — have a complex receivables profile with timing mismatches between premium income and claims payout.",
        "key_signals": [
            {"signal": "Climate claims elevated — cash outflow timing creating balance sheet pressure", "relevance": "high", "signal_type": "financial_pressure", "source_url": None},
            {"signal": "Commercial lines growth outpacing collections infrastructure", "relevance": "medium", "signal_type": "expansion", "source_url": None},
        ],
        "timing_assessment": "Moderate timing. No recent leadership changes. The climate claims angle is real but may already be well-managed internally. Best entry point is via treasury or group finance rather than the CFO directly.",
        "recommended_approach": "Focus on the commercial lines receivables complexity — broker-intermediated premium collection creates multi-party timing risk. Offer a conversation framed around receivables transparency rather than acceleration.",
    },
    "Grindrod": {
        "is_jse_listed": True, "jse_ticker": "GND",
        "latest_stock_data": {"price": 8.42, "change_pct": 1.2, "market_cap": "R4.2bn", "currency": "ZAR", "week_52_high": 9.80, "week_52_low": 6.10, "last_updated": "2026-05-02T09:00:00"},
        "intelligence_summary": "Grindrod's freight division is navigating east African corridor expansion while absorbing port congestion costs. Operating cash flow declined 12% in the most recent period despite 8% revenue growth, indicating working capital pressure. A new CFO was appointed in Q3 2024 — early tenure is historically the highest receptivity window for finance solutions. The east African corridor growth creates multi-currency receivables complexity.",
        "key_signals": [
            {"signal": "New CFO appointed Q3 2024 — 8 months into tenure", "relevance": "high", "signal_type": "leadership_change", "source_url": None},
            {"signal": "Operating cash flow down 12% despite 8% revenue growth", "relevance": "high", "signal_type": "financial_pressure", "source_url": None},
            {"signal": "East African corridor expansion — multi-currency receivables risk", "relevance": "medium", "signal_type": "expansion", "source_url": None},
        ],
        "timing_assessment": "Strong timing. New CFO is 8 months in — optimal window. The cash flow vs revenue growth divergence is a textbook receivables timing problem and is visible in public filings.",
        "recommended_approach": "Lead with the cash flow vs revenue growth gap visible in public filings — this is their own data, not your claim. Frame as: 'Your numbers show the business is growing but cash isn't keeping pace — that gap is almost always receivables.' The east African expansion adds urgency.",
    },
    "Harmony Gold": {
        "is_jse_listed": True, "jse_ticker": "HAR",
        "latest_stock_data": {"price": 98.70, "change_pct": 2.1, "market_cap": "R56bn", "currency": "ZAR", "week_52_high": 115.00, "week_52_low": 65.00, "last_updated": "2026-05-02T09:00:00"},
        "intelligence_summary": "Harmony Gold is benefiting from elevated gold prices but faces significant capital allocation pressure as it advances the Mponeng deep-level extension and Papua New Guinea operations. Gold sales receivables settle quickly (T+2), but contractor and supplier payables extend much further — creating an inverse working capital pressure. The Papua New Guinea operations introduce currency and sovereign receivables risk.",
        "key_signals": [
            {"signal": "PNG operations creating sovereign and FX receivables exposure", "relevance": "high", "signal_type": "financial_pressure", "source_url": None},
            {"signal": "Mponeng extension capex — significant capital commitment", "relevance": "medium", "signal_type": "expansion", "source_url": None},
            {"signal": "Gold price at multi-year high — margins strong but capex absorbing cash", "relevance": "medium", "signal_type": "financial_pressure", "source_url": None},
        ],
        "timing_assessment": "Moderate-good timing. The PNG angle is the strongest entry — international operations create receivables complexity that domestic-only solutions don't address well. This differentiates the conversation.",
        "recommended_approach": "Lead with the PNG complexity — most finance solutions in this space are designed for domestic SA operations. Position as having specific experience with multi-jurisdiction receivables timing and FX exposure management.",
    },
}

_DEMO_ROLES = [
    {"title": "Chief Financial Officer", "seniority": "C-suite", "department": "Finance", "why": "Ultimate owner of receivables risk and working capital strategy. Approves off-balance-sheet financing solutions.", "priority": 1},
    {"title": "Group Financial Manager", "seniority": "Senior Management", "department": "Finance", "why": "Day-to-day owner of cash-flow reporting and receivables tracking.", "priority": 2},
    {"title": "Head of Treasury", "seniority": "Senior Management", "department": "Finance", "why": "Directly responsible for working capital optimisation and liquidity management.", "priority": 3},
]
_DEMO_DEPTS = [
    {"department": "Group Finance", "reason": "Primary buyer and user of receivables management solutions"},
    {"department": "Treasury", "reason": "Manages working capital and liquidity directly"},
]


async def _seed_web_intelligence(db: AsyncSession) -> None:
    from sqlalchemy import select as sa_select
    from urllib.parse import quote_plus

    companies_result = await db.execute(sa_select(Company))
    companies = companies_result.scalars().all()

    for company in companies:
        intel_data = _DEMO_INTEL.get(company.name)
        if not intel_data:
            continue

        ec = quote_plus(company.name)
        linkedin_urls = [
            {"label": f"CFO at {company.name}", "url": f"https://www.linkedin.com/search/results/people/?company={ec}&title=CFO", "description": "Direct search for the Chief Financial Officer"},
            {"label": f"Finance Director at {company.name}", "url": f"https://www.linkedin.com/search/results/people/?company={ec}&title=Finance+Director", "description": "Finance directors and senior finance managers"},
            {"label": f"Treasury & working capital at {company.name}", "url": f"https://www.linkedin.com/search/results/people/?company={ec}&keywords=treasury+working+capital", "description": "Treasury, working capital, and cash management roles"},
            {"label": f"All finance roles at {company.name}", "url": f"https://www.linkedin.com/search/results/people/?company={ec}&keywords=finance+CFO+treasury", "description": "Broad finance department search"},
        ]

        report = WebIntelligenceReport(
            company_id=company.id,
            scan_status="complete",
            scan_triggered_by="auto",
            scan_started_at=datetime.utcnow(),
            scan_completed_at=datetime.utcnow(),
            news_articles=json.dumps([]),
            press_releases=json.dumps([]),
            sens_announcements=json.dumps([]),
            is_jse_listed=intel_data["is_jse_listed"],
            jse_ticker=intel_data["jse_ticker"],
            latest_stock_data=json.dumps(intel_data["latest_stock_data"]),
            public_financial_signals=json.dumps([]),
            company_website_url=company.website,
            linkedin_company_url=None,
            leadership_page_url=None,
            leadership_mentions=json.dumps([]),
            intelligence_summary=intel_data["intelligence_summary"],
            key_signals=json.dumps(intel_data["key_signals"]),
            timing_assessment=intel_data["timing_assessment"],
            recommended_approach=intel_data["recommended_approach"],
            is_demo=True,
        )
        db.add(report)
        await db.flush()

        discovery = ContactDiscovery(
            company_id=company.id,
            web_intelligence_id=report.id,
            recommended_roles=json.dumps(_DEMO_ROLES),
            recommended_departments=json.dumps(_DEMO_DEPTS),
            linkedin_search_urls=json.dumps(linkedin_urls),
            linkedin_company_page=None,
            contact_sources=json.dumps([
                {"source_type": "company_website", "url": company.website, "description": f"{company.name} official website — check About/Leadership/Team sections", "expected_contacts": "C-suite, divisional heads, board"},
                {"source_type": "annual_report", "url": company.website + "/investors" if company.website else None, "description": "Annual report — board and executive committee listed by name", "expected_contacts": "Board members, CFO, group executives"},
            ]),
            publicly_listed_contacts=json.dumps([]),
            is_demo=True,
        )
        db.add(discovery)

    await db.flush()
