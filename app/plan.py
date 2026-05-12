"""Workout plan and split management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
USERS_DIR = PROJECT_ROOT / "data" / "users"

WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
REST_MARKER = "__REST__"


def _get_plan_file(username: str) -> Path:
    return USERS_DIR / f"{username}_plans.json"


def _read_plan_store(username: str) -> dict[str, Any]:
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
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    plan_file = _get_plan_file(username)
    with plan_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _ensure_week_days(days: dict[str, list[str]]) -> dict[str, list[str]]:
    """Ensure all 7 weekdays exist, preserving existing data."""
    for day in WEEK_DAYS:
        days.setdefault(day, [])
    return {day: days[day] for day in WEEK_DAYS if day in days}


def load_plans(username: str) -> dict[str, dict[str, list[str]]]:
    """Load plans as `plan_name -> day_name -> exercise_list`."""
    store = _read_plan_store(username)
    return {name: _ensure_week_days(payload.get("days", {})) for name, payload in store.get("plans", {}).items()}


def create_plan(username: str, plan_name: str) -> None:
    """Create a named plan with all 7 weekdays pre-populated."""
    cleaned = plan_name.strip()
    if not cleaned:
        raise ValueError("Plan name is required.")
    store = _read_plan_store(username)
    if cleaned not in store["plans"]:
        store["plans"][cleaned] = {"days": {day: [] for day in WEEK_DAYS}}
    _write_plan_store(username, store)


def delete_plan(username: str, plan_name: str) -> None:
    store = _read_plan_store(username)
    store.get("plans", {}).pop(plan_name, None)
    _write_plan_store(username, store)


def set_rest_day(username: str, plan_name: str, day_name: str, rest: bool) -> None:
    """Mark a day as rest (clears exercises) or training (removes rest marker)."""
    store = _read_plan_store(username)
    days = store.get("plans", {}).get(plan_name, {}).setdefault("days", {})
    if rest:
        days[day_name] = [REST_MARKER]
    else:
        days[day_name] = []
    _write_plan_store(username, store)


def is_rest_day(exercises: list[str]) -> bool:
    """Return True if this day is marked as a rest day."""
    return exercises == [REST_MARKER]


def add_exercise_to_day(username: str, plan_name: str, day_name: str, exercise_name: str) -> None:
    cleaned = exercise_name.strip()
    if not cleaned:
        raise ValueError("Exercise name is required.")
    store = _read_plan_store(username)
    if plan_name not in store.get("plans", {}):
        raise ValueError("Plan does not exist.")
    days = store["plans"][plan_name].setdefault("days", {})
    if day_name not in days:
        days[day_name] = []
    exercises = days[day_name]
    # Remove rest marker if adding an exercise
    if exercises == [REST_MARKER]:
        exercises.clear()
    exercises.append(cleaned)
    _write_plan_store(username, store)


def remove_exercise_from_day(username: str, plan_name: str, day_name: str, index: int) -> None:
    store = _read_plan_store(username)
    exercises = store.get("plans", {}).get(plan_name, {}).setdefault("days", {}).get(day_name, [])
    if 0 <= index < len(exercises):
        exercises.pop(index)
    _write_plan_store(username, store)


def move_exercise(username: str, plan_name: str, day_name: str, index: int, direction: int) -> int:
    """Move exercise at index up (-1) or down (+1). Returns the new index."""
    store = _read_plan_store(username)
    exercises = store.get("plans", {}).get(plan_name, {}).get("days", {}).get(day_name, [])
    new_index = index + direction
    if 0 <= new_index < len(exercises):
        exercises[index], exercises[new_index] = exercises[new_index], exercises[index]
        _write_plan_store(username, store)
        return new_index
    return index


# Kept for backward compatibility
def add_plan_day(username: str, plan_name: str, day_name: str) -> None:
    store = _read_plan_store(username)
    if plan_name not in store.get("plans", {}):
        raise ValueError("Plan does not exist.")
    store["plans"][plan_name].setdefault("days", {}).setdefault(day_name.strip(), [])
    _write_plan_store(username, store)


def remove_plan_day(username: str, plan_name: str, day_name: str) -> None:
    store = _read_plan_store(username)
    if plan_name in store.get("plans", {}):
        store["plans"][plan_name].setdefault("days", {}).pop(day_name, None)
    _write_plan_store(username, store)


def save_plan(username: str, plan_name: str, exercises: list[str]) -> None:
    create_plan(username, plan_name)
    store = _read_plan_store(username)
    store["plans"][plan_name]["days"]["Monday"] = [item.strip() for item in exercises if item.strip()]
    _write_plan_store(username, store)
