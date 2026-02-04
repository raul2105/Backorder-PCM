"""add must_change_password to users

Revision ID: 7f3b6c7e0a11
Revises: bbf45e6fa095
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f3b6c7e0a11'
down_revision = 'bbf45e6fa095'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column('users', 'must_change_password', server_default=None)


def downgrade():
    op.drop_column('users', 'must_change_password')
