"""Progression graph frame with plateau warning."""

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.progression import detect_plateau, get_progression, get_suggestions


class ProgressFrame(ttk.Frame):
    """Frame that plots progression over time for selected exercise."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        """Initialize widgets and embedded Matplotlib chart."""
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Progression Analysis", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=8)

        self.exercise_var = tk.StringVar()
        self.plateau_var = tk.StringVar(value="")

        controls = ttk.Frame(self)
        controls.pack(fill="x")
        ttk.Label(controls, text="Exercise").pack(side="left")
        self.exercise_box = ttk.Combobox(controls, textvariable=self.exercise_var, state="readonly", width=30)
        self.exercise_box.pack(side="left", padx=6)
        ttk.Button(controls, text="Plot", command=self._plot_progress).pack(side="left")

        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Estimated 1RM Progress")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Estimated 1RM (kg)")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=8)

        ttk.Label(self, textvariable=self.plateau_var, foreground="tomato").pack(anchor="w")

    def refresh(self) -> None:
        """Refresh exercise options based on the current user's workout log."""
        user = self.app.current_user
        if user is None:
            self.exercise_box["values"] = []
            self.exercise_var.set("")
            self.plateau_var.set("Please log in to view progression.")
            self._clear_plot()
            return

        exercises = sorted({entry.get("exercise", "") for entry in user.workout_log if entry.get("exercise")})
        self.exercise_box["values"] = exercises
        if exercises and self.exercise_var.get() not in exercises:
            self.exercise_var.set(exercises[0])
        self.plateau_var.set("")
        self._clear_plot()

    def _clear_plot(self) -> None:
        """Reset plot to an empty state."""
        self.ax.clear()
        self.ax.set_title("Estimated 1RM Progress")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Estimated 1RM (kg)")
        self.canvas.draw()

    def _plot_progress(self) -> None:
        """Plot progression data and display plateau warnings/suggestions."""
        user = self.app.current_user
        exercise = self.exercise_var.get().strip()
        if user is None or not exercise:
            return

        progression = get_progression(exercise, user.workout_log)
        if not progression:
            self.plateau_var.set("No data for selected exercise.")
            self._clear_plot()
            return

        dates = [item[0] for item in progression]
        values = [item[1] for item in progression]

        self.ax.clear()
        self.ax.plot(dates, values, marker="o")
        self.ax.set_title(f"{exercise} Estimated 1RM")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Estimated 1RM (kg)")
        self.ax.tick_params(axis="x", rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

        if detect_plateau(progression):
            tips = " | ".join(get_suggestions()[:2])
            self.plateau_var.set(f"Plateau detected. Suggestions: {tips}")
        else:
            self.plateau_var.set("No plateau detected.")
