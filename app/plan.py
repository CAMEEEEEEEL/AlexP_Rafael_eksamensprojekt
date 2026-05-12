"""Workout plan and split management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
USERS_DIR = PROJECT_ROOT / "data" / "users"


def _get_plan_file(username: str) -> Path:
    """Return the file path used to store a user's workout plans."""
    return USERS_DIR / f"{username}_plans.json"


def _read_plan_store(username: str) -> dict[str, Any]:
    """Read the full plan storage payload from disk."""
    plan_file = _get_plan_file(username)
    if not plan_file.exists():
        return {"plans": {}}

    with plan_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "plans" not in data:
        migrated: dict[str, Any] = {"plans": {}}
        for name, exercises in data.items():
            migrated["plans"][name] = {"days": {"Main Day": exercises if isinstance(exercises, list) else []}}
        return migrated

    return data


def _write_plan_store(username: str, data: dict[str, Any]) -> None:
    """Write the full plan storage payload to disk."""
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    plan_file = _get_plan_file(username)
    with plan_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_plans(username: str) -> dict[str, dict[str, list[str]]]:
    """Load plans as `plan_name -> day_name -> exercise_list`."""
    store = _read_plan_store(username)
    return {name: payload.get("days", {}) for name, payload in store.get("plans", {}).items()}


def create_plan(username: str, plan_name: str) -> None:
    """Create a named plan if it does not exist."""
    cleaned = plan_name.strip()
    if not cleaned:
        raise ValueError("Plan name is required.")
    store = _read_plan_store(username)
    store["plans"].setdefault(cleaned, {"days": {}})
    _write_plan_store(username, store)


def delete_plan(username: str, plan_name: str) -> None:
    """Delete a named plan."""
    store = _read_plan_store(username)
    store.get("plans", {}).pop(plan_name, None)
    _write_plan_store(username, store)


def add_plan_day(username: str, plan_name: str, day_name: str) -> None:
    """Add a day to a plan."""
    cleaned = day_name.strip()
    if not cleaned:
        raise ValueError("Day name is required.")
    store = _read_plan_store(username)
    if plan_name not in store.get("plans", {}):
        raise ValueError("Plan does not exist.")
    store["plans"][plan_name].setdefault("days", {}).setdefault(cleaned, [])
    _write_plan_store(username, store)


def remove_plan_day(username: str, plan_name: str, day_name: str) -> None:
    """Remove a day from a plan."""
    store = _read_plan_store(username)
    if plan_name in store.get("plans", {}):
        store["plans"][plan_name].setdefault("days", {}).pop(day_name, None)
    _write_plan_store(username, store)


def add_exercise_to_day(username: str, plan_name: str, day_name: str, exercise_name: str) -> None:
    """Add an exercise to a specific day."""
    cleaned = exercise_name.strip()
    if not cleaned:
        raise ValueError("Exercise name is required.")
    store = _read_plan_store(username)
    if plan_name not in store.get("plans", {}):
        raise ValueError("Plan does not exist.")
    days = store["plans"][plan_name].setdefault("days", {})
    if day_name not in days:
        raise ValueError("Day does not exist.")
    days[day_name].append(cleaned)
    _write_plan_store(username, store)


def remove_exercise_from_day(username: str, plan_name: str, day_name: str, index: int) -> None:
    """Remove an exercise from a day by index."""
    store = _read_plan_store(username)
    exercises = store.get("plans", {}).get(plan_name, {}).setdefault("days", {}).get(day_name, [])
    if 0 <= index < len(exercises):
        exercises.pop(index)
    _write_plan_store(username, store)


def save_plan(username: str, plan_name: str, exercises: list[str]) -> None:
    """Backwards-compatible helper for a one-day plan format."""
    create_plan(username, plan_name)
    add_plan_day(username, plan_name, "Main Day")
    store = _read_plan_store(username)
    store["plans"][plan_name]["days"]["Main Day"] = [item.strip() for item in exercises if item.strip()]
    _write_plan_store(username, store)
