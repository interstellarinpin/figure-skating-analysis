r"""
Monocular pose extraction for skating clips.

This is a thin, dependency-optional wrapper around a 2.5-D body-landmark
detector. By default it targets MediaPipe Pose (33 landmarks, normalized image
coordinates plus a rough ``z``), because it runs on CPU on a laptop and needs
no rig. The extractor is isolated here so the kinematics layer
(:mod:`skating.video.kinematics`) can run on landmark arrays from *any* source
-- MediaPipe, an OpenPose dump, or synthetic data in the tests.

If MediaPipe / OpenCV are not installed, :func:`extract_pose` raises a clear
error telling you what to install; everything downstream still works on arrays.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# MediaPipe Pose landmark indices we actually use for spin kinematics.
LANDMARKS = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
}


@dataclass
class PoseTrack:
    """A time series of body landmarks.

    Attributes
    ----------
    times : (T,) array of seconds.
    points : (T, L, 3) array of landmark coordinates (image x, image y, depth z),
        with x, y normalized to [0, 1] and the origin at the top-left.
    visibility : (T, L) array in [0, 1], confidence per landmark.
    fps : float, source frame rate.
    """

    times: np.ndarray
    points: np.ndarray
    visibility: np.ndarray
    fps: float

    def landmark(self, name: str) -> np.ndarray:
        """Return the ``(T, 3)`` track of a named landmark."""
        return self.points[:, LANDMARKS[name], :]

    @property
    def n_frames(self) -> int:
        return self.points.shape[0]


def extract_pose(video_path: str, model_complexity: int = 1) -> PoseTrack:
    """Run a pose detector over a video file and return a :class:`PoseTrack`.

    Requires ``mediapipe`` and ``opencv-python`` (install the ``video`` extra).
    Raises :class:`ImportError` with guidance if they are missing so the rest of
    the package stays usable on CPU without heavy vision deps.
    """
    try:
        import cv2  # type: ignore
        import mediapipe as mp  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "extract_pose needs mediapipe and opencv-python. Install with:\n"
            "    pip install 'skating[video]'\n"
            "or:\n"
            "    pip install mediapipe opencv-python"
        ) from exc

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    n_land = max(LANDMARKS.values()) + 1
    pts: list[np.ndarray] = []
    vis: list[np.ndarray] = []
    times: list[float] = []

    mp_pose = mp.solutions.pose
    with mp_pose.Pose(model_complexity=model_complexity) as pose:
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)
            frame_pts = np.full((n_land, 3), np.nan)
            frame_vis = np.zeros(n_land)
            if res.pose_landmarks:
                for i, lm in enumerate(res.pose_landmarks.landmark):
                    if i < n_land:
                        frame_pts[i] = (lm.x, lm.y, lm.z)
                        frame_vis[i] = lm.visibility
            pts.append(frame_pts)
            vis.append(frame_vis)
            times.append(frame_idx / fps)
            frame_idx += 1
    cap.release()

    return PoseTrack(
        times=np.asarray(times),
        points=np.asarray(pts),
        visibility=np.asarray(vis),
        fps=fps,
    )


def synthetic_spin(
    n_frames: int = 180,
    fps: float = 60.0,
    revolutions: float = 3.0,
    draw_in: bool = True,
) -> PoseTrack:
    """A clean synthetic spin for tests / demos (no video, no deps).

    Generates shoulders, hips, and wrists of a body rotating about a vertical
    image axis. If ``draw_in`` is true the wrists spiral inward over time,
    mimicking an arm pull; the kinematics layer should recover both the rising
    rotation rate and the shrinking arm-extension proxy.
    """
    t = np.arange(n_frames) / fps
    total = revolutions * 2.0 * np.pi
    # accelerate: arms drawn in -> faster late rotation
    phase = total * (t / t[-1]) ** (1.4 if draw_in else 1.0)

    n_land = max(LANDMARKS.values()) + 1
    pts = np.full((n_frames, n_land, 3), np.nan)
    vis = np.ones((n_frames, n_land))
    cx, cy = 0.5, 0.5

    shoulder_r = 0.08
    hip_r = 0.06
    wrist_r0, wrist_r1 = 0.22, 0.07
    wrist_r = np.linspace(wrist_r0, wrist_r1, n_frames) if draw_in else np.full(n_frames, wrist_r0)

    def place(idx, radius, angle):
        # Azimuth rendered directly in the image (x, y) plane: viewing a spin
        # from above. The shoulder/hip/wrist vectors then carry the body angle.
        r = np.asarray(radius, dtype=float)
        pts[:, idx, 0] = cx + r * np.cos(angle)
        pts[:, idx, 1] = cy + r * np.sin(angle)
        pts[:, idx, 2] = 0.0

    place(LANDMARKS["left_shoulder"], shoulder_r, phase)
    place(LANDMARKS["right_shoulder"], shoulder_r, phase + np.pi)
    place(LANDMARKS["left_hip"], hip_r, phase)
    place(LANDMARKS["right_hip"], hip_r, phase + np.pi)
    place(LANDMARKS["left_wrist"], wrist_r, phase)
    place(LANDMARKS["right_wrist"], wrist_r, phase + np.pi)

    return PoseTrack(times=t, points=pts, visibility=vis, fps=fps)
