

from pydantic import BaseModel, EmailStr


class UserInfo(BaseModel):
   provider: str
   provider_id: str
   email: EmailStr
   name: str
   avatar_url: str | None = None
   is_verified: bool = False


   