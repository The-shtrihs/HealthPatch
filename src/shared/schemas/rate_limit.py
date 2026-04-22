from pydantic import BaseModel

class RateLimitResponse(BaseModel):
    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: int