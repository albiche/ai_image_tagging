# data_filling/data/io.py

import os
from data_filling.tools.video_to_frames import extract_keyframes_dynamic, extract_frames_regularly
import cv2


def detect_media(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"}
    if ext in video_exts:
        return "video"
    return "image"



import cv2

def get_images_from_case(case_path, mode="dynamic"):
    if not case_path:
        raise ValueError("No input provided.")

    all_images = []

    for path in case_path:
        media_type = detect_media(path)
        if media_type == "video":
            print(f"🎥 Extracting frames from video: {path} (mode={mode})")
            if mode == "regular":
                frames = extract_frames_regularly(path)
            else:
                frames = extract_keyframes_dynamic(path)
            all_images.extend(frames)
        else:
            print(f"🖼️ Reading image: {path}")
            img = cv2.imread(path)
            if img is not None:
                all_images.append(img)
            else:
                print(f"⚠️ Could not read image: {path}")

    return all_images
