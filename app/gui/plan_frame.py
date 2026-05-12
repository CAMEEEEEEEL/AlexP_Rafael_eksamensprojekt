"""Workout plan builder frame."""

import tkinter as tk
from tkinter import messagebox, ttk

from app.plan import (
    add_exercise_to_day,
    add_plan_day,
    create_plan,
    delete_plan,
    load_plans,
    remove_exercise_from_day,
    remove_plan_day,
)


class PlanFrame(ttk.Frame):
    """Frame for creating and managing workout split plans."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        """Initialize plan builder controls."""
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Workout Plans", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=8)

        self.plan_name = ttk.Entry(self)
        self.day_name = ttk.Entry(self)
        self.exercise_name = ttk.Entry(self)
        self.plan_selector = ttk.Combobox(self, state="readonly")
        self.days_list = tk.Listbox(self, height=8)
        self.exercise_list = tk.Listbox(self, height=10)

        ttk.Label(self, text="Plan name (e.g. Push/Pull/Legs)").pack(anchor="w")
        self.plan_name.pack(fill="x", pady=3)
        plan_buttons = ttk.Frame(self)
        plan_buttons.pack(fill="x", pady=4)
        ttk.Button(plan_buttons, text="Create Plan", command=self._create_plan).pack(side="left", padx=(0, 6))
        ttk.Button(plan_buttons, text="Delete Plan", command=self._delete_plan).pack(side="left")

        ttk.Label(self, text="Select plan").pack(anchor="w", pady=(6, 0))
        self.plan_selector.pack(fill="x", pady=3)
        self.plan_selector.bind("<<ComboboxSelected>>", self._on_plan_selected)

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, pady=6)

        left = ttk.Frame(content)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = ttk.Frame(content)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Day name").pack(anchor="w")
        self.day_name.pack(in_=left, fill="x", pady=3)
        day_buttons = ttk.Frame(left)
        day_buttons.pack(fill="x", pady=4)
        ttk.Button(day_buttons, text="Add Day", command=self._add_day).pack(side="left", padx=(0, 6))
        ttk.Button(day_buttons, text="Remove Day", command=self._remove_day).pack(side="left")
        ttk.Label(left, text="Days").pack(anchor="w", pady=(8, 0))
        self.days_list.pack(in_=left, fill="both", expand=True)
        self.days_list.bind("<<ListboxSelect>>", self._on_day_selected)

        ttk.Label(right, text="Exercise").pack(anchor="w")
        self.exercise_name.pack(in_=right, fill="x", pady=3)
        exercise_buttons = ttk.Frame(right)
        exercise_buttons.pack(fill="x", pady=4)
        ttk.Button(exercise_buttons, text="Add Exercise", command=self._add_exercise).pack(side="left", padx=(0, 6))
        ttk.Button(exercise_buttons, text="Remove Exercise", command=self._remove_exercise).pack(side="left")
        ttk.Label(right, text="Exercises").pack(anchor="w", pady=(8, 0))
        self.exercise_list.pack(in_=right, fill="both", expand=True)

    def _selected_plan(self) -> str:
        """Return currently selected plan name."""
        return self.plan_selector.get().strip()

    def _selected_day(self) -> str:
        """Return currently selected day name."""
        selection = self.days_list.curselection()
        if not selection:
            return ""
        return self.days_list.get(selection[0])

    def _create_plan(self) -> None:
        """Create a new workout split plan."""
        user = self.app.current_user
        if user is None:
            messagebox.showwarning("Not logged in", "Please log in before creating plans.")
            return
        try:
            create_plan(user.username, self.plan_name.get())
        except ValueError as exc:
            messagebox.showerror("Invalid plan", str(exc))
            return
        self.plan_name.delete(0, "end")
        messagebox.showinfo("Plan created", "Workout plan created.")
        self.refresh()

    def _delete_plan(self) -> None:
        """Delete selected workout split plan."""
        user = self.app.current_user
        plan_name = self._selected_plan()
        if user is None or not plan_name:
            return
        delete_plan(user.username, plan_name)
        self.refresh()

    def _add_day(self) -> None:
        """Add a training day to the selected plan."""
        user = self.app.current_user
        plan_name = self._selected_plan()
        if user is None or not plan_name:
            messagebox.showwarning("Select plan", "Select a plan first.")
            return
        try:
            add_plan_day(user.username, plan_name, self.day_name.get())
        except ValueError as exc:
            messagebox.showerror("Invalid day", str(exc))
            return
        self.day_name.delete(0, "end")
        self._load_days()

    def _remove_day(self) -> None:
        """Remove selected day from selected plan."""
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            return
        remove_plan_day(user.username, plan_name, day_name)
        self._load_days()
        self.exercise_list.delete(0, "end")

    def _add_exercise(self) -> None:
        """Add exercise to selected plan day."""
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            messagebox.showwarning("Select day", "Select a plan and day first.")
            return
        try:
            add_exercise_to_day(user.username, plan_name, day_name, self.exercise_name.get())
        except ValueError as exc:
            messagebox.showerror("Invalid exercise", str(exc))
            return
        self.exercise_name.delete(0, "end")
        self._load_exercises()

    def _remove_exercise(self) -> None:
        """Remove selected exercise from selected day."""
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        selection = self.exercise_list.curselection()
        if user is None or not plan_name or not day_name or not selection:
            return
        remove_exercise_from_day(user.username, plan_name, day_name, selection[0])
        self._load_exercises()

    def _on_plan_selected(self, _event: tk.Event | None = None) -> None:
        """Refresh day/exercise views when selected plan changes."""
        self._load_days()
        self.exercise_list.delete(0, "end")

    def _on_day_selected(self, _event: tk.Event | None = None) -> None:
        """Refresh exercise list when selected day changes."""
        self._load_exercises()

    def _load_days(self) -> None:
        """Load day list for selected plan."""
        self.days_list.delete(0, "end")
        user = self.app.current_user
        plan_name = self._selected_plan()
        if user is None or not plan_name:
            return
        plans = load_plans(user.username)
        for day_name in plans.get(plan_name, {}).keys():
            self.days_list.insert("end", day_name)

    def _load_exercises(self) -> None:
        """Load exercise list for selected day."""
        self.exercise_list.delete(0, "end")
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            return
        plans = load_plans(user.username)
        for exercise in plans.get(plan_name, {}).get(day_name, []):
            self.exercise_list.insert("end", exercise)

    def refresh(self) -> None:
        """Reload and display current user's saved plans."""
        user = self.app.current_user
        if user is None:
            self.plan_selector["values"] = []
            self.plan_selector.set("")
            self.days_list.delete(0, "end")
            self.exercise_list.delete(0, "end")
            return

        plans = load_plans(user.username)
        plan_names = sorted(plans.keys())
        self.plan_selector["values"] = plan_names
        if not plan_names:
            self.plan_selector.set("")
            self.days_list.delete(0, "end")
            self.exercise_list.delete(0, "end")
            return

        current = self._selected_plan()
        self.plan_selector.set(current if current in plan_names else plan_names[0])
        self._load_days()
        self._load_exercises()