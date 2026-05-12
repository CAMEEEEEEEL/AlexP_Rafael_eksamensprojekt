"""FitTrack entry point."""

from app.gui.app_window import FitTrackApp


def main() -> None:
    """Launch the FitTrack Tkinter application."""
    app = FitTrackApp()
    app.mainloop()


if __name__ == "__main__":
    main()
