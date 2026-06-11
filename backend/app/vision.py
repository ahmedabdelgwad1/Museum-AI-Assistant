"""
Headless (no GUI) Visitor Vision State Machine.
Adapted from 'final face detection with state with multi person selection.py'
for server-side use within the LiveKit Agent Worker.

This module runs SYNCHRONOUSLY — always call process_frame() via asyncio.to_thread()
to avoid blocking the async event loop.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)


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
    STABLE_PRESENCE_THRESHOLD = 10   # frames of detection before confirming presence
    STABLE_ABSENCE_THRESHOLD  = 30   # frames of absence before returning to IDLE (~3s @10fps)
    CENTER_ENGAGE_THRESHOLD   = 15   # consecutive CENTER frames before ENGAGED
    SWITCH_DISTANCE_THRESHOLD = 150  # pixel distance to count as a new target selection
    LOCK_TIMEOUT              = 30   # frames before releasing the locked face target
    TARGET_FPS                = 10   # max frames per second to process (FPS limiter)

    def __init__(self):
        self._mp_face_mesh = mp.solutions.face_mesh
        self._face_mesh = self._mp_face_mesh.FaceMesh(
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )

        # State machine
        self._state           = "IDLE"
        self._stable_presence = 0
        self._stable_absence  = 0
        self._person_confirmed = False
        self._center_frames   = 0

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
            xs = [lm.x * w for lm in face.landmark]
            ys = [lm.y * h for lm in face.landmark]
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
            xs = [lm.x * w for lm in face.landmark]
            ys = [lm.y * h for lm in face.landmark]
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            dist = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest = face
        return closest

    def _get_face_center(self, face, w: int, h: int) -> tuple:
        xs = [lm.x * w for lm in face.landmark]
        ys = [lm.y * h for lm in face.landmark]
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
        results = self._face_mesh.process(rgb)

        person_count   = 0
        main_direction = "N/A"

        # ---- Face Detection + Target Lock ----
        if results.multi_face_landmarks:
            person_count  = len(results.multi_face_landmarks)
            sorted_faces  = self._get_faces_sorted_by_size(results.multi_face_landmarks, w, h)

            # Try to keep tracking the same person
            face = self._find_locked_face(sorted_faces, w, h)
            if face is None:
                face = sorted_faces[0]  # Fall back to largest (closest) face

            # Update lock
            self._locked_face_center = self._get_face_center(face, w, h)
            self._lock_lost_frames   = 0

            # Direction detection (nose relative to eye midpoint)
            nose    = face.landmark[1]
            left    = face.landmark[33]
            right   = face.landmark[263]
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

        # ---- Intent Detection (looking at robot center?) ----
        if main_direction == "CENTER":
            self._center_frames += 1
        else:
            self._center_frames = 0

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
            # Safety: ensure person is still visible before triggering AI
            if person_count > 0:
                self._state = "TALKING"
                logger.info("Vision: ENGAGED → TALKING 🗣️")
            else:
                self._state     = "OBSERVING"
                self._center_frames = 0

        elif self._state == "TALKING":
            if not self._person_confirmed:
                self._state = "IDLE"
                logger.info("Vision: TALKING → IDLE (visitor left 👋)")

        return self._state

    @property
    def state(self) -> str:
        """Current state string."""
        return self._state

    def reset(self):
        """
        Reset for a new visitor session.
        Call this when TALKING → IDLE transition is detected in agent.py.
        """
        self._state            = "IDLE"
        self._stable_presence  = 0
        self._stable_absence   = 0
        self._person_confirmed = False
        self._center_frames    = 0
        self._locked_face_center = None
        self._lock_lost_frames = 0
        logger.info("Vision: State machine reset 🔄 (ready for new visitor)")

    def close(self):
        """Release MediaPipe resources."""
        self._face_mesh.close()
        logger.info("Vision: FaceMesh released")
