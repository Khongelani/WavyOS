"""Add execution enforcement tables and columns

Revision ID: 001_execution_enforcement
Revises:
Create Date: 2026-04-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_execution_enforcement"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # WeeklySnapshot
    op.create_table(
        "weekly_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("week_start_date", sa.Date(), nullable=False, unique=True),
        sa.Column("messages_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("followups_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("briefs_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("calls_requested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies_researched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("week_start_date", name="uq_weekly_snapshots_week_start"),
    )

    # WeeklyReview
    op.create_table(
        "weekly_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("what_was_sent", sa.Text()),
        sa.Column("who_replied", sa.Text()),
        sa.Column("what_worked", sa.Text()),
        sa.Column("industry_response", sa.Text()),
        sa.Column("change_next_week", sa.Text()),
        sa.Column("generated_targets", sa.Text()),
        sa.Column("generated_angle", sa.Text()),
        sa.Column("top_followups", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("week_start_date", name="uq_weekly_reviews_week_start"),
    )

    # OutreachDraft additions
    op.add_column("outreach_drafts", sa.Column("marked_sent_at", sa.DateTime(), nullable=True))
    op.add_column("outreach_drafts", sa.Column("followup_due_at", sa.DateTime(), nullable=True))
    op.add_column("outreach_drafts", sa.Column("contact_status_after", sa.String(100), nullable=True))

    # SignalBrief is_sent
    op.add_column("signal_briefs", sa.Column("is_sent", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("signal_briefs", "is_sent")
    op.drop_column("outreach_drafts", "contact_status_after")
    op.drop_column("outreach_drafts", "followup_due_at")
    op.drop_column("outreach_drafts", "marked_sent_at")
    op.drop_table("weekly_reviews")
    op.drop_table("weekly_snapshots")
