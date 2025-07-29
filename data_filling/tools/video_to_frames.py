# data_filling/tools/video_to_frames.py

import cv2
import numpy as np
import statistics
from typing import List


def is_uniform(frame, threshold_std: float = 5.0) -> bool:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.std(gray) < threshold_std


def extract_keyframes_dynamic(video_path: str, fps_target: float = 0.5, k: float = 4.0) -> List[np.ndarray]:
    """
    Extract keyframes dynamically based on inter-frame differences, aiming for ~1 frame every 2 seconds.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():

        print(f"Error: Cannot open video '{video_path}'.")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps
    max_frames = max(3, int(duration_sec * fps_target))  # 1 frame every 2 seconds
    min_frames = min(3, max_frames)

    ret, prev_frame = cap.read()
    if not ret:
        print(f"Error: Empty or corrupted video '{video_path}'.")
        return []

    frames = [prev_frame]
    diffs = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

        prev_gray = cv2.cvtColor(frames[-2], cv2.COLOR_BGR2GRAY)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff_val = np.sum(cv2.absdiff(prev_gray, gray))
        diffs.append((diff_val, len(frames) - 1))

    cap.release()

    if not diffs:
        return [frames[0]] if not is_uniform(frames[0]) else []

    diff_values = [float(d[0]) for d in diffs]
    threshold = statistics.mean(diff_values) + k * statistics.pstdev(diff_values)
    selected = [idx for (val, idx) in diffs if val >= threshold]

    if 0 not in selected:
        selected.insert(0, 0)
    if len(frames) - 1 not in selected:
        selected.append(len(frames) - 1)

    selected = sorted(set(selected))

    if len(selected) < min_frames:
        top_diffs = sorted(diffs, key=lambda x: x[0], reverse=True)
        needed = min_frames - len(selected)
        for val, idx in top_diffs:
            if idx not in selected:
                selected.append(idx)
                needed -= 1
                if needed == 0:
                    break
        selected = sorted(set(selected))

    if len(selected) > max_frames:
        diff_dict = {idx: val for (val, idx) in diffs if idx in selected}
        sorted_by_diff = sorted(selected, key=lambda x: diff_dict.get(x, 0), reverse=True)
        selected = sorted(set(sorted_by_diff[:max_frames]))

    return [frames[i] for i in selected if not is_uniform(frames[i])]


def extract_frames_regularly(video_path: str, fps_target: float = 0.5) -> List[np.ndarray]:
    """
    Extract frames at regular intervals (e.g., every 2 seconds) from a video.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video '{video_path}'.")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = max(1, int(fps / fps_target))  # e.g., if fps=30, every 60 frames for 0.5 fps (2s)

    selected_frames = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0 and not is_uniform(frame):
            selected_frames.append(frame)
        frame_idx += 1

    cap.release()
    return selected_frames
