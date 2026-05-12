"""Dashboard frame showing user stats."""

import tkinter as tk
from tkinter import ttk


class DashboardFrame(ttk.Frame):
    """Home dashboard for profile and gamification stats."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        """Initialize dashboard widgets."""
        super().__init__(parent)
        self.app = app
        self.title_var = tk.StringVar(value="Dashboard")
        self.stats_var = tk.StringVar(value="Log in to view your stats.")

        ttk.Label(self, textvariable=self.title_var, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(self, textvariable=self.stats_var, justify="left").pack(anchor="w", pady=12)

    def refresh(self) -> None:
        """Refresh dashboard content based on current user."""
        user = self.app.current_user
        if user is None:
            self.title_var.set("Dashboard")
            self.stats_var.set("Please log in first.")
            return

        self.title_var.set(f"Welcome, {user.username}")
        self.stats_var.set(
            "\n".join(
                [
                    f"Goals: {user.goals or 'Not set'}",
                    f"XP: {user.xp}",
                    f"Level: {user.level}",
                    f"Rank: {user.rank}",
                    f"Workout entries: {len(user.workout_log)}",
                ]
            )
        )
