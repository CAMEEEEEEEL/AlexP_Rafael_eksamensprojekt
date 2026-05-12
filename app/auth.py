"""Authentication and profile persistence utilities."""

import hashlib
import json
from pathlib import Path

from app.profile import User

PROJECT_ROOT = Path(__file__).resolve().parent.parent
USERS_DIR = PROJECT_ROOT / "data" / "users"


def _get_user_file(username: str) -> Path:
    """Return the JSON profile path for a given username."""
    return USERS_DIR / f"{username}.json"


def _hash_password(password: str) -> str:
    """Hash a plaintext password with SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(
    username: str,
    password: str,
    age: int,
    weight_kg: float,
    height_cm: float,
    goals: str,
) -> bool:
    """Register a new user and persist their profile to local JSON storage."""
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    user_file = _get_user_file(username)
    if user_file.exists():
        return False

    user = User(
        username=username,
        password_hash=_hash_password(password),
        age=age,
        weight_kg=weight_kg,
        height_cm=height_cm,
        goals=goals,
    )
    save_profile(user)
    return True


def login_user(username: str, password: str) -> User | None:
    """Validate credentials and return the user profile if login succeeds."""
    user = load_profile(username)
    if not user:
        return None
    return user if user.password_hash == _hash_password(password) else None


def load_profile(username: str) -> User | None:
    """Load a user profile from `data/users/{username}.json`."""
    user_file = _get_user_file(username)
    if not user_file.exists():
        return None
    with user_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return User.from_dict(data)


def save_profile(user: User) -> None:
    """Save a user profile to local JSON storage."""
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    user_file = _get_user_file(user.username)
    with user_file.open("w", encoding="utf-8") as f:
        json.dump(user.to_dict(), f, indent=2)
