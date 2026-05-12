"""Main Tkinter app window with frame navigation."""

import tkinter as tk
from tkinter import ttk

from app.gui.dashboard_frame import DashboardFrame
from app.gui.leaderboard_frame import LeaderboardFrame
from app.gui.login_frame import LoginFrame
from app.gui.plan_frame import PlanFrame
from app.gui.progress_frame import ProgressFrame
from app.gui.workout_frame import WorkoutFrame

_NAV_ITEMS = [
    ("Dashboard", DashboardFrame),
    ("Workout", WorkoutFrame),
    ("Plans", PlanFrame),
    ("Progress", ProgressFrame),
    ("Leaderboard", LeaderboardFrame),
]


class FitTrackApp(tk.Tk):
    """Root Tkinter window for FitTrack."""

    def __init__(self) -> None:
        super().__init__()
        self.title("FitTrack")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.current_user = None
        self.current_frame = None

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────
        self.sidebar = ttk.Frame(self, padding=12)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        ttk.Label(self.sidebar, text="FitTrack", font=("Segoe UI", 14, "bold")).pack(pady=(0, 12))

        # Login/Register button (always visible)
        ttk.Button(
            self.sidebar, text="Login / Register",
            command=lambda: self.show_frame(LoginFrame), width=20,
        ).pack(fill="x", pady=4)

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=6)

        # Protected nav buttons (disabled until logged in)
        self._nav_buttons: list[ttk.Button] = []
        for title, frame_cls in _NAV_ITEMS:
            btn = ttk.Button(
                self.sidebar, text=title,
                command=lambda cls=frame_cls: self.show_frame(cls),
                width=20,
            )
            btn.pack(fill="x", pady=4)
            btn.state(["disabled"])
            self._nav_buttons.append(btn)

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", pady=6)

        self.logout_btn = ttk.Button(
            self.sidebar, text="Logout", command=self._logout, width=20, state="disabled",
        )
        self.logout_btn.pack(fill="x", pady=4)

        # ── Content area ──────────────────────────────────────────────
        self.content = ttk.Frame(self, padding=12)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        self.show_frame(LoginFrame)

    # ── Navigation ────────────────────────────────────────────────────

    def show_frame(self, frame_cls: type[ttk.Frame]) -> None:
        """Swap the active content frame."""
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_cls(self.content, self)
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        refresh = getattr(self.current_frame, "refresh", None)
        if callable(refresh):
            refresh()

    def on_login(self) -> None:
        """Enable nav buttons after successful login."""
        for btn in self._nav_buttons:
            btn.state(["!disabled"])
        self.logout_btn.state(["!disabled"])

    def _logout(self) -> None:
        self.current_user = None
        for btn in self._nav_buttons:
            btn.state(["disabled"])
        self.logout_btn.state(["disabled"])
        self.show_frame(LoginFrame)
