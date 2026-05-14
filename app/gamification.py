"""XP, levels, ranks, and local leaderboard logic."""

import json
from pathlib import Path
from typing import Any

from app.auth import save_profile
from app.profile import User

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEADERBOARD_PATH = PROJECT_ROOT / "data" / "leaderboard.json"

XP_PER_SET = 10
LEVEL_THRESHOLDS = [0, 500, 1250, 2500, 4500, 7000, 10000, 14000]
RANK_NAMES = ["Beginner", "Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Elite"]


def calculate_xp(sets: int) -> int:
    """Return XP awarded for completed sets."""
    return max(0, sets) * XP_PER_SET


def get_level(xp: int) -> int:
    """Return level based on XP thresholds."""
    level = 1
    for idx, threshold in enumerate(LEVEL_THRESHOLDS, start=1):
        if xp >= threshold:
            level = idx
    return level


def get_rank(level: int) -> str:
    """Return rank title associated with a level."""
    index = min(max(level - 1, 0), len(RANK_NAMES) - 1)
    return RANK_NAMES[index]


def add_xp(user: User, xp: int) -> None:
    """Add XP to the user, recalculate level/rank, and persist profile."""
    user.xp += max(0, xp)
    user.level = get_level(user.xp)
    user.rank = get_rank(user.level)
    save_profile(user)


def load_leaderboard() -> list[dict[str, Any]]:
    """Load leaderboard entries from local JSON storage."""
    if not LEADERBOARD_PATH.exists():
        return []
    try:
        with LEADERBOARD_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        # Corrupt or unreadable file — reset it and start fresh
        LEADERBOARD_PATH.write_text("[]", encoding="utf-8")
        return []


def update_leaderboard(user: User) -> None:
    """Insert or update the user's leaderboard record."""
    entries = load_leaderboard()
    updated = False
    for record in entries:
        if record["username"] == user.username:
            record.update({"xp": user.xp, "level": user.level, "rank": user.rank})
            updated = True
            break

    if not updated:
        entries.append({"username": user.username, "xp": user.xp, "level": user.level, "rank": user.rank})

    entries.sort(key=lambda row: row["xp"], reverse=True)
    LEADERBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEADERBOARD_PATH.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def get_top_n(n: int = 10) -> list[dict[str, Any]]:
    """Return top N leaderboard records ordered by XP descending."""
    return load_leaderboard()[:n]
