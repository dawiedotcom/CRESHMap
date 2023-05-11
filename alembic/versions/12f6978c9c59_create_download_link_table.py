"""Create download_link table

Revision ID: 12f6978c9c59
Revises: 
Create Date: 2023-05-01 09:45:47.824396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12f6978c9c59'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'download_link',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String()),
        sa.Column('download_hash', sa.String()),
        sa.Column('salt', sa.String()),
        sa.Column('last_accessed', sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table('download_link')
