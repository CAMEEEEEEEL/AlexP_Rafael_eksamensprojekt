"""Workout plan builder frame."""

import tkinter as tk
from tkinter import messagebox, ttk

from app.exercises import get_exercise_names, get_muscle_groups
from app.plan import (
    add_exercise_to_day,
    add_plan_day,
    create_plan,
    delete_plan,
    load_plans,
    remove_exercise_from_day,
    remove_plan_day,
)

_ALL = "All"


class PlanFrame(ttk.Frame):
    """Frame for creating and managing workout split plans."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Workout Plans", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 4))

        # ── Plan management row ───────────────────────────────────────
        plan_row = ttk.Frame(self)
        plan_row.pack(fill="x", pady=(0, 4))

        ttk.Label(plan_row, text="Plan name:").pack(side="left")
        self.plan_name_entry = ttk.Entry(plan_row, width=22)
        self.plan_name_entry.pack(side="left", padx=4)
        self.plan_name_entry.bind("<Return>", lambda _e: self._create_plan())

        ttk.Button(plan_row, text="Create Plan", command=self._create_plan).pack(side="left", padx=(0, 4))
        ttk.Button(plan_row, text="Delete Plan", command=self._delete_plan).pack(side="left", padx=(0, 16))

        ttk.Label(plan_row, text="Select plan:").pack(side="left")
        self.plan_selector = ttk.Combobox(plan_row, state="readonly", width=24)
        self.plan_selector.pack(side="left", padx=4)
        self.plan_selector.bind("<<ComboboxSelected>>", self._on_plan_selected)

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=6)

        # ── Three-column body ─────────────────────────────────────────
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        # Column 1: Days
        days_col = ttk.Frame(body)
        days_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ttk.Label(days_col, text="Days", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        day_input_row = ttk.Frame(days_col)
        day_input_row.pack(fill="x", pady=(4, 2))
        ttk.Label(day_input_row, text="Day name:").pack(side="left")
        self.day_name_entry = ttk.Entry(day_input_row, width=14)
        self.day_name_entry.pack(side="left", padx=4)
        self.day_name_entry.bind("<Return>", lambda _e: self._add_day())

        day_btn_row = ttk.Frame(days_col)
        day_btn_row.pack(fill="x", pady=(0, 4))
        ttk.Button(day_btn_row, text="Add Day", command=self._add_day).pack(side="left", padx=(0, 4))
        ttk.Button(day_btn_row, text="Remove Day", command=self._remove_day).pack(side="left")

        self.days_list = tk.Listbox(days_col, height=12, selectmode="single")
        days_scroll = ttk.Scrollbar(days_col, orient="vertical", command=self.days_list.yview)
        self.days_list.configure(yscrollcommand=days_scroll.set)
        self.days_list.pack(side="left", fill="both", expand=True)
        days_scroll.pack(side="left", fill="y")
        self.days_list.bind("<<ListboxSelect>>", self._on_day_selected)

        # Column 2: Exercises in selected day
        ex_col = ttk.Frame(body)
        ex_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ttk.Label(ex_col, text="Exercises in Day", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        # Muscle group filter + exercise picker
        muscle_row = ttk.Frame(ex_col)
        muscle_row.pack(fill="x", pady=(4, 2))
        ttk.Label(muscle_row, text="Muscle:").pack(side="left")
        self.muscle_var = tk.StringVar(value=_ALL)
        muscle_box = ttk.Combobox(
            muscle_row, textvariable=self.muscle_var,
            values=[_ALL] + get_muscle_groups(), state="readonly", width=12,
        )
        muscle_box.pack(side="left", padx=4)
        muscle_box.bind("<<ComboboxSelected>>", self._on_muscle_changed)

        ex_input_row = ttk.Frame(ex_col)
        ex_input_row.pack(fill="x", pady=(2, 2))
        ttk.Label(ex_input_row, text="Exercise:").pack(side="left")
        self.exercise_var = tk.StringVar()
        self.exercise_box = ttk.Combobox(ex_input_row, textvariable=self.exercise_var, width=20)
        self.exercise_box.pack(side="left", padx=4)
        self.exercise_box.bind("<KeyRelease>", self._on_exercise_typed)
        self._reload_exercise_list()

        ex_btn_row = ttk.Frame(ex_col)
        ex_btn_row.pack(fill="x", pady=(0, 4))
        ttk.Button(ex_btn_row, text="Add Exercise", command=self._add_exercise).pack(side="left", padx=(0, 4))
        ttk.Button(ex_btn_row, text="Remove Exercise", command=self._remove_exercise).pack(side="left")
        self.exercise_box.bind("<Return>", lambda _e: self._add_exercise())

        self.exercise_list = tk.Listbox(ex_col, height=12, selectmode="single")
        ex_scroll = ttk.Scrollbar(ex_col, orient="vertical", command=self.exercise_list.yview)
        self.exercise_list.configure(yscrollcommand=ex_scroll.set)
        self.exercise_list.pack(side="left", fill="both", expand=True)
        ex_scroll.pack(side="left", fill="y")

        # Column 3: Plan overview
        overview_col = ttk.Frame(body)
        overview_col.pack(side="left", fill="both", expand=True)

        ttk.Label(overview_col, text="Plan Overview", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.overview_text = tk.Text(overview_col, width=28, state="disabled", wrap="word", relief="flat")
        ov_scroll = ttk.Scrollbar(overview_col, orient="vertical", command=self.overview_text.yview)
        self.overview_text.configure(yscrollcommand=ov_scroll.set)
        self.overview_text.pack(side="left", fill="both", expand=True, pady=(8, 0))
        ov_scroll.pack(side="left", fill="y", pady=(8, 0))

    # ── Exercise list helpers ─────────────────────────────────────────

    def _reload_exercise_list(self, filter_text: str = "") -> None:
        muscle = self.muscle_var.get()
        names = get_exercise_names(muscle if muscle != _ALL else "")
        if filter_text:
            names = [n for n in names if filter_text.lower() in n.lower()]
        self.exercise_box["values"] = names

    def _on_muscle_changed(self, _event: tk.Event | None = None) -> None:
        self._reload_exercise_list()
        self.exercise_var.set("")

    def _on_exercise_typed(self, _event: tk.Event | None = None) -> None:
        self._reload_exercise_list(filter_text=self.exercise_var.get())

    # ── Selection helpers ─────────────────────────────────────────────

    def _selected_plan(self) -> str:
        return self.plan_selector.get().strip()

    def _selected_day(self) -> str:
        sel = self.days_list.curselection()
        return self.days_list.get(sel[0]) if sel else ""

    # ── Plan actions ──────────────────────────────────────────────────

    def _create_plan(self) -> None:
        user = self.app.current_user
        if user is None:
            messagebox.showwarning("Not logged in", "Please log in before creating plans.")
            return
        try:
            create_plan(user.username, self.plan_name_entry.get())
        except ValueError as exc:
            messagebox.showerror("Invalid plan", str(exc))
            return
        self.plan_name_entry.delete(0, "end")
        self.refresh()

    def _delete_plan(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        if user is None or not plan_name:
            return
        if not messagebox.askyesno("Delete plan", f"Delete plan '{plan_name}'?"):
            return
        delete_plan(user.username, plan_name)
        self.refresh()

    def _add_day(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        if user is None or not plan_name:
            messagebox.showwarning("No plan selected", "Select a plan first.")
            return
        try:
            add_plan_day(user.username, plan_name, self.day_name_entry.get())
        except ValueError as exc:
            messagebox.showerror("Invalid day", str(exc))
            return
        self.day_name_entry.delete(0, "end")
        self._load_days()
        self._refresh_overview()

    def _remove_day(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            return
        remove_plan_day(user.username, plan_name, day_name)
        self._load_days()
        self.exercise_list.delete(0, "end")
        self._refresh_overview()

    def _add_exercise(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            messagebox.showwarning("No day selected", "Select a plan and day first.")
            return
        try:
            add_exercise_to_day(user.username, plan_name, day_name, self.exercise_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid exercise", str(exc))
            return
        self.exercise_var.set("")
        self._load_exercises()
        self._refresh_overview()

    def _remove_exercise(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        sel = self.exercise_list.curselection()
        if user is None or not plan_name or not day_name or not sel:
            return
        remove_exercise_from_day(user.username, plan_name, day_name, sel[0])
        self._load_exercises()
        self._refresh_overview()

    # ── Load helpers ──────────────────────────────────────────────────

    def _load_days(self, auto_select_first: bool = True) -> None:
        """Reload the days listbox for the selected plan."""
        self.days_list.delete(0, "end")
        user = self.app.current_user
        plan_name = self._selected_plan()
        if user is None or not plan_name:
            return
        plans = load_plans(user.username)
        for day_name in plans.get(plan_name, {}).keys():
            self.days_list.insert("end", day_name)
        # Auto-select first day so exercises populate immediately
        if auto_select_first and self.days_list.size() > 0:
            self.days_list.selection_set(0)
            self.days_list.activate(0)
        self._load_exercises()

    def _load_exercises(self) -> None:
        """Reload the exercises listbox for the selected day."""
        self.exercise_list.delete(0, "end")
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            return
        plans = load_plans(user.username)
        for exercise in plans.get(plan_name, {}).get(day_name, []):
            self.exercise_list.insert("end", exercise)

    def _refresh_overview(self) -> None:
        """Rebuild the plan overview text panel."""
        user = self.app.current_user
        plan_name = self._selected_plan()
        self.overview_text.configure(state="normal")
        self.overview_text.delete("1.0", "end")
        if user is None or not plan_name:
            self.overview_text.configure(state="disabled")
            return
        plans = load_plans(user.username)
        days = plans.get(plan_name, {})
        self.overview_text.insert("end", f"{plan_name}\n{'─' * 24}\n")
        for day, exercises in days.items():
            self.overview_text.insert("end", f"\n{day}:\n")
            if exercises:
                for ex in exercises:
                    self.overview_text.insert("end", f"  • {ex}\n")
            else:
                self.overview_text.insert("end", "  (no exercises)\n")
        self.overview_text.configure(state="disabled")

    # ── Event handlers ────────────────────────────────────────────────

    def _on_plan_selected(self, _event: tk.Event | None = None) -> None:
        self._load_days(auto_select_first=True)
        self._refresh_overview()

    def _on_day_selected(self, _event: tk.Event | None = None) -> None:
        self._load_exercises()

    # ── Refresh ───────────────────────────────────────────────────────

    def refresh(self) -> None:
        user = self.app.current_user
        if user is None:
            self.plan_selector["values"] = []
            self.plan_selector.set("")
            self.days_list.delete(0, "end")
            self.exercise_list.delete(0, "end")
            self.overview_text.configure(state="normal")
            self.overview_text.delete("1.0", "end")
            self.overview_text.configure(state="disabled")
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
        self._load_days(auto_select_first=True)
        self._refresh_overview()
