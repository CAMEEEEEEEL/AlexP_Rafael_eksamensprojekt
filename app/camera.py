"""MediaPipe Tasks + OpenCV form-checking helpers.

Uses the MediaPipe Tasks API (mediapipe >= 0.10, Python 3.11+).
Downloads the lite pose model (~4 MB) on first use.
Falls back to plain OpenCV motion scoring if MediaPipe/model unavailable.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Any

import numpy as np

try:
    import cv2
except Exception:
    cv2 = None  # type: ignore

try:
    import mediapipe as mp
    from mediapipe.tasks import python as _mp_python
    from mediapipe.tasks.python import vision as _mp_vision
    _TASKS_OK = True
except Exception:
    mp = None  # type: ignore
    _TASKS_OK = False

# ── Model download ────────────────────────────────────────────────────────────
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
_MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "pose_landmarker_lite.task"


def _ensure_model() -> bool:
    """Download the pose model if not already cached. Returns True on success."""
    if _MODEL_PATH.exists():
        return True
    try:
        _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        print("[FitTrack] Downloading pose model (~4 MB) on first use …")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("[FitTrack] Pose model downloaded.")
        return True
    except Exception as exc:
        print(f"[FitTrack] Could not download pose model: {exc}")
        return False


# ── Landmark indices (same as MediaPipe Pose spec) ────────────────────────────
_LS, _RS = 11, 12   # shoulders
_LE, _RE = 13, 14   # elbows
_LW, _RW = 15, 16   # wrists
_LH, _RH = 23, 24   # hips
_LK, _RK = 25, 26   # knees
_LA, _RA = 27, 28   # ankles

# Skeleton connections to draw (pairs of landmark indices)
_CONNECTIONS = [
    (_LS, _RS), (_LS, _LE), (_LE, _LW), (_RS, _RE), (_RE, _RW),
    (_LS, _LH), (_RS, _RH), (_LH, _RH),
    (_LH, _LK), (_LK, _LA), (_RH, _RK), (_RK, _RA),
]


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _angle(a: tuple, b: tuple, c: tuple) -> float:
    """Angle in degrees at point b formed by a→b and c→b."""
    a2, b2, c2 = np.array(a[:2]), np.array(b[:2]), np.array(c[:2])
    ba, bc = a2 - b2, c2 - b2
    norm = np.linalg.norm(ba) * np.linalg.norm(bc)
    if norm < 1e-6:
        return 0.0
    return float(np.degrees(np.arccos(np.clip(np.dot(ba, bc) / norm, -1.0, 1.0))))


def _lm(landmarks: list, idx: int) -> tuple[float, float, float]:
    lm = landmarks[idx]
    return (lm.x, lm.y, lm.z)


def _draw_skeleton(frame: Any, landmarks: list, w: int, h: int) -> None:
    """Draw landmarks and bones onto a BGR frame using OpenCV."""
    pts = {i: (int(lm.x * w), int(lm.y * h)) for i, lm in enumerate(landmarks)}
    for a, b in _CONNECTIONS:
        if a in pts and b in pts:
            cv2.line(frame, pts[a], pts[b], (0, 200, 100), 2)
    for pt in pts.values():
        cv2.circle(frame, pt, 4, (255, 255, 0), -1)


# ── Exercise configs ──────────────────────────────────────────────────────────

_CONFIGS: list[dict] = [
    {
        "keywords": ["curl", "bicep", "hammer", "preacher", "spider", "concentration"],
        "label": "Bicep Curl",
        "triple": (_LS, _LE, _LW),
        "down": 160, "up": 50,
        "tips_fn": lambda r, c: _curl_tips(r, c),
    },
    {
        "keywords": ["squat", "goblet", "hack", "front squat", "box squat", "wall sit"],
        "label": "Squat",
        "triple": (_LH, _LK, _LA),
        "down": 165, "up": 80,
        "tips_fn": lambda r, c: _squat_tips(r, c),
    },
    {
        "keywords": ["push", "bench", "chest", "dip", "fly", "pec"],
        "label": "Push / Bench",
        "triple": (_LS, _LE, _LW),
        "down": 160, "up": 70,
        "tips_fn": lambda r, c: _push_tips(r, c),
    },
    {
        "keywords": ["overhead press", "shoulder press", "arnold", "ohp", "military"],
        "label": "Overhead Press",
        "triple": (_LE, _LS, _LH),
        "down": 50, "up": 160,
        "tips_fn": lambda r, c: _press_tips(r, c),
    },
    {
        "keywords": ["deadlift", "romanian", "rdl", "good morning", "hip thrust", "glute"],
        "label": "Deadlift / Hip Hinge",
        "triple": (_LS, _LH, _LK),
        "down": 165, "up": 70,
        "tips_fn": lambda r, c: _deadlift_tips(r, c),
    },
    {
        "keywords": ["lunge", "split squat", "bulgarian", "step-up", "step up"],
        "label": "Lunge",
        "triple": (_LH, _LK, _LA),
        "down": 170, "up": 85,
        "tips_fn": lambda r, c: _squat_tips(r, c),
    },
    {
        "keywords": ["row", "pulldown", "pull-up", "pullup", "chin-up", "chin up",
                     "lat pulldown", "seated cable row"],
        "label": "Row / Pull",
        "triple": (_LS, _LE, _LW),
        "down": 160, "up": 60,
        "tips_fn": lambda r, c: _pull_tips(r, c),
    },
    {
        "keywords": ["tricep", "skull", "pushdown", "kickback", "extension"],
        "label": "Tricep",
        "triple": (_LS, _LE, _LW),
        "down": 160, "up": 60,
        "tips_fn": lambda r, c: _curl_tips(r, c),
    },
]


def _match(name: str) -> dict | None:
    lower = name.lower()
    for cfg in _CONFIGS:
        if any(kw in lower for kw in cfg["keywords"]):
            return cfg
    return None


# ── Tip generators ────────────────────────────────────────────────────────────

def _curl_tips(rom: float, con: float) -> list[str]:
    return [
        ("Great range of motion — full extension and contraction." if rom >= 75
         else "Increase range of motion — fully extend at the bottom and curl all the way up."),
        ("Tempo looks controlled and consistent." if con >= 65
         else "Avoid swinging — keep a slow, controlled tempo on both the up and down phase."),
    ]

def _squat_tips(rom: float, con: float) -> list[str]:
    return [
        ("Good squat depth — thighs at or below parallel." if rom >= 70
         else "Squat deeper — aim for thighs parallel to the floor or below."),
        ("Descent is controlled." if con >= 65
         else "Control the descent — lower slowly rather than dropping into the squat."),
    ]

def _push_tips(rom: float, con: float) -> list[str]:
    return [
        ("Full range of motion on the press." if rom >= 70
         else "Lower further — increase range of motion for more muscle activation."),
        ("Good press speed and consistency." if con >= 65
         else "Keep a consistent press speed — avoid rushing the concentric phase."),
    ]

def _press_tips(rom: float, con: float) -> list[str]:
    return [
        ("Full lockout achieved overhead." if rom >= 75
         else "Press all the way to full lockout overhead."),
        ("Bar path looks stable." if con >= 65
         else "Control the bar path — keep it vertical."),
    ]

def _deadlift_tips(rom: float, con: float) -> list[str]:
    return [
        ("Good hip hinge depth." if rom >= 70
         else "Hinge deeper at the hips — push hips further back on the way down."),
        ("Consistent movement — good spine control." if con >= 65
         else "Maintain a neutral spine throughout — avoid rounding the lower back."),
    ]

def _pull_tips(rom: float, con: float) -> list[str]:
    return [
        ("Full pulling range of motion." if rom >= 75
         else "Pull all the way — elbows should drive past the torso at the top."),
        ("Good eccentric control on the way down." if con >= 65
         else "Control the eccentric — lower slowly for better muscle growth."),
    ]

def _generic_tips(rom: float, con: float) -> list[str]:
    return [
        ("Good range of motion detected." if rom >= 65
         else "Focus on achieving a full range of motion each rep."),
        ("Movement tempo is consistent." if con >= 65
         else "Slow down and control each rep — avoid momentum-driven movement."),
    ]


# ── Public entry point ────────────────────────────────────────────────────────

def run_form_check_session(exercise_name: str, duration_seconds: int = 10) -> dict[str, Any]:
    """Run a webcam form-check session.

    Uses MediaPipe PoseLandmarker (Tasks API) when available.
    Falls back to plain OpenCV motion scoring otherwise.
    """
    if _TASKS_OK and cv2 is not None and _ensure_model():
        return _mediapipe_session(exercise_name, duration_seconds)
    if cv2 is not None:
        return _opencv_session(exercise_name, duration_seconds)
    return {
        "success": False, "score": 0.0,
        "message": "Neither MediaPipe nor OpenCV is available.\nRun: pip install mediapipe opencv-python",
        "tips": [],
    }


# ── MediaPipe Tasks session ───────────────────────────────────────────────────

def _mediapipe_session(exercise_name: str, duration_seconds: int) -> dict[str, Any]:
    cfg = _match(exercise_name)
    label = cfg["label"] if cfg else exercise_name

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return {"success": False, "score": 0.0,
                "message": "Unable to access webcam.", "tips": []}

    fps = int(cap.get(cv2.CAP_PROP_FPS) or 30)
    max_frames = duration_seconds * fps

    options = _mp_vision.PoseLandmarkerOptions(
        base_options=_mp_python.BaseOptions(model_asset_path=str(_MODEL_PATH)),
        running_mode=_mp_vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    angle_series: list[float] = []
    rep_count = 0
    rep_state = "down"

    with _mp_vision.PoseLandmarker.create_from_options(options) as landmarker:
        cv2.namedWindow("FitTrack Form Check", cv2.WINDOW_NORMAL)
        frames_done = 0
        timestamp_ms = 0

        while frames_done < max_frames:
            ok, frame = cap.read()
            if not ok:
                break

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timestamp_ms = int(frames_done * (1000 / fps))
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                lms = result.pose_landmarks[0]
                _draw_skeleton(frame, lms, w, h)

                if cfg:
                    try:
                        a = _lm(lms, cfg["triple"][0])
                        b = _lm(lms, cfg["triple"][1])
                        c = _lm(lms, cfg["triple"][2])
                        ang = _angle(a, b, c)
                        angle_series.append(ang)

                        # Rep counting via midpoint crossing
                        mid = (cfg["down"] + cfg["up"]) / 2
                        if rep_state == "down" and ang < mid:
                            rep_state = "up"
                        elif rep_state == "up" and ang > mid:
                            rep_state = "down"
                            rep_count += 1

                        colour = (0, 220, 0) if abs(ang - cfg["up"]) < 25 else (0, 200, 255)
                        cv2.putText(frame, f"Angle: {ang:.0f}°",
                                    (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, colour, 2)
                    except Exception:
                        pass

                cv2.putText(frame, f"Reps: {rep_count}",
                            (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            frames_done += 1
            remaining = max(0, duration_seconds - frames_done // fps)
            cv2.putText(frame,
                        f"{label}  |  {remaining}s remaining  (press Q to finish)",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            cv2.imshow("FitTrack Form Check", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()

    if not angle_series:
        return {
            "success": False, "score": 0.0,
            "message": "No pose detected. Ensure your full body is visible and lighting is good.",
            "tips": ["Step back so the camera can see your entire body.",
                     "Ensure good lighting and a plain background."],
        }

    actual_rom = float(np.ptp(angle_series))
    if cfg:
        target_rom = abs(cfg["down"] - cfg["up"])
        rom_score = float(np.clip((actual_rom / max(target_rom, 1)) * 100, 0, 100))
    else:
        rom_score = float(np.clip(actual_rom, 0, 100))

    if len(angle_series) > 2:
        diffs = np.abs(np.diff(angle_series))
        consistency_score = float(np.clip(100 - float(np.std(diffs)) * 4, 0, 100))
    else:
        consistency_score = 50.0

    stability_score = float(np.clip((rom_score + consistency_score) / 2, 0, 100))
    total = round(rom_score * 0.55 + consistency_score * 0.25 + stability_score * 0.20, 1)
    tips = cfg["tips_fn"](rom_score, consistency_score) if cfg else _generic_tips(rom_score, consistency_score)

    return {
        "success": True,
        "score": total,
        "rom_score": round(rom_score, 1),
        "stability_score": round(stability_score, 1),
        "consistency_score": round(consistency_score, 1),
        "rep_count": rep_count,
        "tips": tips,
        "exercise": label,
        "message": f"Form check complete. Score: {total}/100",
        "engine": "MediaPipe",
    }


# ── OpenCV fallback session ───────────────────────────────────────────────────

def _opencv_session(exercise_name: str, duration_seconds: int) -> dict[str, Any]:
    """Basic motion-based scoring — no pose estimation."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return {"success": False, "score": 0.0,
                "message": "Unable to access webcam.", "tips": []}

    fps = int(cap.get(cv2.CAP_PROP_FPS) or 30)
    max_frames = duration_seconds * fps

    ok, first = cap.read()
    if not ok:
        cap.release()
        return {"success": False, "score": 0.0,
                "message": "Failed to read webcam frames.", "tips": []}

    base = cv2.GaussianBlur(cv2.cvtColor(first, cv2.COLOR_BGR2GRAY), (7, 7), 0)
    fh, fw = base.shape
    min_area = fw * fh * 0.01

    height_series: list[float] = []
    cx_series: list[float] = []
    frames_done = 0

    cv2.namedWindow("FitTrack Form Check", cv2.WINDOW_NORMAL)
    while frames_done < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (7, 7), 0)
        delta = cv2.threshold(cv2.absdiff(base, gray), 25, 255, cv2.THRESH_BINARY)[1]
        delta = cv2.dilate(delta, None, iterations=2)
        contours, _ = cv2.findContours(delta, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            lc = max(contours, key=cv2.contourArea)
            if cv2.contourArea(lc) > min_area:
                x, y, bw, bh = cv2.boundingRect(lc)
                height_series.append(float(bh))
                cx_series.append(float(x + bw / 2))
                cv2.rectangle(frame, (x, y), (x + bw, y + bh), (80, 220, 80), 2)

        frames_done += 1
        remaining = max(0, duration_seconds - frames_done // fps)
        cv2.putText(frame, f"{exercise_name}  |  {remaining}s  (Q to finish)",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.imshow("FitTrack Form Check", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if not height_series:
        return {"success": False, "score": 0.0,
                "message": "No movement detected.",
                "tips": ["Ensure you are fully visible to the camera."]}

    mean_h = float(np.mean(height_series)) or 1.0
    rom_score = float(np.clip(float(np.ptp(height_series)) / mean_h * 260, 0, 100))
    stability_score = float(np.clip(100 - (float(np.std(cx_series)) / max(fw, 1)) * 800, 0, 100))
    consistency_score = float(np.clip(100 - (float(np.std(height_series)) / mean_h) * 380, 0, 100))
    total = round(rom_score * 0.4 + stability_score * 0.35 + consistency_score * 0.25, 1)

    reps, direction = 0, 0
    for i in range(1, len(height_series)):
        d = height_series[i] - height_series[i - 1]
        nd = 1 if d > 0 else -1 if d < 0 else direction
        if direction == 1 and nd == -1:
            reps += 1
        direction = nd

    tips: list[str] = []
    if rom_score < 65:
        tips.append("Increase controlled range of motion each rep.")
    if stability_score < 65:
        tips.append("Keep your torso and bar path more stable.")
    if consistency_score < 65:
        tips.append("Maintain a steadier tempo across reps.")
    if not tips:
        tips.append("Form looks consistent. Keep progression gradual.")

    return {
        "success": True,
        "score": total,
        "rom_score": round(rom_score, 1),
        "stability_score": round(stability_score, 1),
        "consistency_score": round(consistency_score, 1),
        "rep_count": reps,
        "tips": tips,
        "exercise": exercise_name,
        "message": f"Form check complete (motion mode). Score: {total}/100",
        "engine": "OpenCV",
    }


# ── Legacy helpers ────────────────────────────────────────────────────────────

def start_camera_preview() -> None:
    if cv2 is None:
        return
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        cv2.imshow("FitTrack Camera Preview", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


def check_form_similarity(current_angles: list[float], target_angles: list[float]) -> float:
    if not current_angles or not target_angles or len(current_angles) != len(target_angles):
        return 0.0
    return float(max(0.0, 100.0 - np.abs(np.array(current_angles) - np.array(target_angles)).mean()))
