"""Leaderboard frame."""

import tkinter as tk
from tkinter import ttk

from app.gamification import get_top_n


class LeaderboardFrame(ttk.Frame):
    """Frame showing local leaderboard rankings."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        """Initialize leaderboard widgets."""
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Leaderboard", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=8)
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill="both", expand=True)

    def refresh(self) -> None:
        """Reload top leaderboard entries."""
        self.listbox.delete(0, "end")
        for idx, row in enumerate(get_top_n(10), start=1):
            self.listbox.insert(
                "end",
                f"{idx}. {row['username']} — XP: {row['xp']} | Level: {row['level']} | Rank: {row['rank']}",
            )
