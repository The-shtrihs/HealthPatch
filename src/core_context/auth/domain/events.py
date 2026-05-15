from dataclasses import dataclass


@dataclass(frozen=True)
class UserRegisteredEvent:
    user_id: int
    email: str
    name: str


@dataclass(frozen=True)
class PasswordResetRequestedEvent:
    user_id: int
    email: str
    name: str


@dataclass(frozen=True)
class VerificationEmailRequestedEvent:
    user_id: int
    email: str
    name: str
