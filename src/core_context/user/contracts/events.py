from src.core_context.user.contracts.dtos import FitnessGoal
from src.shared.contracts.integration_event import IntegrationEvent


class ProfileUpdated(IntegrationEvent):
    user_id: int
    changed_fields: tuple[str, ...] = ()


class FitnessGoalChanged(IntegrationEvent):
    user_id: int
    new_goal: FitnessGoal
