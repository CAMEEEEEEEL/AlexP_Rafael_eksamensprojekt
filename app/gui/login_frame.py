"""Login and registration frame."""

import tkinter as tk
from tkinter import messagebox, ttk

from app import auth
from app.gui.dashboard_frame import DashboardFrame


class LoginFrame(ttk.Frame):
    """Frame for user login and quick registration."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk) -> None:
        """Build login/register input controls."""
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="FitTrack Login", font=("Segoe UI", 18, "bold")).pack(pady=12)

        self.username = ttk.Entry(self)
        self.password = ttk.Entry(self, show="*")
        self.age = ttk.Entry(self)
        self.weight = ttk.Entry(self)
        self.height = ttk.Entry(self)
        self.goals = ttk.Entry(self, width=40)

        fields = [
            ("Username", self.username),
            ("Password", self.password),
            ("Age", self.age),
            ("Weight (kg)", self.weight),
            ("Height (cm)", self.height),
            ("Goals", self.goals),
        ]
        for label, widget in fields:
            ttk.Label(self, text=label).pack(anchor="w")
            widget.pack(fill="x", pady=4)

        button_row = ttk.Frame(self)
        button_row.pack(pady=10, fill="x")
        ttk.Button(button_row, text="Login", command=self._handle_login).pack(side="left", padx=4)
        ttk.Button(button_row, text="Register", command=self._handle_register).pack(side="left", padx=4)

    def _handle_login(self) -> None:
        """Authenticate user and navigate to dashboard."""
        user = auth.login_user(self.username.get().strip(), self.password.get())
        if user is None:
            messagebox.showerror("Login failed", "Invalid username or password.")
            return
        self.app.current_user = user
        messagebox.showinfo("Success", f"Welcome back, {user.username}!")
        self.app.show_frame(DashboardFrame)

    def _handle_register(self) -> None:
        """Register a new user profile and sign in."""
        try:
            success = auth.register_user(
                username=self.username.get().strip(),
                password=self.password.get(),
                age=int(self.age.get() or 0),
                weight_kg=float(self.weight.get() or 0),
                height_cm=float(self.height.get() or 0),
                goals=self.goals.get().strip(),
            )
        except ValueError:
            messagebox.showerror("Invalid input", "Age, weight, and height must be numeric.")
            return

        if not success:
            messagebox.showerror("Register failed", "Username already exists.")
            return

        self.app.current_user = auth.login_user(self.username.get().strip(), self.password.get())
        messagebox.showinfo("Success", "Registration completed.")
        self.app.show_frame(DashboardFrame)
