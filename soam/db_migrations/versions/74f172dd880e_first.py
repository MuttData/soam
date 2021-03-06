"""first

Revision ID: 74f172dd880e
Revises: Fabian
Create Date: 2020-09-01 15:23:00.216000

"""
# pylint: skip-file

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils.types.uuid import UUIDType

from soam.data_models import Identity

# revision identifiers, used by Alembic.
revision = "74f172dd880e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Creates tables and sets keys and constraints."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "soam_flow_runs",
        sa.Column("flow_run_id", UUIDType(binary=False), nullable=False,),
        sa.Column("run_date", sa.DateTime(), nullable=True),
        sa.Column("start_datetime", sa.DateTime(), nullable=True),
        sa.Column("end_datetime", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("flow_run_id"),
        sa.UniqueConstraint("flow_run_id"),
    )
    op.create_table(
        "tasks_runs",
        sa.Column("params", sa.Text(), nullable=False),
        sa.Column("params_hash", sa.Text(), nullable=False),
        sa.Column("task_run_id", UUIDType(binary=False), nullable=False,),
        sa.Column("flow_run_id", UUIDType(binary=False), nullable=True,),
        sa.Column(
            "step_type",
            sa.Enum(
                "extract",
                "preprocess",
                "forecast",
                "postprocess",
                "custom",
                name="steptypeenum",
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["flow_run_id"], ["soam_flow_runs.flow_run_id"],),
        sa.PrimaryKeyConstraint("task_run_id"),
        sa.UniqueConstraint("task_run_id"),
    )
    op.create_table(
        "forecaster_values",
        sa.Column("id", Identity(), nullable=False),
        sa.Column("task_run_id", UUIDType(binary=False), nullable=False,),
        sa.Column("forecast_date", sa.DateTime(), nullable=False),
        sa.Column("yhat", sa.Float(), nullable=False),
        sa.Column("yhat_lower", sa.Float(), nullable=True),
        sa.Column("yhat_upper", sa.Float(), nullable=True),
        sa.Column("y", sa.Float(), nullable=True),
        sa.Column("trend", sa.Float(), nullable=True),
        sa.Column("outlier_value", sa.Float(), nullable=True),
        sa.Column("outlier_sign", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["task_run_id"], ["tasks_runs.task_run_id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_run_id", "forecast_date"),
    )
    # ### end Alembic commands ###


def downgrade():
    """Drop tables"""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("forecaster_values")
    op.drop_table("tasks_runs")
    op.drop_table("soam_flow_runs")
    # ### end Alembic commands ###
