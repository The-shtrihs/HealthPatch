from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base import Base

if TYPE_CHECKING:
    from src.models.user import User


class Food(Base):
    __tablename__ = "food"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fdc_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brand_name: Mapped[str | None] = mapped_column(String(255), index=True)
    data_type: Mapped[str | None] = mapped_column(String(50))
    calories_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    protein_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    meal_entries: Mapped[list["MealEntry"]] = relationship(back_populates="food")
    portions: Mapped[list["FoodPortion"]] = relationship(back_populates="food", cascade="all, delete-orphan")


class FoodPortion(Base):
    __tablename__ = "food_portion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("food.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=1.0)
    measure_unit_name: Mapped[str] = mapped_column(String(100))
    gram_weight: Mapped[float] = mapped_column(Float, nullable=False)

    food: Mapped["Food"] = relationship(back_populates="portions")


class DailyDiary(Base):
    __tablename__ = "daily_diary"
    __table_args__ = (UniqueConstraint("user_id", "target_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    water_ml: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="daily_diaries")
    meal_entries: Mapped[list["MealEntry"]] = relationship(back_populates="daily_diary", cascade="all, delete-orphan")


class MealEntry(Base):
    __tablename__ = "meal_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    daily_diary_id: Mapped[int] = mapped_column(ForeignKey("daily_diary.id", ondelete="CASCADE"), nullable=False)
    food_id: Mapped[int] = mapped_column(ForeignKey("food.id", ondelete="RESTRICT"), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    weight_grams: Mapped[float] = mapped_column(Float, nullable=False)

    daily_diary: Mapped["DailyDiary"] = relationship(back_populates="meal_entries")
    food: Mapped["Food"] = relationship(back_populates="meal_entries")
