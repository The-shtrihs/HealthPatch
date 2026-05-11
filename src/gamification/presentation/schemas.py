from pydantic import BaseModel, ConfigDict

from src.gamification.domain.leveling import LevelInfo


class LevelInfoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    level: int
    rank_tier: str
    rank_name: str
    current_xp: int
    xp_for_next_level: int | None
    xp_progress: int
    xp_needed: int | None

    @classmethod
    def from_domain(cls, level_info: LevelInfo) -> "LevelInfoSchema":
        return cls(
            level=level_info.level,
            rank_tier=level_info.rank_tier,
            rank_name=level_info.rank_name,
            current_xp=level_info.current_xp,
            xp_for_next_level=level_info.xp_for_next_level,
            xp_progress=level_info.xp_progress,
            xp_needed=level_info.xp_needed,
        )


class GamificationProfileResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 42,
                "total_xp": 1850,
                "level_info": {
                    "level": 3,
                    "rank_tier": "Novice",
                    "rank_name": "Piglet",
                    "current_xp": 1850,
                    "xp_for_next_level": 2500,
                    "xp_progress": 450,
                    "xp_needed": 650,
                },
            }
        },
    )

    user_id: int
    total_xp: int
    level_info: LevelInfoSchema
