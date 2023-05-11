"""Add name and organization fields to download_link

Revision ID: 18bcc4e0f257
Revises: 12f6978c9c59
Create Date: 2023-05-11 14:34:02.265007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '18bcc4e0f257'
down_revision = '12f6978c9c59'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('download_link', sa.Column('organization', sa.String()))
    op.add_column('download_link', sa.Column('name', sa.String()))


def downgrade() -> None:
    op.drop_column('download_link', 'organization')
    op.drop_column('download_link', 'name')
