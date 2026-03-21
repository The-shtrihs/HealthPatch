import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters.")
    password_confirm: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str):
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[@$!%*?&_]", value):
            raise ValueError("Password must contain at least one special character (@$!%*?&_)")
        return value

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters")
    new_password: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters")
    new_password_confirm: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters")

    @model_validator(mode="after")
    def validate_new_passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("New passwords do not match")
        return self


class RegisterResponse(BaseModel):
    message: str


class MessageResponse(BaseModel):
    message: str


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_base64: str
    message: str = "Scan the QR code with your authenticator app and enter the generated code to enable 2FA"


class Verify2FARequest(BaseModel):
    temp_token: str
    code: str


class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    avatar_url: str | None = None
    is_verified: bool
    is_2fa_enabled: bool
    oauth_provider: str | None = None

    class Config:
        from_attributes = True
