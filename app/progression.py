"""Progression analytics and plateau suggestions."""

from typing import Iterable


def calculate_1rm(weight: float, reps: int) -> float:
    """Estimate 1RM using the Epley formula."""
    return round(weight * (1 + reps / 30), 2)


def get_progression(exercise_name: str, workout_log: list[dict]) -> list[tuple[str, float]]:
    """Return date and estimated 1RM pairs for the selected exercise."""
    progression_data: list[tuple[str, float]] = []
    for entry in workout_log:
        if entry.get("exercise", "").lower() == exercise_name.lower():
            date = entry.get("date", "")
            reps = int(entry.get("reps", 0))
            weight = float(entry.get("weight_kg", 0))
            progression_data.append((date, calculate_1rm(weight, reps)))
    return progression_data


def detect_plateau(progression_data: Iterable[tuple[str, float]], window: int = 4) -> bool:
    """Return True when the last window of sessions improves by less than 2%."""
    data = list(progression_data)
    if len(data) < window:
        return False

    recent = data[-window:]
    start_1rm = recent[0][1]
    end_1rm = recent[-1][1]
    if start_1rm <= 0:
        return False

    improvement_pct = ((end_1rm - start_1rm) / start_1rm) * 100
    return improvement_pct < 2


def get_suggestions() -> list[str]:
    """Return generic plateau-busting suggestions."""
    return [
        "Schedule a deload week to reduce fatigue and recover.",
        "Increase sleep and protein intake for better recovery.",
        "Adjust training volume or intensity for your next block.",
        "Review technique and range of motion on core lifts.",
        "Track nutrition consistency for 2 weeks before major changes.",
    ]
