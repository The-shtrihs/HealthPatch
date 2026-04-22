from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterCommand:
    name: str
    email: str
    password: str


@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str
    device_info: str | None = None


@dataclass(frozen=True)
class LogoutCommand:
    refresh_token: str


@dataclass(frozen=True)
class LogoutAllCommand:
    user_id: int


@dataclass(frozen=True)
class RefreshTokenCommand:
    refresh_token: str


@dataclass(frozen=True)
class ChangePasswordCommand:
    user_id: int
    current_password: str
    new_password: str


@dataclass(frozen=True)
class ForgotPasswordCommand:
    email: str


@dataclass(frozen=True)
class ResetPasswordCommand:
    token: str
    new_password: str


@dataclass(frozen=True)
class VerifyEmailCommand:
    token: str


@dataclass(frozen=True)
class ResendVerificationCommand:
    email: str


@dataclass(frozen=True)
class Enable2FACommand:
    user_id: int


@dataclass(frozen=True)
class Confirm2FACommand:
    user_id: int
    code: str


@dataclass(frozen=True)
class Disable2FACommand:
    user_id: int
    code: str


@dataclass(frozen=True)
class Verify2FAAndLoginCommand:
    temp_token: str
    code: str
    device_info: str | None = None


@dataclass(frozen=True)
class HandleOAuthUserCommand:
    provider: str
    provider_id: str
    email: str
    name: str
    avatar_url: str | None
