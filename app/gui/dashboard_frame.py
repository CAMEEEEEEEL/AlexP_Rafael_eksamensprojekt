"""Dashboard frame showing user stats and recent activity."""

import tkinter as tk
from tkinter import messagebox, ttk

from app.auth import save_profile
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

        ttk.Button(left, text="Edit Profile", command=self._open_edit_dialog).pack(anchor="w", pady=(8, 0))

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

    # ── Edit Profile dialog ───────────────────────────────────────────

    def _open_edit_dialog(self) -> None:
        """Open a modal dialog to edit profile fields."""
        user = self.app.current_user
        if user is None:
            messagebox.showwarning("Not logged in", "Please log in first.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("Edit Profile")
        dlg.resizable(False, False)
        dlg.grab_set()           # modal

        # Centre over parent window
        dlg.geometry("320x300")
        dlg.update_idletasks()
        px = self.winfo_rootx() + (self.winfo_width()  - dlg.winfo_width())  // 2
        py = self.winfo_rooty() + (self.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{px}+{py}")

        pad = {"padx": 12, "pady": 4}

        # Age
        ttk.Label(dlg, text="Age").grid(row=0, column=0, sticky="w", **pad)
        age_var = tk.StringVar(value=str(user.age or ""))
        ttk.Entry(dlg, textvariable=age_var, width=20).grid(row=0, column=1, sticky="ew", **pad)

        # Weight
        ttk.Label(dlg, text="Weight (kg)").grid(row=1, column=0, sticky="w", **pad)
        weight_var = tk.StringVar(value=str(user.weight_kg or ""))
        ttk.Entry(dlg, textvariable=weight_var, width=20).grid(row=1, column=1, sticky="ew", **pad)

        # Height
        ttk.Label(dlg, text="Height (cm)").grid(row=2, column=0, sticky="w", **pad)
        height_var = tk.StringVar(value=str(user.height_cm or ""))
        ttk.Entry(dlg, textvariable=height_var, width=20).grid(row=2, column=1, sticky="ew", **pad)

        # Goals
        ttk.Label(dlg, text="Goal").grid(row=3, column=0, sticky="w", **pad)
        goals_var = tk.StringVar(value=user.goals or "Maintain Weight")
        ttk.Combobox(
            dlg, textvariable=goals_var,
            values=["Lose Weight", "Maintain Weight", "Gain Weight"],
            state="readonly", width=18,
        ).grid(row=3, column=1, sticky="ew", **pad)

        dlg.columnconfigure(1, weight=1)

        def _save() -> None:
            try:
                new_age    = int(age_var.get().strip() or 0)
                new_weight = float(weight_var.get().strip() or 0)
                new_height = float(height_var.get().strip() or 0)
            except ValueError:
                messagebox.showerror("Invalid input",
                                     "Age must be a whole number; weight and height must be numbers.",
                                     parent=dlg)
                return
            user.age       = new_age
            user.weight_kg = new_weight
            user.height_cm = new_height
            user.goals     = goals_var.get()
            save_profile(user)
            messagebox.showinfo("Saved", "Profile updated successfully!", parent=dlg)
            dlg.destroy()
            self.refresh()

        btn_row = ttk.Frame(dlg)
        btn_row.grid(row=4, column=0, columnspan=2, pady=12)
        ttk.Button(btn_row, text="Save",   command=_save).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancel", command=dlg.destroy).pack(side="left", padx=6)

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
