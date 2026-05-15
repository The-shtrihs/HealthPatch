from datetime import date

from src.shared.contracts.integration_event import IntegrationEvent


class MealEntryAdded(IntegrationEvent):
    entry_id: int
    user_id: int
    consumed_on: date
    meal_type: str
    weight_grams: float


class MealEntryUpdated(IntegrationEvent):
    entry_id: int
    user_id: int
    consumed_on: date


class MealEntryDeleted(IntegrationEvent):
    entry_id: int
    user_id: int
    consumed_on: date


class DailyNormAchieved(IntegrationEvent):
    user_id: int
    day: date
