"""Exercise data loading and filtering utilities."""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXERCISE_CSV_PATH = PROJECT_ROOT / "data" / "gym_exercise_data.csv"

_cache: pd.DataFrame | None = None


def load_exercises() -> pd.DataFrame:
    """Load exercise data from the local CSV dataset (cached after first load)."""
    global _cache
    if _cache is None:
        _cache = pd.read_csv(EXERCISE_CSV_PATH)
    return _cache


def get_muscle_groups() -> list[str]:
    """Return sorted unique muscle group names."""
    df = load_exercises()
    return sorted(df["muscle_group"].dropna().unique().tolist())


def get_equipment_types() -> list[str]:
    """Return sorted unique equipment types."""
    df = load_exercises()
    return sorted(df["equipment"].dropna().unique().tolist())


def filter_by_muscle(muscle_group: str) -> pd.DataFrame:
    """Return exercises filtered by case-insensitive muscle group."""
    df = load_exercises()
    return df[df["muscle_group"].str.lower() == muscle_group.lower()]


def filter_exercises(
    muscle_group: str = "",
    equipment: str = "",
    difficulty: str = "",
    search: str = "",
) -> pd.DataFrame:
    """Return exercises matching all non-empty filter criteria."""
    df = load_exercises()
    if muscle_group:
        df = df[df["muscle_group"].str.lower() == muscle_group.lower()]
    if equipment:
        df = df[df["equipment"].str.lower() == equipment.lower()]
    if difficulty:
        df = df[df["difficulty"].str.lower() == difficulty.lower()]
    if search:
        df = df[df["exercise"].str.lower().str.contains(search.lower(), na=False)]
    return df


def get_exercise_names(muscle_group: str = "") -> list[str]:
    """Return sorted exercise names, optionally filtered by muscle group."""
    if muscle_group and muscle_group != "All":
        df = filter_by_muscle(muscle_group)
    else:
        df = load_exercises()
    return sorted(df["exercise"].dropna().tolist())
