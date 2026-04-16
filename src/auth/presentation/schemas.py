import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str):
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[@$!%*?&_]", v):
            raise ValueError("Password must contain at least one special character (@$!%*?&_)")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str  


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    new_password_confirm: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("New passwords do not match")
        return self


class Verify2FARequest(BaseModel):
    temp_token: str
    code: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class MessageResponse(BaseModel):
    message: str


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_base64: str
    message: str = "Scan the QR code with your authenticator app and enter the generated code to enable 2FA"


class UserMeResponse(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: str | None = None
    is_verified: bool
    is_2fa_enabled: bool
    oauth_provider: str | None = None

    model_config = ConfigDict(from_attributes=True)