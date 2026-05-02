"""Add web intelligence and contact discovery tables

Revision ID: 002_web_intelligence
Revises: 001_execution_enforcement
Create Date: 2026-05-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_web_intelligence"
down_revision: Union[str, None] = "001_execution_enforcement"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "web_intelligence_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scan_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("scan_triggered_by", sa.String(50), server_default="auto"),
        sa.Column("scan_started_at", sa.DateTime(), nullable=True),
        sa.Column("scan_completed_at", sa.DateTime(), nullable=True),
        sa.Column("scan_error", sa.Text(), nullable=True),
        # News & press
        sa.Column("news_articles", sa.Text(), nullable=True),
        sa.Column("press_releases", sa.Text(), nullable=True),
        sa.Column("sens_announcements", sa.Text(), nullable=True),
        # Financial
        sa.Column("is_jse_listed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("jse_ticker", sa.String(20), nullable=True),
        sa.Column("latest_stock_data", sa.Text(), nullable=True),
        sa.Column("public_financial_signals", sa.Text(), nullable=True),
        # Web presence
        sa.Column("company_website_url", sa.String(500), nullable=True),
        sa.Column("linkedin_company_url", sa.String(500), nullable=True),
        sa.Column("leadership_page_url", sa.String(500), nullable=True),
        sa.Column("leadership_mentions", sa.Text(), nullable=True),
        # Synthesised
        sa.Column("intelligence_summary", sa.Text(), nullable=True),
        sa.Column("key_signals", sa.Text(), nullable=True),
        sa.Column("timing_assessment", sa.Text(), nullable=True),
        sa.Column("recommended_approach", sa.Text(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "contact_discoveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("web_intelligence_id", sa.Integer(), sa.ForeignKey("web_intelligence_reports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recommended_roles", sa.Text(), nullable=True),
        sa.Column("recommended_departments", sa.Text(), nullable=True),
        sa.Column("linkedin_search_urls", sa.Text(), nullable=True),
        sa.Column("linkedin_company_page", sa.String(500), nullable=True),
        sa.Column("contact_sources", sa.Text(), nullable=True),
        sa.Column("publicly_listed_contacts", sa.Text(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("contact_discoveries")
    op.drop_table("web_intelligence_reports")
