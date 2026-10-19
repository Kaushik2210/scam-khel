"""incident feedback

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('feedback_verdict', sa.String(length=16), nullable=True))

    op.create_table(
        'incident_feedback',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False),
        sa.Column('verdict', sa.String(length=16), nullable=False),
        sa.Column('notes', sa.Text(), server_default='', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    with op.batch_alter_table('incident_feedback', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_incident_feedback_incident_id'), ['incident_id'], unique=False)


def downgrade() -> None:
    op.drop_table('incident_feedback')
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.drop_column('feedback_verdict')
