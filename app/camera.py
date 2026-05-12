"""OpenCV-based form-checking helpers."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


def start_camera_preview() -> None:
    """Open a webcam preview window until the user presses `q`."""
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
    """Compute a basic similarity score between current and target joint angles."""
    if not current_angles or not target_angles or len(current_angles) != len(target_angles):
        return 0.0
    current = np.array(current_angles, dtype=float)
    target = np.array(target_angles, dtype=float)
    diff = np.abs(current - target).mean()
    return float(max(0.0, 100.0 - diff))


def _estimate_rep_count(height_series: list[float]) -> int:
    """Estimate rough rep count from local extrema in movement height data."""
    if len(height_series) < 5:
        return 0

    reps = 0
    direction = 0
    for idx in range(1, len(height_series)):
        delta = height_series[idx] - height_series[idx - 1]
        new_direction = 1 if delta > 0 else -1 if delta < 0 else direction
        if direction == 1 and new_direction == -1:
            reps += 1
        direction = new_direction
    return max(0, reps)


def _form_tips_from_scores(rom_score: float, stability_score: float, consistency_score: float) -> list[str]:
    """Return qualitative tips based on component scores."""
    tips: list[str] = []
    if rom_score < 65:
        tips.append("Increase controlled range of motion each rep.")
    if stability_score < 65:
        tips.append("Keep your torso and bar path more stable.")
    if consistency_score < 65:
        tips.append("Maintain a steadier tempo across reps.")
    if not tips:
        tips.append("Form looks consistent. Keep progression gradual.")
    return tips


def evaluate_form_metrics(height_series: list[float], center_x_series: list[float], frame_width: int) -> dict[str, Any]:
    """Evaluate movement metrics and compute an overall form score."""
    if not height_series:
        return {
            "success": False,
            "score": 0.0,
            "rom_score": 0.0,
            "stability_score": 0.0,
            "consistency_score": 0.0,
            "rep_count": 0,
            "tips": ["Not enough movement detected for analysis."],
            "message": "Form check failed: insufficient movement detected.",
        }

    movement_range = float(np.ptp(height_series))
    mean_height = float(np.mean(height_series)) if height_series else 1.0
    variability = float(np.std(height_series))
    center_std = float(np.std(center_x_series)) if center_x_series else 0.0

    rom_ratio = movement_range / max(mean_height, 1.0)
    rom_score = float(np.clip(rom_ratio * 260, 0, 100))

    center_ratio = center_std / max(frame_width, 1.0)
    stability_score = float(np.clip(100 - (center_ratio * 800), 0, 100))

    consistency_ratio = variability / max(mean_height, 1.0)
    consistency_score = float(np.clip(100 - (consistency_ratio * 380), 0, 100))

    total_score = round((rom_score * 0.4) + (stability_score * 0.35) + (consistency_score * 0.25), 1)
    rep_count = _estimate_rep_count(height_series)
    tips = _form_tips_from_scores(rom_score, stability_score, consistency_score)

    return {
        "success": True,
        "score": total_score,
        "rom_score": round(rom_score, 1),
        "stability_score": round(stability_score, 1),
        "consistency_score": round(consistency_score, 1),
        "rep_count": rep_count,
        "tips": tips,
        "message": f"Form check complete. Score: {total_score}/100",
    }


def run_form_check_session(exercise_name: str, duration_seconds: int = 8) -> dict[str, Any]:
    """Run webcam-based form analysis and return score, metrics, and feedback."""
    if cv2 is None:
        return {
            "success": False,
            "score": 0.0,
            "message": "OpenCV is not available. Install opencv-python to use form checking.",
            "tips": [],
        }

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return {
            "success": False,
            "score": 0.0,
            "message": "Unable to access webcam.",
            "tips": [],
        }

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = int(fps) if fps and fps > 0 else 30
    max_frames = max(30, duration_seconds * fps)

    ok, first_frame = cap.read()
    if not ok:
        cap.release()
        return {
            "success": False,
            "score": 0.0,
            "message": "Failed to read webcam frames.",
            "tips": [],
        }

    base_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    base_gray = cv2.GaussianBlur(base_gray, (7, 7), 0)
    frame_h, frame_w = base_gray.shape

    height_series: list[float] = []
    center_x_series: list[float] = []
    frames_processed = 0
    min_area = frame_w * frame_h * 0.01

    cv2.namedWindow("FitTrack Form Check", cv2.WINDOW_NORMAL)
    while frames_processed < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)

        delta = cv2.absdiff(base_gray, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(largest)
                height_series.append(float(h))
                center_x_series.append(float(x + (w / 2)))
                cv2.rectangle(frame, (x, y), (x + w, y + h), (80, 220, 80), 2)

        frames_processed += 1
        cv2.putText(
            frame,
            f"{exercise_name} form check ({frames_processed}/{max_frames}) - press q to finish",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        cv2.imshow("FitTrack Form Check", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyWindow("FitTrack Form Check")

    result = evaluate_form_metrics(height_series, center_x_series, frame_w)
    result["exercise"] = exercise_name.strip()
    result["frames_processed"] = frames_processed
    return result
