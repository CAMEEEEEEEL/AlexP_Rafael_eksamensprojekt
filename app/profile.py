"""User profile model for FitTrack."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class User:
    """Represents a FitTrack user profile."""

    username: str
    password_hash: str
    age: int
    weight_kg: float
    height_cm: float
    goals: str
    xp: int = 0
    level: int = 1
    rank: str = "Beginner"
    workout_log: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the user profile into a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Create a User instance from a dictionary."""
        return cls(**data)
