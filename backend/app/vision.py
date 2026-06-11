"""
Headless (no GUI) Visitor Vision State Machine.
Adapted from 'final face detection with state with multi person selection.py'
for server-side use within the LiveKit Agent Worker.

This module runs SYNCHRONOUSLY — always call process_frame() via asyncio.to_thread()
to avoid blocking the async event loop.
"""

import os
import tempfile
import time
import logging

import cv2
import numpy as np

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

logger = logging.getLogger(__name__)

import os
import pathlib

# Build the FaceLandmarker once at module level
model_path = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
_base_opts = mp_python.BaseOptions(model_asset_path=model_path)
_face_opts = mp_vision.FaceLandmarkerOptions(
    base_options=_base_opts,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False,
    num_faces=4,
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5,
)
face_landmarker = mp_vision.FaceLandmarker.create_from_options(_face_opts)


class VisitorVision:
    """
    MediaPipe FaceMesh-based State Machine for detecting museum visitor engagement.

    States:
        IDLE       → No visitor detected (stable absence confirmed)
        OBSERVING  → Visitor present but not yet looking directly at the robot
        ENGAGED    → Visitor looking at robot center (trigger for AI greeting)
        TALKING    → Conversation in progress

    Usage (always call from asyncio.to_thread):
        vision = VisitorVision()
        state = await asyncio.to_thread(vision.process_frame, bgr_frame)
    """

    # ---- Configuration Thresholds ----
    STABLE_PRESENCE_THRESHOLD = 3      # frames to confirm visitor is present (~0.3s @10fps)
    STABLE_ABSENCE_THRESHOLD  = 5      # frames to confirm visitor is gone  (~0.5s @10fps)
    CENTER_ENGAGE_THRESHOLD   = 5      # consecutive CENTER frames before ENGAGED (~0.5s)
    LOOK_AWAY_THRESHOLD       = 6      # consecutive LEFT/RIGHT frames before asking to continue
    SWITCH_DISTANCE_THRESHOLD = 150    # pixel distance to count as a new target selection
    LOCK_TIMEOUT              = 10     # frames before releasing the locked face target (~1s)
    TARGET_FPS                = 10     # max frames per second to process (FPS limiter)

    def __init__(self):
        # FaceLandmarker is initialized globally above

        # State machine
        self._state            = "IDLE"
        self._stable_presence  = 0
        self._stable_absence   = 0
        self._person_confirmed = False
        self._center_frames    = 0
        self._look_away_frames = 0

        # Target lock — keeps tracking the same visitor across frames
        self._locked_face_center = None
        self._lock_lost_frames   = 0

        # FPS limiter — skip frames to stay at TARGET_FPS
        self._last_process_time = 0.0
        self._frame_interval    = 1.0 / self.TARGET_FPS

        logger.info("VisitorVision initialized — Headless mode, %d FPS target", self.TARGET_FPS)

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_faces_sorted_by_size(self, faces, w: int, h: int) -> list:
        """Return faces sorted largest-first (largest = closest to camera)."""
        scored = []
        for face in faces:
            xs = [lm.x * w for lm in face]
            ys = [lm.y * h for lm in face]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            scored.append((area, face))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored]

    def _find_locked_face(self, faces, w: int, h: int, max_dist: int = 100):
        """Try to re-find the previously locked face within max_dist pixels."""
        if self._locked_face_center is None:
            return None
        lx, ly = self._locked_face_center
        closest, closest_dist = None, max_dist
        for face in faces:
            xs = [lm.x * w for lm in face]
            ys = [lm.y * h for lm in face]
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            dist = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest = face
        return closest

    def _get_face_center(self, face, w: int, h: int) -> tuple:
        xs = [lm.x * w for lm in face]
        ys = [lm.y * h for lm in face]
        return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def process_frame(self, frame_bgr: np.ndarray) -> str:
        """
        Process a single BGR frame and update the internal state machine.

        Returns the current state string: "IDLE" | "OBSERVING" | "ENGAGED" | "TALKING"

        *** SYNCHRONOUS — always call via asyncio.to_thread() ***
        """
        # ---- FPS Limiter: skip this frame if too soon ----
        now = time.monotonic()
        if now - self._last_process_time < self._frame_interval:
            return self._state
        self._last_process_time = now

        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = face_landmarker.detect(mp_image)

        person_count   = 0
        main_direction = "N/A"

        # ---- Face Detection + Target Lock ----
        if result.face_landmarks:
            person_count  = len(result.face_landmarks)
            sorted_faces  = self._get_faces_sorted_by_size(result.face_landmarks, w, h)

            # Try to keep tracking the same person
            face = self._find_locked_face(sorted_faces, w, h)
            if face is None:
                face = sorted_faces[0]  # Fall back to largest (closest) face

            # Update lock
            self._locked_face_center = self._get_face_center(face, w, h)
            self._lock_lost_frames   = 0

            # Direction detection (nose relative to eye midpoint)
            nose    = face[1]
            left    = face[33]
            right   = face[263]
            x_nose  = nose.x * w
            center_x = ((left.x + right.x) / 2) * w
            error   = (x_nose - center_x) / w

            if error < -0.05:
                main_direction = "RIGHT"
            elif error > 0.05:
                main_direction = "LEFT"
            else:
                main_direction = "CENTER"
        else:
            self._lock_lost_frames += 1
            if self._lock_lost_frames > self.LOCK_TIMEOUT:
                self._locked_face_center = None

        # ---- Stability Filter (debounce rapid state flips) ----
        if person_count > 0:
            self._stable_presence += 1
            self._stable_absence   = 0
        else:
            self._stable_absence  += 1
            self._stable_presence  = 0

        if self._stable_presence >= self.STABLE_PRESENCE_THRESHOLD:
            self._person_confirmed = True

        if self._stable_absence >= self.STABLE_ABSENCE_THRESHOLD:
            self._person_confirmed  = False
            self._state             = "IDLE"
            self._center_frames     = 0
            self._locked_face_center = None

        # ---- Intent Detection ----
        if main_direction == "CENTER":
            self._center_frames += 1
            self._look_away_frames = 0
        else:
            self._center_frames = 0
            if person_count > 0 and self._person_confirmed:
                self._look_away_frames += 1
            else:
                self._look_away_frames = 0

        # ---- State Machine Transitions ----
        if self._state == "IDLE":
            if self._person_confirmed:
                self._state = "OBSERVING"
                logger.info("Vision: IDLE → OBSERVING")

        elif self._state == "OBSERVING":
            if self._center_frames >= self.CENTER_ENGAGE_THRESHOLD:
                self._state = "ENGAGED"
                logger.info("Vision: OBSERVING → ENGAGED 🎯 (visitor is looking at robot!)")

        elif self._state == "ENGAGED":
            if self._look_away_frames >= self.LOOK_AWAY_THRESHOLD:
                self._state = "OBSERVING"
                self._center_frames = 0
                logger.info("Vision: ENGAGED → OBSERVING (visitor looked away)")
            elif person_count > 0:
                self._state = "TALKING"
                logger.info("Vision: ENGAGED → TALKING 🗣️")

        elif self._state == "TALKING":
            if self._stable_absence >= self.STABLE_ABSENCE_THRESHOLD:
                self._state = "IDLE"
                logger.info("Vision: TALKING → IDLE (visitor left 👋)")
            elif self._look_away_frames >= self.LOOK_AWAY_THRESHOLD:
                self._state = "OBSERVING"
                self._center_frames = 0
                logger.info("Vision: TALKING → OBSERVING (visitor looked %s)", main_direction.lower())

        return self._state

    @property
    def state(self) -> str:
        """Current state string."""
        return self._state

    def reset(self):
        """Reset for a new visitor session."""
        self._state              = "IDLE"
        self._stable_presence    = 0
        self._stable_absence     = 0
        self._person_confirmed   = False
        self._center_frames      = 0
        self._look_away_frames   = 0
        self._locked_face_center = None
        self._lock_lost_frames   = 0
        logger.info("Vision: State machine reset 🔄 (ready for new visitor)")

    def close(self):
        """Release MediaPipe resources."""
        # FaceLandmarker is global, no need to close per instance.
        logger.info("Vision: FaceLandmarker released")
