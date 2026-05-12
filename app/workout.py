"""Workout session logging and exercise tracking logic."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.auth import save_profile
from app.profile import User
from app.progression import calculate_1rm


def _normalized_exercise_name(exercise_name: str) -> str:
    """Return a normalized exercise name for case-insensitive comparisons."""
    return exercise_name.strip().lower()


def validate_workout_input(exercise_name: str, sets: int, reps: int, weight_kg: float) -> None:
    """Validate workout input values and raise ValueError on invalid data."""
    if not exercise_name.strip():
        raise ValueError("Exercise name is required.")
    if sets <= 0:
        raise ValueError("Sets must be greater than 0.")
    if reps <= 0:
        raise ValueError("Reps must be greater than 0.")
    if weight_kg < 0:
        raise ValueError("Weight cannot be negative.")


def _build_workout_entry(
    date: str,
    exercise_name: str,
    sets: int,
    reps: int,
    weight_kg: float,
    notes: str = "",
) -> dict[str, Any]:
    """Create a normalized workout entry payload."""
    volume_kg = round(sets * reps * weight_kg, 2)
    estimated_1rm = calculate_1rm(weight_kg, reps)
    set_details = [{"set_number": idx + 1, "reps": reps, "weight_kg": weight_kg} for idx in range(sets)]
    return {
        "date": date,
        "exercise": exercise_name.strip(),
        "sets": sets,
        "reps": reps,
        "weight_kg": weight_kg,
        "volume_kg": volume_kg,
        "estimated_1rm": estimated_1rm,
        "set_details": set_details,
        "notes": notes.strip(),
    }


def log_workout_entry(
    user: User,
    date: str,
    exercise_name: str,
    sets: int,
    reps: int,
    weight_kg: float,
    notes: str = "",
) -> dict[str, Any]:
    """Append a validated workout entry to a user profile and persist it."""
    validate_workout_input(exercise_name, sets, reps, weight_kg)
    entry = _build_workout_entry(date, exercise_name, sets, reps, weight_kg, notes)
    user.workout_log.append(entry)
    save_profile(user)
    return entry


def get_exercise_history(user: User, exercise_name: str) -> list[dict[str, Any]]:
    """Return all workout entries for an exercise sorted by date."""
    target = _normalized_exercise_name(exercise_name)
    history = [entry for entry in user.workout_log if _normalized_exercise_name(entry.get("exercise", "")) == target]
    return sorted(history, key=lambda item: item.get("date", ""))


def get_recent_workouts(user: User, limit: int = 10) -> list[dict[str, Any]]:
    """Return recent workout entries ordered from newest to oldest."""
    if limit <= 0:
        return []
    return sorted(user.workout_log, key=lambda item: item.get("date", ""), reverse=True)[:limit]


def get_personal_record(user: User, exercise_name: str) -> dict[str, Any] | None:
    """Return the entry with the highest estimated 1RM for an exercise."""
    history = get_exercise_history(user, exercise_name)
    if not history:
        return None
    return max(history, key=lambda item: float(item.get("estimated_1rm", calculate_1rm(item.get("weight_kg", 0), item.get("reps", 0)))))


def get_training_summary(user: User) -> dict[str, Any]:
    """Return aggregate workout statistics for a user."""
    total_sessions = len(user.workout_log)
    if total_sessions == 0:
        return {
            "total_sessions": 0,
            "total_sets": 0,
            "total_reps": 0,
            "total_volume_kg": 0.0,
            "unique_exercises": 0,
            "most_logged_exercise": None,
        }

    total_sets = sum(int(entry.get("sets", 0)) for entry in user.workout_log)
    total_reps = sum(int(entry.get("sets", 0)) * int(entry.get("reps", 0)) for entry in user.workout_log)
    total_volume_kg = round(sum(float(entry.get("volume_kg", 0)) for entry in user.workout_log), 2)

    exercise_counts: dict[str, int] = defaultdict(int)
    for entry in user.workout_log:
        name = entry.get("exercise", "").strip()
        if name:
            exercise_counts[name] += 1

    most_logged_exercise = None
    if exercise_counts:
        most_logged_exercise = max(exercise_counts.items(), key=lambda item: item[1])[0]

    return {
        "total_sessions": total_sessions,
        "total_sets": total_sets,
        "total_reps": total_reps,
        "total_volume_kg": total_volume_kg,
        "unique_exercises": len(exercise_counts),
        "most_logged_exercise": most_logged_exercise,
    }


def get_exercise_catalog(user: User) -> list[str]:
    """Return sorted unique exercise names from a user's workout history."""
    exercises = {entry.get("exercise", "").strip() for entry in user.workout_log if entry.get("exercise", "").strip()}
    return sorted(exercises)
