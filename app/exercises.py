"""Exercise data loading and filtering utilities."""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXERCISE_CSV_PATH = PROJECT_ROOT / "data" / "gym_exercise_data.csv"


def load_exercises() -> pd.DataFrame:
    """Load exercise data from the local CSV dataset."""
    return pd.read_csv(EXERCISE_CSV_PATH)


def filter_by_muscle(muscle_group: str) -> pd.DataFrame:
    """Return exercises filtered by case-insensitive muscle group."""
    df = load_exercises()
    return df[df["muscle_group"].str.lower() == muscle_group.lower()]
