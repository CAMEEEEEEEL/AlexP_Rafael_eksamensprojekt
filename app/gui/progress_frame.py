"""Progression graph frame with plateau warning and multi-chart support."""

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.progression import detect_plateau, get_progression, get_suggestions
from app.workout import get_exercise_history

_CHART_TYPES = ["Estimated 1RM", "Total Volume (kg)", "Weight Lifted (kg)"]


class ProgressFrame(ttk.Frame):
    """Frame that plots progression over time for a selected exercise."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Progression Analysis", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 4))

        # ── Controls row ──────────────────────────────────────────────
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 6))

        ttk.Label(controls, text="Exercise:").pack(side="left")
        self.exercise_var = tk.StringVar()
        self.exercise_box = ttk.Combobox(
            controls, textvariable=self.exercise_var, state="readonly", width=28,
        )
        self.exercise_box.pack(side="left", padx=(4, 12))

        ttk.Label(controls, text="Chart:").pack(side="left")
        self.chart_var = tk.StringVar(value=_CHART_TYPES[0])
        chart_box = ttk.Combobox(
            controls, textvariable=self.chart_var, values=_CHART_TYPES, state="readonly", width=22,
        )
        chart_box.pack(side="left", padx=(4, 12))

        ttk.Button(controls, text="Plot", command=self._plot_progress).pack(side="left")

        # ── Matplotlib chart ──────────────────────────────────────────
        self.figure = Figure(figsize=(7, 3.8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=4)

        # ── Status / plateau message ──────────────────────────────────
        self.plateau_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.plateau_var, foreground="tomato").pack(anchor="w")

        # ── Stats summary panel ───────────────────────────────────────
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=4)
        self.stats_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.stats_var, justify="left", font=("Segoe UI", 9)).pack(anchor="w")

        self._clear_plot("Select an exercise and click Plot.")

    # ── Helpers ───────────────────────────────────────────────────────

    def _clear_plot(self, msg: str = "") -> None:
        self.ax.clear()
        if msg:
            self.ax.text(0.5, 0.5, msg, ha="center", va="center", transform=self.ax.transAxes,
                         color="grey", fontsize=11)
        self.ax.set_xlabel("Date")
        self.figure.tight_layout()
        self.canvas.draw()

    def _build_series(self, exercise: str) -> tuple[list[str], list[float], str]:
        """Return (dates, values, y_label) for the chosen chart type."""
        user = self.app.current_user
        chart = self.chart_var.get()

        if chart == "Estimated 1RM":
            progression = get_progression(exercise, user.workout_log)
            dates = [p[0] for p in progression]
            values = [p[1] for p in progression]
            return dates, values, "Estimated 1RM (kg)"

        history = get_exercise_history(user, exercise)
        dates = [e.get("date", "") for e in history]

        if chart == "Total Volume (kg)":
            values = [float(e.get("volume_kg", 0)) for e in history]
            return dates, values, "Volume (kg)"

        # Weight Lifted
        values = [float(e.get("weight_kg", 0)) for e in history]
        return dates, values, "Weight (kg)"

    def _build_stats_text(self, exercise: str, dates: list[str], values: list[float]) -> str:
        if not values:
            return ""
        chart = self.chart_var.get()
        best = max(values)
        best_date = dates[values.index(best)] if dates else "—"
        recent = values[-1] if values else 0
        first = values[0] if values else 0
        delta = round(recent - first, 2)
        sign = "+" if delta >= 0 else ""
        return (
            f"Sessions tracked: {len(values)}  |  "
            f"Best {chart}: {best} kg (on {best_date})  |  "
            f"Change (first → latest): {sign}{delta} kg"
        )

    # ── Refresh / Plot ────────────────────────────────────────────────

    def refresh(self) -> None:
        user = self.app.current_user
        if user is None:
            self.exercise_box["values"] = []
            self.exercise_var.set("")
            self.plateau_var.set("Please log in to view progression.")
            self.stats_var.set("")
            self._clear_plot()
            return

        exercises = sorted({e.get("exercise", "") for e in user.workout_log if e.get("exercise")})
        self.exercise_box["values"] = exercises
        if exercises and self.exercise_var.get() not in exercises:
            self.exercise_var.set(exercises[0])
        self.plateau_var.set("")
        self.stats_var.set("")
        self._clear_plot("Select an exercise and click Plot.")

    def _plot_progress(self) -> None:
        user = self.app.current_user
        exercise = self.exercise_var.get().strip()
        if user is None or not exercise:
            return

        dates, values, y_label = self._build_series(exercise)

        if not values:
            self.plateau_var.set("No data for selected exercise.")
            self._clear_plot("No data yet.")
            self.stats_var.set("")
            return

        self.ax.clear()
        self.ax.plot(dates, values, marker="o", linewidth=2, color="#4C9BE8")
        self.ax.fill_between(range(len(values)), values, alpha=0.12, color="#4C9BE8")
        self.ax.set_xticks(range(len(dates)))
        self.ax.set_xticklabels(dates, rotation=40, ha="right", fontsize=8)
        self.ax.set_title(f"{exercise} — {self.chart_var.get()}", fontsize=11)
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel(y_label)
        self.ax.grid(axis="y", linestyle="--", alpha=0.4)
        self.figure.tight_layout()
        self.canvas.draw()

        # Plateau detection only makes sense for 1RM series
        if self.chart_var.get() == "Estimated 1RM":
            progression = list(zip(dates, values))
            if detect_plateau(progression):
                tips = " | ".join(get_suggestions()[:2])
                self.plateau_var.set(f"Plateau detected. Suggestions: {tips}")
            else:
                self.plateau_var.set("No plateau detected — keep progressing!")
        else:
            self.plateau_var.set("")

        self.stats_var.set(self._build_stats_text(exercise, dates, values))
