# FitTrack

FitTrack is a local-first desktop fitness application built with Tkinter.

## Features
- User registration/login with local JSON profiles
- Workout logging for sets, reps, and lifted weight
- Workout split planning
- Progression analysis with 1RM estimation and plateau detection
- XP, levels, ranks, and local leaderboard
- Optional OpenCV camera module placeholder for form checks

## Tech Stack
- Python 3.11+
- Tkinter
- Pandas + NumPy
- Matplotlib
- OpenCV
- JSON/CSV local data files

## Run
1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   python main.py
   ```

User data is saved locally in `data/users/`.
