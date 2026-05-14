"""Workout logging frame."""

import datetime as dt
import tkinter as tk
from tkinter import messagebox, ttk

from app.auth import save_profile
from app.camera import run_form_check_session
from app.exercises import get_exercise_names, get_muscle_groups
from app.gamification import add_xp, calculate_xp, update_leaderboard
from app.workout import get_personal_record, get_recent_workouts, get_training_summary, log_workout_entry

_ALL = "All"


class WorkoutFrame(ttk.Frame):
    """Frame for logging workout sessions."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Log Workout", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 4))

        # ── Filter row ────────────────────────────────────────────────
        filter_row = ttk.Frame(self)
        filter_row.pack(fill="x", pady=(0, 2))

        ttk.Label(filter_row, text="Muscle:").pack(side="left")
        self.muscle_var = tk.StringVar(value=_ALL)
        muscle_groups = [_ALL] + get_muscle_groups()
        self.muscle_box = ttk.Combobox(
            filter_row, textvariable=self.muscle_var,
            values=muscle_groups, state="readonly", width=14,
        )
        self.muscle_box.pack(side="left", padx=(4, 12))
        self.muscle_box.bind("<<ComboboxSelected>>", self._on_muscle_changed)

        ttk.Label(filter_row, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_row, textvariable=self.search_var, width=18)
        search_entry.pack(side="left", padx=(4, 4))
        self.search_var.trace_add("write", self._on_search_changed)

        # ── Exercise selector row ─────────────────────────────────────
        ex_row = ttk.Frame(self)
        ex_row.pack(fill="x", pady=(2, 6))

        ttk.Label(ex_row, text="Exercise:").pack(side="left")
        self.exercise_var = tk.StringVar()
        self.exercise_box = ttk.Combobox(
            ex_row, textvariable=self.exercise_var, state="readonly", width=36,
        )
        self.exercise_box.pack(side="left", padx=4)
        self._reload_exercise_list()

        # ── Entry fields ──────────────────────────────────────────────
        form = ttk.Frame(self)
        form.pack(fill="x", pady=4)

        self.sets_entry = ttk.Entry(form, width=10)
        self.reps_entry = ttk.Entry(form, width=10)
        self.weight_entry = ttk.Entry(form, width=10)
        self.notes_entry = ttk.Entry(form, width=32)

        for col, (label, widget) in enumerate([
            ("Sets", self.sets_entry),
            ("Reps", self.reps_entry),
            ("Weight (kg)", self.weight_entry),
            ("Notes (optional)", self.notes_entry),
        ]):
            ttk.Label(form, text=label).grid(row=0, column=col, sticky="w", padx=(0, 6))
            widget.grid(row=1, column=col, sticky="w", padx=(0, 6))

        # ── Action buttons ────────────────────────────────────────────
        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", pady=8)
        self.save_btn = ttk.Button(btn_row, text="Save Workout", command=self._save_workout)
        self.save_btn.pack(side="left", padx=(0, 8))
        self.form_btn = ttk.Button(btn_row, text="Form Check (Camera)", command=self._run_form_check)
        self.form_btn.pack(side="left")

        # Bind Enter key on numeric fields
        for widget in (self.sets_entry, self.reps_entry, self.weight_entry, self.notes_entry):
            widget.bind("<Return>", lambda _e: self._save_workout())

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=6)

        # ── Summary ───────────────────────────────────────────────────
        bottom = ttk.Frame(self)
        bottom.pack(fill="both", expand=True)

        # Left: stats
        stats_col = ttk.Frame(bottom)
        stats_col.pack(side="left", fill="y", padx=(0, 16))
        ttk.Label(stats_col, text="Training Summary", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.summary_var = tk.StringVar(value="No workouts logged yet.")
        ttk.Label(stats_col, textvariable=self.summary_var, justify="left").pack(anchor="w", pady=4)

        # Right: recent workouts table
        recent_col = ttk.Frame(bottom)
        recent_col.pack(side="left", fill="both", expand=True)
        ttk.Label(recent_col, text="Recent Workouts", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        cols = ("Date", "Exercise", "Sets", "Reps", "Weight", "Vol (kg)", "Est 1RM")
        self.recent_tree = ttk.Treeview(recent_col, columns=cols, show="headings", height=8)
        for col in cols:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=80, anchor="center")
        self.recent_tree.column("Exercise", width=160, anchor="w")
        scroll = ttk.Scrollbar(recent_col, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scroll.set)
        self.recent_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

    # ── Helpers ───────────────────────────────────────────────────────

    def _reload_exercise_list(self) -> None:
        muscle = self.muscle_var.get()
        names = get_exercise_names(muscle if muscle != _ALL else "")
        search = self.search_var.get().strip().lower()
        if search:
            names = [n for n in names if search in n.lower()]
        self.exercise_box["values"] = names
        if names and self.exercise_var.get() not in names:
            self.exercise_var.set(names[0])

    def _on_muscle_changed(self, _event: tk.Event | None = None) -> None:
        self.search_var.set("")
        self._reload_exercise_list()

    def _on_search_changed(self, *_args) -> None:
        self._reload_exercise_list()

    def _clear_form(self) -> None:
        self.exercise_var.set("")
        self.sets_entry.delete(0, "end")
        self.reps_entry.delete(0, "end")
        self.weight_entry.delete(0, "end")
        self.notes_entry.delete(0, "end")

    # ── Actions ───────────────────────────────────────────────────────

    def _save_workout(self) -> None:
        user = self.app.current_user
        if user is None:
            messagebox.showwarning("Not logged in", "Please log in before logging workouts.")
            return

        exercise_name = self.exercise_var.get().strip()
        if not exercise_name:
            messagebox.showerror("Missing exercise", "Please select an exercise from the dropdown.")
            return

        try:
            sets = int(self.sets_entry.get())
            reps = int(self.reps_entry.get())
            weight = float(self.weight_entry.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Sets and reps must be whole numbers; weight must be a number.")
            return

        try:
            entry = log_workout_entry(
                user=user,
                date=dt.date.today().isoformat(),
                exercise_name=exercise_name,
                sets=sets,
                reps=reps,
                weight_kg=weight,
                notes=self.notes_entry.get().strip(),
            )
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        xp_gain = calculate_xp(sets)
        add_xp(user, xp_gain)
        update_leaderboard(user)
        save_profile(user)

        personal_record = get_personal_record(user, entry["exercise"])
        pr_value = personal_record["estimated_1rm"] if personal_record else entry["estimated_1rm"]

        self._clear_form()
        self.refresh()

        messagebox.showinfo(
            "Workout saved",
            (
                f"Saved: {entry['exercise']} — {entry['date']}\n"
                f"Volume: {entry['volume_kg']} kg\n"
                f"Estimated 1RM: {entry['estimated_1rm']} kg\n"
                f"PR (1RM): {pr_value} kg\n"
                f"XP gained: +{xp_gain}  (Total: {user.xp})"
            ),
        )

    def _run_form_check(self) -> None:
        exercise_name = self.exercise_var.get().strip() or "Exercise"
        result = run_form_check_session(exercise_name, duration_seconds=60)
        if not result.get("success"):
            messagebox.showwarning("Form Check", result.get("message", "Form check failed."))
            return

        engine = result.get("engine", "OpenCV")
        tips = "\n• ".join(result.get("tips", []))
        rom = result.get("rom_score", 0)
        con = result.get("consistency_score", 0)
        stab = result.get("stability_score", 0)

        messagebox.showinfo(
            "Form Check Result",
            (
                f"Exercise: {result.get('exercise', exercise_name)}\n"
                f"Engine: {engine}\n"
                f"\nOverall score: {result['score']}/100\n"
                f"Range of motion: {rom}/100\n"
                f"Consistency:     {con}/100\n"
                f"Stability:       {stab}/100\n"
                f"\nReps detected: {result.get('rep_count', 0)}\n"
                f"\nFeedback:\n• {tips}"
            ),
        )

    # ── Refresh ───────────────────────────────────────────────────────

    def refresh(self) -> None:
        user = self.app.current_user
        if user is None:
            self.summary_var.set("Please log in to track workouts.")
            self.recent_tree.delete(*self.recent_tree.get_children())
            return

        summary = get_training_summary(user)
        if summary["total_sessions"] == 0:
            self.summary_var.set("No workouts logged yet.")
        else:
            most_logged = summary["most_logged_exercise"] or "N/A"
            self.summary_var.set(
                "\n".join([
                    f"Sessions: {summary['total_sessions']}",
                    f"Total sets: {summary['total_sets']}",
                    f"Total reps: {summary['total_reps']}",
                    f"Total volume: {summary['total_volume_kg']} kg",
                    f"Unique exercises: {summary['unique_exercises']}",
                    f"Most logged: {most_logged}",
                ])
            )

        self.recent_tree.delete(*self.recent_tree.get_children())
        for entry in get_recent_workouts(user, limit=20):
            self.recent_tree.insert("", "end", values=(
                entry.get("date", ""),
                entry.get("exercise", ""),
                entry.get("sets", ""),
                entry.get("reps", ""),
                entry.get("weight_kg", ""),
                entry.get("volume_kg", ""),
                entry.get("estimated_1rm", ""),
            ))
