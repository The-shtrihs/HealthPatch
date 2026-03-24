from pydantic import BaseModel, EmailStr


class UserInfo(BaseModel):
    provider: str
    provider_id: str
    email: EmailStr
    name: str
    avatar_url: str | None = None
    is_verified: bool = False

class OAuthStateData(BaseModel):
    provider: str         
    redirect_after: str   
    created_at: str        
    ip_address: str | None = None   
