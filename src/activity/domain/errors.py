class ActivityDomainError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class WorkoutPlanNotFoundError(ActivityDomainError):
    def __init__(self, plan_id: int | None = None):
        msg = f"Workout plan {plan_id} not found" if plan_id else "Workout plan not found"
        super().__init__(msg)


class PlanTrainingNotFoundError(ActivityDomainError):
    def __init__(self, training_id: int | None = None):
        msg = f"Plan training {training_id} not found" if training_id else "Plan training not found"
        super().__init__(msg)


class PlanTrainingExerciseNotFoundError(ActivityDomainError):
    def __init__(self, pte_id: int | None = None):
        msg = f"Plan training exercise {pte_id} not found" if pte_id else "Plan training exercise not found"
        super().__init__(msg)


class ExerciseNotFoundError(ActivityDomainError):
    def __init__(self, exercise_id: int | None = None):
        msg = f"Exercise {exercise_id} not found" if exercise_id else "Exercise not found"
        super().__init__(msg)


class MuscleGroupNotFoundError(ActivityDomainError):
    def __init__(self, muscle_group_id: int | None = None):
        msg = f"Muscle group {muscle_group_id} not found" if muscle_group_id else "Muscle group not found"
        super().__init__(msg)


class WorkoutSessionNotFoundError(ActivityDomainError):
    def __init__(self, session_id: int | None = None):
        msg = f"Workout session {session_id} not found" if session_id else "Workout session not found"
        super().__init__(msg)


class ExerciseSessionNotFoundError(ActivityDomainError):
    def __init__(self, exercise_session_id: int | None = None):
        msg = f"Exercise session {exercise_session_id} not found" if exercise_session_id else "Exercise session not found"
        super().__init__(msg)


class PersonalRecordNotFoundError(ActivityDomainError):
    def __init__(self, pr_id: int | None = None):
        msg = f"Personal record {pr_id} not found" if pr_id else "Personal record not found"
        super().__init__(msg)


class SessionAlreadyEndedError(ActivityDomainError):
    def __init__(self, message: str = "Workout session has already ended"):
        super().__init__(message)


class NotResourceOwnerError(ActivityDomainError):
    def __init__(self, message: str = "You do not own this resource"):
        super().__init__(message)


class PrivatePlanAccessError(ActivityDomainError):
    def __init__(self, message: str = "This workout plan is private"):
        super().__init__(message)


class InvalidWeightError(ActivityDomainError):
    def __init__(self, message: str = "Weight must be non-negative"):
        super().__init__(message)


class InvalidRepsError(ActivityDomainError):
    def __init__(self, message: str = "Reps must be positive"):
        super().__init__(message)


class InvalidSetNumberError(ActivityDomainError):
    def __init__(self, message: str = "Set number must be positive"):
        super().__init__(message)


class InvalidTimeRangeError(ActivityDomainError):
    def __init__(self, message: str = "End time must be greater than or equal to start time"):
        super().__init__(message)


class InvalidPlanTitleError(ActivityDomainError):
    def __init__(self, message: str = "Plan title must be non-empty"):
        super().__init__(message)


class PersonalRecordDowngradeError(ActivityDomainError):
    def __init__(self, new_weight: float, current_weight: float):
        super().__init__(f"New weight {new_weight} kg is less than current record {current_weight} kg")
