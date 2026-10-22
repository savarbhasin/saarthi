"""sandbox history: task call link, follow-ups, call sync

Revision ID: 9d4a2c6e8b11
Revises: 7c1e4b9d2f30
Create Date: 2026-10-22 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d4a2c6e8b11'
down_revision: Union[str, Sequence[str], None] = '7c1e4b9d2f30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tasks', sa.Column('call_execution_id', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_tasks_call_execution_id'), 'tasks', ['call_execution_id'], unique=False)
    op.add_column('tasks', sa.Column('follow_up_of', sa.Uuid(), nullable=True))
    op.create_foreign_key(op.f('fk_tasks_follow_up_of_tasks'), 'tasks', 'tasks', ['follow_up_of'], ['id'], ondelete='SET NULL')
    op.add_column('calls', sa.Column('sandbox_synced_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('calls', 'sandbox_synced_at')
    op.drop_constraint(op.f('fk_tasks_follow_up_of_tasks'), 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'follow_up_of')
    op.drop_index(op.f('ix_tasks_call_execution_id'), table_name='tasks')
    op.drop_column('tasks', 'call_execution_id')
