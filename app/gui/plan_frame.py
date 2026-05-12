"""Workout plan builder frame."""

import tkinter as tk
from tkinter import messagebox, ttk

from app.exercises import get_exercise_names, get_muscle_groups
from app.plan import (
    REST_MARKER,
    WEEK_DAYS,
    add_exercise_to_day,
    create_plan,
    delete_plan,
    is_rest_day,
    load_plans,
    move_exercise,
    remove_exercise_from_day,
    set_rest_day,
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
        plan_row.pack(fill="x", pady=(0, 6))

        ttk.Label(plan_row, text="Plan name:").pack(side="left")
        self.plan_name_entry = ttk.Entry(plan_row, width=22)
        self.plan_name_entry.pack(side="left", padx=4)
        self.plan_name_entry.bind("<Return>", lambda _e: self._create_plan())
        ttk.Button(plan_row, text="Create Plan", command=self._create_plan).pack(side="left", padx=(0, 6))
        ttk.Button(plan_row, text="Delete Plan", command=self._delete_plan).pack(side="left", padx=(0, 20))

        ttk.Label(plan_row, text="Select plan:").pack(side="left")
        self.plan_selector = ttk.Combobox(plan_row, state="readonly", width=24)
        self.plan_selector.pack(side="left", padx=4)
        self.plan_selector.bind("<<ComboboxSelected>>", self._on_plan_selected)

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=6)

        # ── Three-column body ─────────────────────────────────────────
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        # ── Column 1: Day selector (Mon–Sun) ──────────────────────────
        days_col = ttk.Frame(body)
        days_col.pack(side="left", fill="y", padx=(0, 10))

        ttk.Label(days_col, text="Days", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))

        self.days_list = tk.Listbox(
            days_col, width=22, height=7, selectmode="single",
            font=("Segoe UI", 10), activestyle="none",
        )
        self.days_list.pack(fill="y")
        self.days_list.bind("<<ListboxSelect>>", self._on_day_selected)

        rest_btn = ttk.Button(days_col, text="Toggle Rest Day", command=self._toggle_rest_day)
        rest_btn.pack(fill="x", pady=(6, 0))

        # ── Column 2: Exercises ───────────────────────────────────────
        ex_col = ttk.Frame(body)
        ex_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ttk.Label(ex_col, text="Exercises", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))

        # Muscle filter + exercise picker
        picker_row = ttk.Frame(ex_col)
        picker_row.pack(fill="x", pady=(0, 4))

        ttk.Label(picker_row, text="Muscle:").grid(row=0, column=0, sticky="w")
        self.muscle_var = tk.StringVar(value=_ALL)
        muscle_box = ttk.Combobox(
            picker_row, textvariable=self.muscle_var,
            values=[_ALL] + get_muscle_groups(), state="readonly", width=13,
        )
        muscle_box.grid(row=0, column=1, sticky="w", padx=(4, 12))
        muscle_box.bind("<<ComboboxSelected>>", self._on_muscle_changed)

        ttk.Label(picker_row, text="Exercise:").grid(row=0, column=2, sticky="w")
        self.exercise_var = tk.StringVar()
        self.exercise_box = ttk.Combobox(picker_row, textvariable=self.exercise_var, width=22)
        self.exercise_box.grid(row=0, column=3, sticky="w", padx=4)
        self.exercise_box.bind("<KeyRelease>", self._on_exercise_typed)
        self.exercise_box.bind("<Return>", lambda _e: self._add_exercise())
        self._reload_exercise_list()

        ttk.Button(picker_row, text="Add", command=self._add_exercise).grid(row=0, column=4, padx=(4, 0))

        # Exercise listbox + up/down/remove buttons
        ex_body = ttk.Frame(ex_col)
        ex_body.pack(fill="both", expand=True)

        self.exercise_list = tk.Listbox(ex_body, height=12, selectmode="single", font=("Segoe UI", 10))
        ex_scroll = ttk.Scrollbar(ex_body, orient="vertical", command=self.exercise_list.yview)
        self.exercise_list.configure(yscrollcommand=ex_scroll.set)
        self.exercise_list.pack(side="left", fill="both", expand=True)
        ex_scroll.pack(side="left", fill="y")

        btn_col = ttk.Frame(ex_body)
        btn_col.pack(side="left", fill="y", padx=(6, 0))
        ttk.Button(btn_col, text="▲ Up",     command=self._move_up,         width=10).pack(pady=(0, 4))
        ttk.Button(btn_col, text="▼ Down",   command=self._move_down,       width=10).pack(pady=(0, 12))
        ttk.Button(btn_col, text="✕ Remove", command=self._remove_exercise, width=10).pack()

        # ── Column 3: Plan overview ───────────────────────────────────
        ov_col = ttk.Frame(body)
        ov_col.pack(side="left", fill="both", expand=True)

        ttk.Label(ov_col, text="Plan Overview", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))
        self.overview_text = tk.Text(ov_col, width=26, state="disabled", wrap="word", relief="flat",
                                     font=("Segoe UI", 9))
        ov_scroll = ttk.Scrollbar(ov_col, orient="vertical", command=self.overview_text.yview)
        self.overview_text.configure(yscrollcommand=ov_scroll.set)
        self.overview_text.pack(side="left", fill="both", expand=True)
        ov_scroll.pack(side="left", fill="y")

    # ── Exercise picker helpers ───────────────────────────────────────

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
        if not sel:
            return ""
        # Strip the indicator suffix to get the plain day name
        return self.days_list.get(sel[0]).split("  ")[0].strip()

    def _selected_exercise_index(self) -> int | None:
        sel = self.exercise_list.curselection()
        return sel[0] if sel else None

    # ── Plan actions ──────────────────────────────────────────────────

    def _create_plan(self) -> None:
        user = self.app.current_user
        if user is None:
            messagebox.showwarning("Not logged in", "Please log in before creating plans.")
            return
        name = self.plan_name_entry.get().strip()
        if not name:
            messagebox.showerror("Invalid plan", "Plan name is required.")
            return
        try:
            create_plan(user.username, name)
        except ValueError as exc:
            messagebox.showerror("Invalid plan", str(exc))
            return
        self.plan_name_entry.delete(0, "end")
        self.refresh()
        self.plan_selector.set(name)
        self._load_days()
        self._refresh_overview()

    def _delete_plan(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        if user is None or not plan_name:
            return
        if not messagebox.askyesno("Delete plan", f"Delete '{plan_name}'?"):
            return
        delete_plan(user.username, plan_name)
        self.refresh()

    def _toggle_rest_day(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            messagebox.showwarning("No day selected", "Select a day first.")
            return
        plans = load_plans(user.username)
        exercises = plans.get(plan_name, {}).get(day_name, [])
        currently_rest = is_rest_day(exercises)
        set_rest_day(user.username, plan_name, day_name, rest=not currently_rest)
        self._load_days(keep_selection=day_name)
        self._load_exercises()
        self._refresh_overview()

    def _add_exercise(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            messagebox.showwarning("No day selected", "Select a plan and day first.")
            return
        name = self.exercise_var.get().strip()
        if not name:
            messagebox.showerror("Missing exercise", "Type or select an exercise.")
            return
        try:
            add_exercise_to_day(user.username, plan_name, day_name, name)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.exercise_var.set("")
        self._load_exercises()
        self._load_days(keep_selection=day_name)
        self._refresh_overview()

    def _remove_exercise(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        idx = self._selected_exercise_index()
        if user is None or not plan_name or not day_name or idx is None:
            return
        remove_exercise_from_day(user.username, plan_name, day_name, idx)
        self._load_exercises()
        self._load_days(keep_selection=day_name)
        self._refresh_overview()

    def _move_up(self) -> None:
        self._move_exercise(-1)

    def _move_down(self) -> None:
        self._move_exercise(1)

    def _move_exercise(self, direction: int) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        idx = self._selected_exercise_index()
        if user is None or not plan_name or not day_name or idx is None:
            return
        new_idx = move_exercise(user.username, plan_name, day_name, idx, direction)
        self._load_exercises()
        # Re-select the moved item
        self.exercise_list.selection_set(new_idx)
        self.exercise_list.see(new_idx)
        self._refresh_overview()

    # ── Load helpers ──────────────────────────────────────────────────

    def _load_days(self, keep_selection: str = "") -> None:
        """Reload the Mon–Sun day listbox, keeping or auto-selecting a day."""
        self.days_list.delete(0, "end")
        user = self.app.current_user
        plan_name = self._selected_plan()
        if user is None or not plan_name:
            return

        plans = load_plans(user.username)
        day_data = plans.get(plan_name, {})

        select_idx = 0
        for i, day in enumerate(WEEK_DAYS):
            exercises = day_data.get(day, [])
            if is_rest_day(exercises):
                label = f"{day}  — REST"
            elif exercises:
                label = f"{day}  ({len(exercises)} exercise{'s' if len(exercises) != 1 else ''})"
            else:
                label = f"{day}  (empty)"
            self.days_list.insert("end", label)
            if day == keep_selection:
                select_idx = i

        self.days_list.selection_set(select_idx)
        self.days_list.see(select_idx)
        self._load_exercises()

    def _load_exercises(self) -> None:
        """Reload exercises for the currently selected day."""
        self.exercise_list.delete(0, "end")
        user = self.app.current_user
        plan_name = self._selected_plan()
        day_name = self._selected_day()
        if user is None or not plan_name or not day_name:
            return

        plans = load_plans(user.username)
        exercises = plans.get(plan_name, {}).get(day_name, [])

        if is_rest_day(exercises):
            self.exercise_list.insert("end", "🛌  Rest Day")
        else:
            for ex in exercises:
                self.exercise_list.insert("end", ex)

    def _refresh_overview(self) -> None:
        user = self.app.current_user
        plan_name = self._selected_plan()
        self.overview_text.configure(state="normal")
        self.overview_text.delete("1.0", "end")
        if user is None or not plan_name:
            self.overview_text.configure(state="disabled")
            return

        plans = load_plans(user.username)
        day_data = plans.get(plan_name, {})
        self.overview_text.insert("end", f"{plan_name}\n{'─' * 22}\n")
        for day in WEEK_DAYS:
            exercises = day_data.get(day, [])
            if is_rest_day(exercises):
                self.overview_text.insert("end", f"\n{day}:\n  REST\n")
            elif exercises:
                self.overview_text.insert("end", f"\n{day}:\n")
                for ex in exercises:
                    self.overview_text.insert("end", f"  • {ex}\n")
            else:
                self.overview_text.insert("end", f"\n{day}:\n  (empty)\n")
        self.overview_text.configure(state="disabled")

    # ── Event handlers ────────────────────────────────────────────────

    def _on_plan_selected(self, _event: tk.Event | None = None) -> None:
        self._load_days()
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
        self._load_days()
        self._refresh_overview()
