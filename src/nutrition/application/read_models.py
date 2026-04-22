from dataclasses import dataclass
from datetime import date


@dataclass
class MacroTotalsReadModel:
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float


@dataclass
class DayOverviewReadModel:
    target_date: date
    norm: MacroTotalsReadModel
    consumed: MacroTotalsReadModel
    remaining: MacroTotalsReadModel
