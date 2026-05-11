from typing import Final

from src.gamification.domain.value_objects import LevelInfo


def _generate_xp_thresholds() -> list[int]:
    thresholds = [0, 0]
    for lvl in range(2, 101):
        xp_required = int(150 * (lvl**2.1))
        thresholds.append(xp_required)
    return thresholds


_XP_THRESHOLDS: Final[list[int]] = _generate_xp_thresholds()
_MAX_LEVEL: Final[int] = len(_XP_THRESHOLDS) - 1


def _rank_for_level(level: int) -> tuple[str, str]:
    match level:
        case lvl if 1 <= lvl <= 5:
            return "Novice", "Piglet"
        case lvl if 6 <= lvl <= 15:
            return "Apprentice", "Boar"
        case lvl if 16 <= lvl <= 30:
            return "Wild", "Boar"
        case lvl if 31 <= lvl <= 50:
            return "Fierce", "Tusker"
        case lvl if 51 <= lvl <= 80:
            return "Berserker", "Boar"
        case lvl if 81 <= lvl <= 99:
            return "Crimson", "Boar"
        case _:
            return "Elder", "Boar"


def calculate_level(total_xp: int) -> LevelInfo:
    if total_xp < 0:
        raise ValueError(f"total_xp cannot be negative, got {total_xp}")

    current_level = 1
    for lvl, threshold in enumerate(_XP_THRESHOLDS):
        if total_xp >= threshold:
            current_level = lvl
        else:
            break

    current_level = min(current_level, _MAX_LEVEL)

    xp_this_level_starts = _XP_THRESHOLDS[current_level]

    if current_level < _MAX_LEVEL:
        xp_next_level = _XP_THRESHOLDS[current_level + 1]
        xp_progress = total_xp - xp_this_level_starts
        xp_needed = xp_next_level - total_xp
    else:
        xp_next_level = None
        xp_progress = total_xp - xp_this_level_starts
        xp_needed = None

    tier, name = _rank_for_level(current_level)

    return LevelInfo(
        level=current_level,
        rank_tier=tier,
        rank_name=name,
        current_xp=total_xp,
        xp_for_next_level=xp_next_level,
        xp_progress=xp_progress,
        xp_needed=xp_needed,
    )
