"""Ranks tab — shows all rank tiers, XP requirements and the user's progress."""

import tkinter as tk
from tkinter import ttk

from app.gamification import LEVEL_THRESHOLDS, RANK_NAMES, XP_PER_SET  # XP_PER_SET used in progress card


# Rank badge colours  (background, foreground)
_RANK_COLOURS: dict[str, tuple[str, str]] = {
    "Beginner":  ("#e0e0e0", "#333333"),
    "Iron":      ("#909090", "#ffffff"),
    "Bronze":    ("#cd7f32", "#ffffff"),
    "Silver":    ("#c0c0c0", "#1a1a1a"),
    "Gold":      ("#ffd700", "#1a1a1a"),
    "Platinum":  ("#00bcd4", "#ffffff"),
    "Diamond":   ("#90caf9", "#0d47a1"),
    "Elite":     ("#7b1fa2", "#ffffff"),
}

# Emoji medals shown on each rank row
_RANK_ICONS: dict[str, str] = {
    "Beginner":  "🔰",
    "Iron":      "⚙️",
    "Bronze":    "🥉",
    "Silver":    "🥈",
    "Gold":      "🥇",
    "Platinum":  "💎",
    "Diamond":   "🔷",
    "Elite":     "👑",
}


class RanksFrame(ttk.Frame):
    """Frame displaying all rank tiers and the current user's progression."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Ranks & Progression",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 4))

        # ── Top: user progress card ───────────────────────────────────
        self._card = ttk.LabelFrame(self, text="Your Progress", padding=12)
        self._card.pack(fill="x", pady=(0, 14))

        self._rank_var  = tk.StringVar(value="—")
        self._level_var = tk.StringVar(value="—")
        self._xp_var    = tk.StringVar(value="—")
        self._next_var  = tk.StringVar(value="")

        top_row = ttk.Frame(self._card)
        top_row.pack(fill="x")

        self._rank_badge = tk.Label(
            top_row, textvariable=self._rank_var,
            font=("Segoe UI", 14, "bold"), width=12,
            relief="flat", bd=0, padx=10, pady=6,
        )
        self._rank_badge.pack(side="left", padx=(0, 18))

        info = ttk.Frame(top_row)
        info.pack(side="left", fill="x", expand=True)
        ttk.Label(info, textvariable=self._level_var, font=("Segoe UI", 11)).pack(anchor="w")
        ttk.Label(info, textvariable=self._xp_var,    font=("Segoe UI", 11)).pack(anchor="w")
        ttk.Label(info, textvariable=self._next_var,  font=("Segoe UI", 10),
                  foreground="#555555").pack(anchor="w", pady=(2, 0))

        self._progress = ttk.Progressbar(self._card, length=400, mode="determinate")
        self._progress.pack(fill="x", pady=(10, 0))

        # ── Bottom: scrollable rank list ──────────────────────────────
        ttk.Label(self, text="All Ranks  (8 total)",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))

        # Canvas + scrollbar so the list scrolls if window is small
        list_outer = ttk.Frame(self)
        list_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(list_outer, highlightthickness=0)
        vbar = ttk.Scrollbar(list_outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vbar.set)

        vbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor="nw"
        )

        self._list_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>",     self._on_canvas_configure)

        # Build one row widget per rank — stored so refresh() can update them
        self._row_widgets: list[dict] = []
        self._build_rank_list()

    # ── Layout helpers ────────────────────────────────────────────────

    def _on_frame_configure(self, _event: tk.Event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    # ── Build list rows ───────────────────────────────────────────────

    def _build_rank_list(self) -> None:
        """Create one styled row for each of the 8 ranks."""
        for idx, (rank, threshold) in enumerate(zip(RANK_NAMES, LEVEL_THRESHOLDS)):
            level      = idx + 1
            bg, fg = _RANK_COLOURS[rank]
            icon   = _RANK_ICONS[rank]

            # Outer card frame — border via highlightbackground
            card = tk.Frame(
                self._list_frame,
                bg=bg,
                highlightbackground="#cccccc",
                highlightthickness=1,
                padx=10, pady=8,
            )
            card.pack(fill="x", padx=6, pady=3)

            # Left: icon + rank name
            left_lbl = tk.Label(
                card,
                text=f"{icon}  {rank}",
                font=("Segoe UI", 13, "bold"),
                bg=bg, fg=fg, anchor="w",
            )
            left_lbl.pack(side="left", padx=(0, 20))

            # Right: level / XP / sets info
            xp_label  = "Start rank" if threshold == 0 else f"{threshold} XP required"
            info_text = f"Level {level}   •   {xp_label}"
            info_lbl = tk.Label(
                card,
                text=info_text,
                font=("Segoe UI", 10),
                bg=bg, fg=fg, anchor="w",
            )
            info_lbl.pack(side="left", fill="x", expand=True)

            # "YOU ARE HERE" tag (hidden by default)
            here_lbl = tk.Label(
                card,
                text="◀ YOU ARE HERE",
                font=("Segoe UI", 10, "bold"),
                bg=bg, fg=fg,
            )
            # not packed yet — refresh() will show/hide it

            self._row_widgets.append({
                "card":     card,
                "left":     left_lbl,
                "info":     info_lbl,
                "here":     here_lbl,
                "rank":     rank,
                "level":    level,
                "orig_bg":  bg,
                "orig_fg":  fg,
            })

    # ── Public refresh ────────────────────────────────────────────────

    def refresh(self) -> None:
        user = self.app.current_user

        # ── progress card ─────────────────────────────────────────────
        if user is None:
            self._rank_var.set("—")
            self._level_var.set("Log in to see your rank.")
            self._xp_var.set("")
            self._next_var.set("")
            self._progress["value"] = 0
            self._rank_badge.configure(background="#e0e0e0", foreground="#333333")
            self._reset_list_rows()
            return

        current_level = user.level
        current_xp    = user.xp
        rank_name     = user.rank

        self._rank_var.set(rank_name)
        self._level_var.set(f"Level {current_level}")
        self._xp_var.set(f"Total XP: {current_xp}")

        badge_bg, badge_fg = _RANK_COLOURS.get(rank_name, ("#e0e0e0", "#333333"))
        self._rank_badge.configure(background=badge_bg, foreground=badge_fg)

        idx = current_level - 1   # 0-based
        if current_level < len(LEVEL_THRESHOLDS):
            next_threshold = LEVEL_THRESHOLDS[idx + 1]
            prev_threshold = LEVEL_THRESHOLDS[idx]
            span   = next_threshold - prev_threshold
            gained = current_xp - prev_threshold
            pct    = max(0, min(100, int(gained / span * 100))) if span > 0 else 100
            xp_needed = next_threshold - current_xp
            next_rank = RANK_NAMES[idx + 1]
            self._next_var.set(
                f"Next rank: {next_rank} at {next_threshold} XP  "
                f"({xp_needed} XP / {max(0, -(-xp_needed // XP_PER_SET))} sets remaining)"
            )
            self._progress["value"] = pct
        else:
            self._next_var.set("You have reached the highest rank — Elite!")
            self._progress["value"] = 100

        # ── rank list highlighting ────────────────────────────────────
        for row in self._row_widgets:
            rank  = row["rank"]
            level = row["level"]
            bg    = row["orig_bg"]
            fg    = row["orig_fg"]
            here  = row["here"]

            if rank == rank_name:
                # Brighten the current rank row with a green tint overlay
                row["card"].configure(bg="#d4edda", highlightbackground="#28a745", highlightthickness=2)
                row["left"].configure(bg="#d4edda", fg="#155724")
                row["info"].configure(bg="#d4edda", fg="#155724")
                here.configure(bg="#d4edda", fg="#155724")
                here.pack(side="right", padx=6)
            elif level > current_level:
                # Future / locked rank — dim it
                row["card"].configure(bg="#f5f5f5", highlightbackground="#cccccc", highlightthickness=1)
                row["left"].configure(bg="#f5f5f5", fg="#aaaaaa")
                row["info"].configure(bg="#f5f5f5", fg="#aaaaaa")
                here.pack_forget()
            else:
                # Already unlocked — show in original colours
                row["card"].configure(bg=bg, highlightbackground="#cccccc", highlightthickness=1)
                row["left"].configure(bg=bg, fg=fg)
                row["info"].configure(bg=bg, fg=fg)
                here.pack_forget()

    def _reset_list_rows(self) -> None:
        for row in self._row_widgets:
            bg = row["orig_bg"]
            fg = row["orig_fg"]
            row["card"].configure(bg=bg, highlightbackground="#cccccc", highlightthickness=1)
            row["left"].configure(bg=bg, fg=fg)
            row["info"].configure(bg=bg, fg=fg)
            row["here"].pack_forget()
