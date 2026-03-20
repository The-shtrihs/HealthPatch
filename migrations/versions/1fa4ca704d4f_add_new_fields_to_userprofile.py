"""add new fields to userProfile

Revision ID: 1fa4ca704d4f
Revises: 0bfc85f1c349
Create Date: 2026-03-20 19:26:52.813909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1fa4ca704d4f'
down_revision: Union[str, None] = '0bfc85f1c349'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    gender_enum = postgresql.ENUM("MALE", "FEMALE", name="gender")
    fitness_enum = postgresql.ENUM(
        "WEIGHT_LOSS", "MUSCLE_GAIN", "STRENGTH_BUILDING", "ENDURANCE",
        name="fitnessgoal"
    )

    gender_enum.create(bind, checkfirst=True)
    fitness_enum.create(bind, checkfirst=True)

    op.add_column("user_profile", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("user_profile", sa.Column("gender", gender_enum, nullable=True))

    op.alter_column(
        "user_profile",
        "fitness_goal",
        existing_type=sa.VARCHAR(length=255),
        type_=fitness_enum,
        existing_nullable=True,
        postgresql_using="""
            CASE
                WHEN fitness_goal IS NULL THEN NULL
                WHEN lower(fitness_goal) = 'weight loss' THEN 'WEIGHT_LOSS'
                WHEN lower(fitness_goal) = 'muscle gain' THEN 'MUSCLE_GAIN'
                WHEN lower(fitness_goal) = 'strength building' THEN 'STRENGTH_BUILDING'
                WHEN lower(fitness_goal) = 'endurance' THEN 'ENDURANCE'
                ELSE NULL
            END::fitnessgoal
        """,
    )

def downgrade() -> None:
    bind = op.get_bind()

    fitness_enum = postgresql.ENUM(
        "WEIGHT_LOSS", "MUSCLE_GAIN", "STRENGTH_BUILDING", "ENDURANCE",
        name="fitnessgoal"
    )
    gender_enum = postgresql.ENUM("MALE", "FEMALE", name="gender")

    op.alter_column(
        "user_profile",
        "fitness_goal",
        existing_type=fitness_enum,
        type_=sa.VARCHAR(length=255),
        existing_nullable=True,
        postgresql_using="""
            CASE
                WHEN fitness_goal = 'WEIGHT_LOSS' THEN 'weight loss'
                WHEN fitness_goal = 'MUSCLE_GAIN' THEN 'muscle gain'
                WHEN fitness_goal = 'STRENGTH_BUILDING' THEN 'strength building'
                WHEN fitness_goal = 'ENDURANCE' THEN 'endurance'
                ELSE NULL
            END
        """,
    )
    op.drop_column("user_profile", "gender")
    op.drop_column("user_profile", "age")

    gender_enum.drop(bind, checkfirst=True)
    fitness_enum.drop(bind, checkfirst=True)