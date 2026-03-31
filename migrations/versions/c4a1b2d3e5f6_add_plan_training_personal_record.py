"""add_plan_training_personal_record

Revision ID: c4a1b2d3e5f6
Revises: 1fa4ca704d4f
Create Date: 2026-03-27 00:00:00.000000

Schema changes:
- NEW TABLE plan_training: training day within a workout plan
- NEW TABLE plan_training_exercise: exercise prescription inside a training template
- NEW TABLE personal_record: user's best weight per exercise (unique per user+exercise)
- NEW TABLE muscle_group: controlled vocabulary of muscle groups (admin-managed)
- NEW TABLE exercise_muscle_group: many-to-many association for secondary muscle groups on an exercise
- MODIFIED exercise: drop muscle_group VARCHAR, add primary_muscle_group_id FK -> muscle_group (RESTRICT, nullable)
- MODIFIED workout_session: drop plan_id FK (workout_plan), add plan_training_id FK (plan_training, SET NULL)
- MODIFIED exercise_session: add is_from_template BOOLEAN NOT NULL DEFAULT false

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4a1b2d3e5f6"
down_revision: str | None = "1fa4ca704d4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### new tables ###
    op.create_table(
        "muscle_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "plan_training",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("weekday", sa.Enum("mon", "tue", "wed", "thu", "fri", "sat", "sun", name="weekday"), nullable=True),
        sa.Column("order_num", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["plan_id"], ["workout_plan.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "plan_training_exercise",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_training_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("order_num", sa.Integer(), nullable=False),
        sa.Column("target_sets", sa.Integer(), nullable=False),
        sa.Column("target_reps", sa.Integer(), nullable=False),
        sa.Column("target_weight_pct", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["plan_training_id"], ["plan_training.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "personal_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "exercise_id"),
    )

    # ### modify workout_session: replace plan_id with plan_training_id ###
    op.drop_constraint("workout_session_plan_id_fkey", "workout_session", type_="foreignkey")
    op.drop_column("workout_session", "plan_id")
    op.add_column("workout_session", sa.Column("plan_training_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "workout_session_plan_training_id_fkey",
        "workout_session",
        "plan_training",
        ["plan_training_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ### modify exercise: drop muscle_group string, add FK-based primary + secondary ###
    op.drop_column("exercise", "muscle_group")
    op.add_column("exercise", sa.Column("primary_muscle_group_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "exercise_primary_muscle_group_id_fkey",
        "exercise",
        "muscle_group",
        ["primary_muscle_group_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_table(
        "exercise_muscle_group",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("muscle_group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["muscle_group_id"], ["muscle_group.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("exercise_id", "muscle_group_id"),
        sa.UniqueConstraint("exercise_id", "muscle_group_id"),
    )

    # ### modify exercise_session: add is_from_template ###
    op.add_column("exercise_session", sa.Column("is_from_template", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    # ### revert exercise_session ###
    op.drop_column("exercise_session", "is_from_template")

    # ### revert exercise muscle group ###
    op.drop_table("exercise_muscle_group")
    op.drop_constraint("exercise_primary_muscle_group_id_fkey", "exercise", type_="foreignkey")
    op.drop_column("exercise", "primary_muscle_group_id")
    op.add_column("exercise", sa.Column("muscle_group", sa.String(length=100), nullable=True))

    # ### revert workout_session: restore plan_id ###
    op.drop_constraint("workout_session_plan_training_id_fkey", "workout_session", type_="foreignkey")
    op.drop_column("workout_session", "plan_training_id")
    op.add_column("workout_session", sa.Column("plan_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "workout_session_plan_id_fkey",
        "workout_session",
        "workout_plan",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ### drop new tables (reverse dependency order) ###
    op.drop_table("personal_record")
    op.drop_table("plan_training_exercise")
    op.drop_table("plan_training")
    sa.Enum(name="weekday").drop(op.get_bind(), checkfirst=True)
    op.drop_table("muscle_group")
