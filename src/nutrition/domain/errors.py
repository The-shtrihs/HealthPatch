class NutritionDomainError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NutritionProfileNotFoundError(NutritionDomainError):
    def __init__(self, user_id: int | None = None):
        msg = f"Nutrition profile for user {user_id} was not found" if user_id is not None else "Nutrition profile was not found"
        super().__init__(msg)


class IncompleteNutritionProfileError(NutritionDomainError):
    def __init__(self, missing_fields: list[str]):
        fields = ", ".join(missing_fields)
        super().__init__(f"Complete profile is required for nutrition calculations. Missing: {fields}")


class UnsupportedGenderError(NutritionDomainError):
    def __init__(self):
        super().__init__("Unsupported gender for BMR calculation")


class UnsupportedFitnessGoalError(NutritionDomainError):
    def __init__(self, goal: str):
        super().__init__(f"Unsupported fitness goal: {goal}")


class UnsupportedActivityLevelError(NutritionDomainError):
    def __init__(self):
        super().__init__("Unsupported activity level. Use one of: sedentary, lightly_active, moderately_active, very_active")


class InvalidMealEntryError(NutritionDomainError):
    def __init__(self, message: str):
        super().__init__(message)


class MealEntryNotFoundError(NutritionDomainError):
    def __init__(self, meal_entry_id: int | None = None):
        msg = f"Meal entry with id {meal_entry_id} not found" if meal_entry_id is not None else "Meal entry not found"
        super().__init__(msg)
