"""Workout logging frame."""

import datetime as dt
import tkinter as tk
from tkinter import messagebox, ttk

from app.auth import save_profile
from app.gamification import add_xp, calculate_xp, update_leaderboard
from app.workout import get_personal_record, get_training_summary, log_workout_entry


class WorkoutFrame(ttk.Frame):
    """Frame for logging workout sessions."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        """Create workout log form controls."""
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Log Workout", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=8)

        self.exercise_entry = ttk.Entry(self)
        self.sets_entry = ttk.Entry(self)
        self.reps_entry = ttk.Entry(self)
        self.weight_entry = ttk.Entry(self)
        self.notes_entry = ttk.Entry(self)
        self.summary_var = tk.StringVar(value="No workouts logged yet.")

        for label, widget in [
            ("Exercise", self.exercise_entry),
            ("Sets", self.sets_entry),
            ("Reps", self.reps_entry),
            ("Weight (kg)", self.weight_entry),
            ("Notes (optional)", self.notes_entry),
        ]:
            ttk.Label(self, text=label).pack(anchor="w")
            widget.pack(fill="x", pady=3)

        ttk.Button(self, text="Save Workout", command=self._save_workout).pack(pady=12, anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=6)
        ttk.Label(self, text="Tracking Summary", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(self, textvariable=self.summary_var, justify="left").pack(anchor="w", pady=4)

    def refresh(self) -> None:
        """Refresh the tracking summary section."""
        user = self.app.current_user
        if user is None:
            self.summary_var.set("Please log in to track workouts.")
            return

        summary = get_training_summary(user)
        if summary["total_sessions"] == 0:
            self.summary_var.set("No workouts logged yet.")
            return

        most_logged = summary["most_logged_exercise"] or "N/A"
        self.summary_var.set(
            "\n".join(
                [
                    f"Sessions: {summary['total_sessions']}",
                    f"Sets: {summary['total_sets']}",
                    f"Reps: {summary['total_reps']}",
                    f"Volume: {summary['total_volume_kg']} kg",
                    f"Unique exercises: {summary['unique_exercises']}",
                    f"Most logged: {most_logged}",
                ]
            )
        )

    def _save_workout(self) -> None:
        """Persist a workout entry and award XP."""
        user = self.app.current_user
        if user is None:
            messagebox.showwarning("Not logged in", "Please log in before logging workouts.")
            return

        try:
            sets = int(self.sets_entry.get())
            reps = int(self.reps_entry.get())
            weight = float(self.weight_entry.get())
            entry = log_workout_entry(
                user=user,
                date=dt.date.today().isoformat(),
                exercise_name=self.exercise_entry.get().strip(),
                sets=sets,
                reps=reps,
                weight_kg=weight,
                notes=self.notes_entry.get().strip(),
            )
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        self.refresh()

        xp_gain = calculate_xp(sets)
        add_xp(user, xp_gain)
        update_leaderboard(user)
        save_profile(user)
        personal_record = get_personal_record(user, entry["exercise"])
        pr_value = personal_record["estimated_1rm"] if personal_record else entry["estimated_1rm"]
        messagebox.showinfo(
            "Workout saved",
            (
                f"Saved: {entry['exercise']} on {entry['date']}.\n"
                f"Volume: {entry['volume_kg']} kg\n"
                f"Estimated 1RM: {entry['estimated_1rm']} kg\n"
                f"XP gained: {xp_gain}\n"
                f"Current PR (1RM): {pr_value} kg"
            ),
        )
