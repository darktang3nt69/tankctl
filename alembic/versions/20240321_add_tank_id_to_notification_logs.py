"""add tank_id to notification_logs

Revision ID: 20240321_add_tank_id_to_notification_logs
Revises: ba24862272c3_add_tank_metrics
Create Date: 2024-03-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20240321_add_tank_id_to_notification_logs'
down_revision: Union[str, None] = 'ba24862272c3_add_tank_metrics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tank_id column
    op.add_column('notification_logs', sa.Column('tank_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_notification_logs_tank_id',
        'notification_logs', 'tanks',
        ['tank_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_notification_logs_tank_id', 'notification_logs', type_='foreignkey')
    
    # Drop tank_id column
    op.drop_column('notification_logs', 'tank_id') 