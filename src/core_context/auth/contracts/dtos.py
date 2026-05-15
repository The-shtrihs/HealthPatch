from pydantic import BaseModel, ConfigDict, EmailStr


class UserSummaryDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    email: EmailStr
    display_name: str | None = None
    is_active: bool = True
