"""tasks callback_execution_id

Revision ID: 7c1e4b9d2f30
Revises: 2a65b5eeba68
Create Date: 2026-10-22 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1e4b9d2f30'
down_revision: Union[str, Sequence[str], None] = '2a65b5eeba68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tasks', sa.Column('callback_execution_id', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_tasks_callback_execution_id'), 'tasks', ['callback_execution_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tasks_callback_execution_id'), table_name='tasks')
    op.drop_column('tasks', 'callback_execution_id')
