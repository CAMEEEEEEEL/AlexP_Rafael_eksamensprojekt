"""Main Tkinter app window with frame navigation."""

import tkinter as tk
from tkinter import ttk

from app.gui.dashboard_frame import DashboardFrame
from app.gui.leaderboard_frame import LeaderboardFrame
from app.gui.login_frame import LoginFrame
from app.gui.plan_frame import PlanFrame
from app.gui.progress_frame import ProgressFrame
from app.gui.workout_frame import WorkoutFrame


class FitTrackApp(tk.Tk):
    """Root Tkinter window for FitTrack."""

    def __init__(self) -> None:
        """Initialize window, sidebar navigation, and content container."""
        super().__init__()
        self.title("FitTrack")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.current_user = None
        self.current_frame = None

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, padding=12)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ttk.Frame(self, padding=12)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        nav_items = [
            ("Login", LoginFrame),
            ("Dashboard", DashboardFrame),
            ("Workout", WorkoutFrame),
            ("Plans", PlanFrame),
            ("Progress", ProgressFrame),
            ("Leaderboard", LeaderboardFrame),
        ]
        for title, frame_cls in nav_items:
            ttk.Button(
                self.sidebar,
                text=title,
                command=lambda cls=frame_cls: self.show_frame(cls),
                width=20,
            ).pack(fill="x", pady=4)

        self.show_frame(LoginFrame)

    def show_frame(self, frame_cls: type[ttk.Frame]) -> None:
        """Swap the active content frame."""
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_cls(self.content, self)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        refresh = getattr(self.current_frame, "refresh", None)
        if callable(refresh):
            refresh()
