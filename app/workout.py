"""Workout session logging and exercise tracking logic."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.auth import save_profile
from app.profile import User
from app.progression import calculate_1rm


def _normalized(name: str) -> str:
    return name.strip().lower()


# ── Reps parsing ──────────────────────────────────────────────────────────────

def parse_reps(reps_str: str, sets: int) -> list[int]:
    """Parse a reps string into a list of ints, one per set.

    '10'     with sets=3  → [10, 10, 10]
    '8,6,4'  with sets=3  → [8, 6, 4]
    """
    parts = [p.strip() for p in str(reps_str).split(",")]
    try:
        values = [int(p) for p in parts if p]
    except ValueError:
        raise ValueError("Reps must be whole numbers, e.g. '10' or '8,6,4'.")

    if not values:
        raise ValueError("Reps field is required.")

    if len(values) == 1:
        return values * sets          # same reps for every set
    if len(values) != sets:
        raise ValueError(
            f"You entered {sets} sets but {len(values)} rep values. "
            f"Either enter one number (same for all sets) or one per set."
        )
    return values


# ── Validation ────────────────────────────────────────────────────────────────

def validate_workout_input(
    exercise_name: str,
    sets: int,
    reps_list: list[int],
    weight_kg: float,
) -> None:
    if not exercise_name.strip():
        raise ValueError("Exercise name is required.")
    if sets <= 0:
        raise ValueError("Sets must be greater than 0.")
    if any(r <= 0 for r in reps_list):
        raise ValueError("All rep counts must be greater than 0.")
    if weight_kg < 0:
        raise ValueError("Weight cannot be negative.")


# ── Entry builder ─────────────────────────────────────────────────────────────

def _build_workout_entry(
    date: str,
    exercise_name: str,
    sets: int,
    reps_list: list[int],
    weight_kg: float,
    notes: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    volume_kg = round(sum(r * weight_kg for r in reps_list), 2)
    estimated_1rm = max(calculate_1rm(weight_kg, r) for r in reps_list)
    total_reps = sum(reps_list)
    reps_display = ",".join(str(r) for r in reps_list) if len(set(reps_list)) > 1 else str(reps_list[0])
    set_details = [
        {"set_number": i + 1, "reps": reps_list[i], "weight_kg": weight_kg}
        for i in range(sets)
    ]
    return {
        "date": date,
        "exercise": exercise_name.strip(),
        "sets": sets,
        "reps": reps_display,          # "10" or "8,6,4" — for display
        "total_reps": total_reps,
        "weight_kg": weight_kg,
        "volume_kg": volume_kg,
        "estimated_1rm": estimated_1rm,
        "set_details": set_details,
        "notes": notes.strip(),
        "session_id": session_id,
    }


# ── Logging ───────────────────────────────────────────────────────────────────

def log_workout_entry(
    user: User,
    date: str,
    exercise_name: str,
    sets: int,
    reps_input: str,
    weight_kg: float,
    notes: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    """Parse, validate and append a workout entry; persist the profile."""
    reps_list = parse_reps(reps_input, sets)
    validate_workout_input(exercise_name, sets, reps_list, weight_kg)
    entry = _build_workout_entry(date, exercise_name, sets, reps_list,
                                 weight_kg, notes, session_id)
    user.workout_log.append(entry)
    save_profile(user)
    return entry


# ── Queries ───────────────────────────────────────────────────────────────────

def get_exercise_history(user: User, exercise_name: str) -> list[dict[str, Any]]:
    target = _normalized(exercise_name)
    history = [e for e in user.workout_log if _normalized(e.get("exercise", "")) == target]
    return sorted(history, key=lambda e: e.get("date", ""))


def get_recent_workouts(user: User, limit: int = 10) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return sorted(user.workout_log, key=lambda e: e.get("date", ""), reverse=True)[:limit]


def get_personal_record(user: User, exercise_name: str) -> dict[str, Any] | None:
    history = get_exercise_history(user, exercise_name)
    if not history:
        return None
    return max(history, key=lambda e: float(e.get("estimated_1rm", 0)))


def get_training_summary(user: User) -> dict[str, Any]:
    """Return aggregate stats. Sessions are counted by unique session_id."""
    log = user.workout_log
    if not log:
        return {
            "total_sessions": 0, "total_sets": 0, "total_reps": 0,
            "total_volume_kg": 0.0, "unique_exercises": 0,
            "most_logged_exercise": None,
        }

    # Count unique sessions (entries without session_id each count as 1)
    session_ids: set[str] = set()
    solo_count = 0
    for e in log:
        sid = e.get("session_id", "")
        if sid:
            session_ids.add(sid)
        else:
            solo_count += 1
    total_sessions = len(session_ids) + solo_count

    total_sets = sum(int(e.get("sets", 0)) for e in log)
    total_reps = sum(int(e.get("total_reps", 0)) or
                     int(e.get("sets", 0)) * _safe_reps(e.get("reps", 0))
                     for e in log)
    total_volume_kg = round(sum(float(e.get("volume_kg", 0)) for e in log), 2)

    exercise_counts: dict[str, int] = defaultdict(int)
    for e in log:
        name = e.get("exercise", "").strip()
        if name:
            exercise_counts[name] += 1

    return {
        "total_sessions": total_sessions,
        "total_sets": total_sets,
        "total_reps": total_reps,
        "total_volume_kg": total_volume_kg,
        "unique_exercises": len(exercise_counts),
        "most_logged_exercise": max(exercise_counts, key=exercise_counts.get) if exercise_counts else None,
    }


def _safe_reps(val: Any) -> int:
    """Convert a reps value (might be '8,6,4' or int) to a total int."""
    try:
        return sum(int(x) for x in str(val).split(","))
    except Exception:
        return 0


def get_exercise_catalog(user: User) -> list[str]:
    exercises = {e.get("exercise", "").strip() for e in user.workout_log if e.get("exercise", "").strip()}
    return sorted(exercises)
