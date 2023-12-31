"""Support ticket changes

Revision ID: e27df088124c
Revises: 77f8c4a5ec7b
Create Date: 2023-12-02 21:54:35.248379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e27df088124c'
down_revision: Union[str, None] = '77f8c4a5ec7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('support_tickets', 'close_requests_ids',
               existing_type=postgresql.ARRAY(sa.INTEGER()),
               type_=sa.ARRAY(sa.String()),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('support_tickets', 'close_requests_ids',
               existing_type=sa.ARRAY(sa.String()),
               type_=postgresql.ARRAY(sa.INTEGER()),
               existing_nullable=True)
    # ### end Alembic commands ###
