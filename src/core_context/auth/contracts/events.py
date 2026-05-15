from pydantic import EmailStr

from src.shared.contracts.integration_event import IntegrationEvent


class UserRegistered(IntegrationEvent):
    user_id: int
    email: EmailStr
    display_name: str | None = None


class UserLoggedIn(IntegrationEvent):
    user_id: int
    via: str = "password"


class PasswordResetRequested(IntegrationEvent):
    user_id: int
    email: EmailStr
