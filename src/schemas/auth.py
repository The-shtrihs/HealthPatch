from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50, description="Name must be between 2 and 50 characters")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Password must be between 8 and 128 characters")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
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


class RegisterResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    token_response: TokenResponse
    name: str
    email: EmailStr
