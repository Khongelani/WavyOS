import json
from datetime import datetime, timedelta, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import PipelineStage, Company, Contact, ResearchReport, SignalBrief, Task, OutreachDraft, WeeklySnapshot

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
