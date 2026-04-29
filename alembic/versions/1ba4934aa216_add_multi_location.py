"""add multi-location

Revision ID: 1ba4934aa216
Revises: 
Create Date: 2026-04-28 19:36:47.315331
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ba4934aa216'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('organizations') as batch_op:
        batch_op.add_column(
            sa.Column('parent_id', sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_organizations_parent_id',   # explicit name (important)
            'organizations',
            ['parent_id'],
            ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('organizations') as batch_op:
        batch_op.drop_constraint(
            'fk_organizations_parent_id',
            type_='foreignkey'
        )
        batch_op.drop_column('parent_id')