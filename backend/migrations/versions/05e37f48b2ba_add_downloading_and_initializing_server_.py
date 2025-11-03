"""add downloading and initializing server status

Revision ID: 05e37f48b2ba
Revises: a71a4d567fd8
Create Date: 2025-11-03 20:11:21.538017

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = "05e37f48b2ba"
down_revision: Union[str, Sequence[str], None] = "a71a4d567fd8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add DOWNLOADING and INITIALIZING to ServerStatus enum
    op.alter_column(
        "servers",
        "status",
        existing_type=sa.Enum(
            "STOPPED",
            "STARTING",
            "RUNNING",
            "STOPPING",
            "ERROR",
            name="serverstatus",
        ),
        type_=sa.Enum(
            "STOPPED",
            "DOWNLOADING",
            "INITIALIZING",
            "STARTING",
            "RUNNING",
            "STOPPING",
            "ERROR",
            name="serverstatus",
        ),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove DOWNLOADING and INITIALIZING from ServerStatus enum
    op.alter_column(
        "servers",
        "status",
        existing_type=sa.Enum(
            "STOPPED",
            "DOWNLOADING",
            "INITIALIZING",
            "STARTING",
            "RUNNING",
            "STOPPING",
            "ERROR",
            name="serverstatus",
        ),
        type_=sa.Enum(
            "STOPPED",
            "STARTING",
            "RUNNING",
            "STOPPING",
            "ERROR",
            name="serverstatus",
        ),
        existing_nullable=False,
    )
