from dataclasses import dataclass

@dataclass
class RegisterCommand:
    name: str
    email: str
    password: str  


@dataclass
class LoginCommand:
    email: str
    password: str
    device_info: str | None = None  


@dataclass
class ChangePasswordCommand:
    current_password: str
    new_password: str


@dataclass
class TokenResult:
    access_token: str
    refresh_token: str | None   
    token_type: str         
    expires_in: int           


@dataclass
class TwoFactorSetupResult:
    secret: str
    qr_code_base64: str