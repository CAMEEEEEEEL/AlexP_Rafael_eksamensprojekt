"""Workout logging frame — with sessions, plan import, and per-set reps."""

import datetime as dt
import tkinter as tk
from tkinter import messagebox, ttk

from app.auth import save_profile
from app.camera import run_form_check_session
from app.exercises import get_exercise_names, get_muscle_groups
from app.gamification import add_xp, calculate_xp, update_leaderboard
from app.plan import WEEK_DAYS, is_rest_day, load_plans
from app.workout import (
    get_personal_record,
    get_recent_workouts,
    get_training_summary,
    log_workout_entry,
    parse_reps,
)

_ALL = "All"


class WorkoutFrame(ttk.Frame):
    """Frame for logging workout sessions."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Log Workout", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 2))

        # ── Session bar ───────────────────────────────────────────────
        session_bar = ttk.Frame(self)
        session_bar.pack(fill="x", pady=(0, 4))

        self.session_label = tk.StringVar(value="No active session")
        ttk.Label(session_bar, textvariable=self.session_label, foreground="grey").pack(side="left")
        self.start_btn = ttk.Button(session_bar, text="Start Session", command=self._start_session)
        self.start_btn.pack(side="left", padx=(12, 4))
        self.end_btn = ttk.Button(session_bar, text="End Session", command=self._end_session, state="disabled")
        self.end_btn.pack(side="left")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(0, 6))

        # ── Load from plan (collapsible row) ──────────────────────────
        plan_bar = ttk.Frame(self)
        plan_bar.pack(fill="x", pady=(0, 4))

        ttk.Label(plan_bar, text="Load from Plan:").pack(side="left")
        self.plan_var = tk.StringVar()
        self.plan_box = ttk.Combobox(plan_bar, textvariable=self.plan_var, state="readonly", width=20)
        self.plan_box.pack(side="left", padx=(4, 8))
        self.plan_box.bind("<<ComboboxSelected>>", self._on_plan_selected)

        self.day_var = tk.StringVar()
        self.day_box = ttk.Combobox(plan_bar, textvariable=self.day_var, state="readonly", width=14)
        self.day_box.pack(side="left", padx=(0, 8))
        self.day_box.bind("<<ComboboxSelected>>", self._on_day_selected)

        ttk.Button(plan_bar, text="Load", command=self._load_plan_exercises).pack(side="left")

        # Plan exercise list (hidden until loaded)
        self.plan_ex_frame = ttk.Frame(self)
        self.plan_ex_frame.pack(fill="x", pady=(0, 4))
        ttk.Label(self.plan_ex_frame, text="Today's exercises — click to pre-fill:").pack(anchor="w")
        self.plan_ex_list = tk.Listbox(self.plan_ex_frame, height=4, selectmode="single",
                                        exportselection=False, font=("Segoe UI", 9))
        self.plan_ex_list.pack(fill="x")
        self.plan_ex_list.bind("<<ListboxSelect>>", self._on_plan_exercise_selected)
        self.plan_ex_frame.pack_forget()   # hidden by default

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(0, 6))

        # ── Exercise picker ───────────────────────────────────────────
        filter_row = ttk.Frame(self)
        filter_row.pack(fill="x", pady=(0, 2))

        ttk.Label(filter_row, text="Muscle:").pack(side="left")
        self.muscle_var = tk.StringVar(value=_ALL)
        muscle_box = ttk.Combobox(filter_row, textvariable=self.muscle_var,
                                   values=[_ALL] + get_muscle_groups(), state="readonly", width=14)
        muscle_box.pack(side="left", padx=(4, 12))
        muscle_box.bind("<<ComboboxSelected>>", self._on_muscle_changed)

        ttk.Label(filter_row, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(filter_row, textvariable=self.search_var, width=18).pack(side="left", padx=(4, 4))
        self.search_var.trace_add("write", self._on_search_changed)

        ex_row = ttk.Frame(self)
        ex_row.pack(fill="x", pady=(2, 6))
        ttk.Label(ex_row, text="Exercise:").pack(side="left")
        self.exercise_var = tk.StringVar()
        self.exercise_box = ttk.Combobox(ex_row, textvariable=self.exercise_var,
                                          state="readonly", width=36)
        self.exercise_box.pack(side="left", padx=4)
        self._reload_exercise_list()

        # ── Entry fields ──────────────────────────────────────────────
        form = ttk.Frame(self)
        form.pack(fill="x", pady=4)

        self.sets_entry   = ttk.Entry(form, width=8)
        self.reps_entry   = ttk.Entry(form, width=14)
        self.weight_entry = ttk.Entry(form, width=8)
        self.notes_entry  = ttk.Entry(form, width=28)

        for col, (lbl, widget, hint) in enumerate([
            ("Sets",                self.sets_entry,   ""),
            ("Reps (e.g. 10 or 8,6,4)", self.reps_entry, ""),
            ("Weight (kg)",         self.weight_entry, ""),
            ("Notes (optional)",    self.notes_entry,  ""),
        ]):
            ttk.Label(form, text=lbl).grid(row=0, column=col, sticky="w", padx=(0, 8))
            widget.grid(row=1, column=col, sticky="w", padx=(0, 8))

        # ── Action buttons ────────────────────────────────────────────
        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", pady=6)
        ttk.Button(btn_row, text="Save Exercise", command=self._save_workout).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Form Check (Camera)", command=self._run_form_check).pack(side="left")

        for widget in (self.sets_entry, self.reps_entry, self.weight_entry, self.notes_entry):
            widget.bind("<Return>", lambda _e: self._save_workout())

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=4)

        # ── Summary + recent workouts ─────────────────────────────────
        bottom = ttk.Frame(self)
        bottom.pack(fill="both", expand=True)

        stats_col = ttk.Frame(bottom)
        stats_col.pack(side="left", fill="y", padx=(0, 16))
        ttk.Label(stats_col, text="Training Summary", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.summary_var = tk.StringVar(value="No workouts logged yet.")
        ttk.Label(stats_col, textvariable=self.summary_var, justify="left").pack(anchor="w", pady=4)

        recent_col = ttk.Frame(bottom)
        recent_col.pack(side="left", fill="both", expand=True)
        ttk.Label(recent_col, text="Recent Exercises", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        cols = ("Date", "Exercise", "Sets", "Reps", "Weight", "Vol (kg)", "Est 1RM")
        self.recent_tree = ttk.Treeview(recent_col, columns=cols, show="headings", height=7)
        for col in cols:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=80, anchor="center")
        self.recent_tree.column("Exercise", width=160, anchor="w")
        scroll = ttk.Scrollbar(recent_col, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scroll.set)
        self.recent_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

    # ── Session management ────────────────────────────────────────────

    def _start_session(self) -> None:
        if self.app.current_user is None:
            messagebox.showwarning("Not logged in", "Please log in first.")
            return
        self.app.current_session_id = dt.datetime.now().isoformat(timespec="seconds")
        self._update_session_ui()

    def _end_session(self) -> None:
        self.app.current_session_id = ""
        self._update_session_ui()
        messagebox.showinfo("Session ended", "Great workout! Session has been saved.")

    def _update_session_ui(self) -> None:
        if self.app.current_session_id:
            t = self.app.current_session_id[11:16]   # HH:MM
            self.session_label.set(f"Session active since {t}")
            self.start_btn.state(["disabled"])
            self.end_btn.state(["!disabled"])
        else:
            self.session_label.set("No active session")
            self.start_btn.state(["!disabled"])
            self.end_btn.state(["disabled"])

    # ── Plan import ───────────────────────────────────────────────────

    def _reload_plans(self) -> None:
        user = self.app.current_user
        if user is None:
            return
        plans = load_plans(user.username)
        self.plan_box["values"] = sorted(plans.keys())

    def _on_plan_selected(self, _e=None) -> None:
        user = self.app.current_user
        plan = self.plan_var.get()
        if not user or not plan:
            return
        plans = load_plans(user.username)
        days = [d for d, exs in plans.get(plan, {}).items() if not is_rest_day(exs)]
        self.day_box["values"] = days
        # Default to today's weekday if available
        today = dt.date.today().strftime("%A")
        self.day_var.set(today if today in days else (days[0] if days else ""))

    def _on_day_selected(self, _e=None) -> None:
        pass  # user clicks Load button manually

    def _load_plan_exercises(self) -> None:
        user = self.app.current_user
        plan = self.plan_var.get()
        day = self.day_var.get()
        if not user or not plan or not day:
            messagebox.showwarning("Select plan", "Choose a plan and day first.")
            return
        plans = load_plans(user.username)
        exercises = plans.get(plan, {}).get(day, [])
        if not exercises or is_rest_day(exercises):
            messagebox.showinfo("Rest Day", "That day is marked as a rest day.")
            return
        self.plan_ex_list.delete(0, "end")
        for ex in exercises:
            self.plan_ex_list.insert("end", ex)
        self.plan_ex_frame.pack(fill="x", pady=(0, 4), after=self.plan_ex_frame.master.children.get(
            list(self.plan_ex_frame.master.children.keys())[0]))
        # Re-show the frame
        self.plan_ex_frame.pack(fill="x", pady=(0, 4))

    def _on_plan_exercise_selected(self, _e=None) -> None:
        sel = self.plan_ex_list.curselection()
        if not sel:
            return
        name = self.plan_ex_list.get(sel[0])
        self.exercise_var.set(name)
        # Try to match muscle group to update dropdown values
        self._reload_exercise_list()

    # ── Exercise picker helpers ───────────────────────────────────────

    def _reload_exercise_list(self) -> None:
        muscle = self.muscle_var.get()
        names = get_exercise_names(muscle if muscle != _ALL else "")
        search = self.search_var.get().strip().lower()
        if search:
            names = [n for n in names if search in n.lower()]
        self.exercise_box["values"] = names
        if names and self.exercise_var.get() not in names:
            self.exercise_box["values"] = names

    def _on_muscle_changed(self, _e=None) -> None:
        self.search_var.set("")
        self._reload_exercise_list()

    def _on_search_changed(self, *_args) -> None:
        self._reload_exercise_list()

    def _clear_form(self) -> None:
        self.sets_entry.delete(0, "end")
        self.reps_entry.delete(0, "end")
        self.weight_entry.delete(0, "end")
        self.notes_entry.delete(0, "end")

    # ── Save workout ──────────────────────────────────────────────────

    def _save_workout(self) -> None:
        user = self.app.current_user
        if user is None:
            messagebox.showwarning("Not logged in", "Please log in first.")
            return

        # Prompt to start session if none active
        if not self.app.current_session_id:
            if messagebox.askyesno("No session", "No workout session is active. Start one now?"):
                self._start_session()
            else:
                return

        exercise_name = self.exercise_var.get().strip()
        if not exercise_name:
            messagebox.showerror("Missing exercise", "Please select an exercise.")
            return

        try:
            sets = int(self.sets_entry.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Sets must be a whole number.")
            return

        reps_raw = self.reps_entry.get().strip()
        try:
            reps_list = parse_reps(reps_raw, sets)
        except ValueError as exc:
            messagebox.showerror("Invalid reps", str(exc))
            return

        try:
            weight = float(self.weight_entry.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Weight must be a number.")
            return

        try:
            entry = log_workout_entry(
                user=user,
                date=dt.date.today().isoformat(),
                exercise_name=exercise_name,
                sets=sets,
                reps_input=reps_raw,
                weight_kg=weight,
                notes=self.notes_entry.get().strip(),
                session_id=self.app.current_session_id,
            )
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        xp_gain = calculate_xp(sets)
        add_xp(user, xp_gain)
        update_leaderboard(user)
        save_profile(user)

        pr = get_personal_record(user, entry["exercise"])
        pr_value = pr["estimated_1rm"] if pr else entry["estimated_1rm"]

        # Mark exercise as logged in plan list
        for i in range(self.plan_ex_list.size()):
            if self.plan_ex_list.get(i).lstrip("✓ ") == exercise_name:
                self.plan_ex_list.delete(i)
                self.plan_ex_list.insert(i, f"✓ {exercise_name}")
                break

        self._clear_form()
        self.refresh()

        reps_display = entry["reps"]
        messagebox.showinfo(
            "Exercise saved",
            (
                f"{entry['exercise']} — {entry['date']}\n"
                f"Sets: {entry['sets']}  Reps: {reps_display}  Weight: {weight} kg\n"
                f"Volume: {entry['volume_kg']} kg\n"
                f"Estimated 1RM: {entry['estimated_1rm']} kg  (PR: {pr_value} kg)\n"
                f"XP gained: +{xp_gain}"
            ),
        )

    # ── Form check ────────────────────────────────────────────────────

    def _run_form_check(self) -> None:
        exercise_name = self.exercise_var.get().strip() or "Exercise"
        result = run_form_check_session(exercise_name, duration_seconds=60)
        if not result.get("success"):
            messagebox.showwarning("Form Check", result.get("message", "Form check failed."))
            return
        engine = result.get("engine", "OpenCV")
        tips = "\n• ".join(result.get("tips", []))
        messagebox.showinfo(
            "Form Check Result",
            (
                f"Exercise: {result.get('exercise', exercise_name)}\n"
                f"Engine: {engine}\n"
                f"\nOverall score: {result['score']}/100\n"
                f"Range of motion: {result.get('rom_score', 0)}/100\n"
                f"Consistency:     {result.get('consistency_score', 0)}/100\n"
                f"Stability:       {result.get('stability_score', 0)}/100\n"
                f"\nReps detected: {result.get('rep_count', 0)}\n"
                f"\nFeedback:\n• {tips}"
            ),
        )

    # ── Refresh ───────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._update_session_ui()
        self._reload_plans()

        user = self.app.current_user
        if user is None:
            self.summary_var.set("Please log in to track workouts.")
            self.recent_tree.delete(*self.recent_tree.get_children())
            return

        summary = get_training_summary(user)
        if summary["total_sessions"] == 0:
            self.summary_var.set("No workouts logged yet.")
        else:
            self.summary_var.set("\n".join([
                f"Sessions:         {summary['total_sessions']}",
                f"Total sets:       {summary['total_sets']}",
                f"Total reps:       {summary['total_reps']}",
                f"Total volume:     {summary['total_volume_kg']} kg",
                f"Unique exercises: {summary['unique_exercises']}",
                f"Most logged:      {summary['most_logged_exercise'] or 'N/A'}",
            ]))

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
