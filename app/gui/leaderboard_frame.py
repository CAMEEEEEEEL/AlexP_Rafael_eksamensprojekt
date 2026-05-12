"""Leaderboard frame."""

import tkinter as tk
from tkinter import ttk

from app.gamification import get_top_n


class LeaderboardFrame(ttk.Frame):
    """Frame showing local leaderboard rankings with highlighted current user."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Leaderboard", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 4))
        ttk.Label(
            self,
            text="Top players ranked by total XP. Your row is highlighted.",
            foreground="grey",
        ).pack(anchor="w", pady=(0, 8))

        cols = ("#", "Username", "XP", "Level", "Rank")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for col, width in zip(cols, [40, 200, 80, 60, 100]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")
        self.tree.column("Username", anchor="w")

        self.tree.tag_configure("you", background="#d4edda", font=("Segoe UI", 9, "bold"))

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        current = self.app.current_user.username if self.app.current_user else None
        for idx, row in enumerate(get_top_n(20), start=1):
            tag = ("you",) if row["username"] == current else ()
            name = f"★ {row['username']}" if row["username"] == current else row["username"]
            self.tree.insert("", "end", values=(idx, name, row["xp"], row["level"], row["rank"]), tags=tag)
