from pydantic import BaseModel, ConfigDict


class GamificationProfileDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    level: int
    total_xp: int
