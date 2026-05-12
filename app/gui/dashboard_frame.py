"""Dashboard frame showing user stats and recent activity."""

import tkinter as tk
from tkinter import ttk

from app.workout import get_recent_workouts, get_training_summary


def _bmi(weight_kg: float, height_cm: float) -> str:
    if height_cm <= 0 or weight_kg <= 0:
        return "N/A"
    bmi = weight_kg / ((height_cm / 100) ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return f"{bmi:.1f} ({category})"


class DashboardFrame(ttk.Frame):
    """Home dashboard showing profile, gamification stats, and recent activity."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Dashboard", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 4))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        # ── Left column: profile + stats ──────────────────────────────
        left = ttk.Frame(body)
        left.pack(side="left", fill="y", padx=(0, 24), anchor="n")

        self.welcome_var = tk.StringVar(value="Welcome!")
        ttk.Label(left, textvariable=self.welcome_var, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        self.profile_var = tk.StringVar(value="Log in to view your profile.")
        ttk.Label(left, textvariable=self.profile_var, justify="left").pack(anchor="w")

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(left, text="Training Stats", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.stats_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.stats_var, justify="left").pack(anchor="w", pady=4)

        # ── Right column: recent workouts ─────────────────────────────
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, anchor="n")

        ttk.Label(right, text="Recent Workouts", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        cols = ("Date", "Exercise", "Sets × Reps", "Weight (kg)", "Vol (kg)")
        self.recent_tree = ttk.Treeview(right, columns=cols, show="headings", height=10)
        for col in cols:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=100, anchor="center")
        self.recent_tree.column("Exercise", width=180, anchor="w")

        scroll = ttk.Scrollbar(right, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scroll.set)
        self.recent_tree.pack(side="left", fill="both", expand=True, pady=4)
        scroll.pack(side="left", fill="y", pady=4)

    def refresh(self) -> None:
        user = self.app.current_user
        if user is None:
            self.welcome_var.set("Welcome!")
            self.profile_var.set("Log in to view your profile.")
            self.stats_var.set("")
            self.recent_tree.delete(*self.recent_tree.get_children())
            return

        self.welcome_var.set(f"Welcome back, {user.username}!")
        self.profile_var.set(
            "\n".join([
                f"Age:     {user.age or '—'}",
                f"Weight:  {user.weight_kg or '—'} kg",
                f"Height:  {user.height_cm or '—'} cm",
                f"BMI:     {_bmi(user.weight_kg, user.height_cm)}",
                f"Goals:   {user.goals or 'Not set'}",
                f"",
                f"XP:      {user.xp}",
                f"Level:   {user.level}",
                f"Rank:    {user.rank}",
            ])
        )

        summary = get_training_summary(user)
        if summary["total_sessions"] == 0:
            self.stats_var.set("No workouts logged yet. Start training!")
        else:
            self.stats_var.set(
                "\n".join([
                    f"Sessions logged:  {summary['total_sessions']}",
                    f"Total volume:     {summary['total_volume_kg']} kg",
                    f"Unique exercises: {summary['unique_exercises']}",
                    f"Most logged:      {summary['most_logged_exercise'] or 'N/A'}",
                ])
            )

        self.recent_tree.delete(*self.recent_tree.get_children())
        for entry in get_recent_workouts(user, limit=10):
            sets_reps = f"{entry.get('sets', '')} × {entry.get('reps', '')}"
            self.recent_tree.insert("", "end", values=(
                entry.get("date", ""),
                entry.get("exercise", ""),
                sets_reps,
                entry.get("weight_kg", ""),
                entry.get("volume_kg", ""),
            ))
