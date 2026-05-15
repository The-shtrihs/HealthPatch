from src.shared.contracts.integration_event import IntegrationEvent


class XPGained(IntegrationEvent):
    user_id: int
    amount: int
    reason: str


class LeveledUp(IntegrationEvent):
    user_id: int
    new_level: int
    previous_level: int
