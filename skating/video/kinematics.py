r"""
Turn a :class:`~skating.video.pose.PoseTrack` into spin kinematics.

These functions are the bridge from pixels to physics: from landmark tracks
they recover the body's azimuth, its rotation rate and revolution count, an
arm-extension proxy, and a moment-of-inertia proxy. The inertia proxy is what
lets a video be read in the same language as :mod:`skating.physics` -- you can
watch ``I(t)`` fall as the arms come in and ``omega(t)`` rise to match.

All of this operates on plain arrays, so it runs in the tests on synthetic
poses with no vision dependencies.
"""

from __future__ import annotations

import numpy as np

from .pose import PoseTrack

# Rough limb mass fractions (Winter, *Biomechanics and Motor Control*),
# used only to weight the inertia proxy; absolute scale is arbitrary.
SEGMENT_MASS_FRACTION = {
    "trunk": 0.50,
    "arm": 0.05,   # each upper+fore arm+hand, per side
    "leg": 0.16,   # each thigh+shank+foot, per side
}


def _mid(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 0.5 * (a + b)


def body_center(track: PoseTrack) -> np.ndarray:
    """Approximate spin axis location per frame: midpoint of the two hips."""
    return _mid(track.landmark("left_hip"), track.landmark("right_hip"))


def body_axis_angle(track: PoseTrack) -> np.ndarray:
    """Unwrapped azimuth (rad) of the shoulder line in the image plane.

    Uses the vector from right to left shoulder; ``np.unwrap`` removes the
    2*pi jumps so the result accumulates across many revolutions.
    """
    ls = track.landmark("left_shoulder")[:, :2]
    rs = track.landmark("right_shoulder")[:, :2]
    v = ls - rs
    angle = np.arctan2(v[:, 1], v[:, 0])
    return np.unwrap(angle)


def rotation_rate(track: PoseTrack, smooth: int = 5) -> np.ndarray:
    """Instantaneous spin rate ``omega(t)`` (rad/s) from the azimuth track."""
    angle = body_axis_angle(track)
    if smooth > 1:
        angle = _moving_average(angle, smooth)
    return np.gradient(angle, track.times)


def count_revolutions(track: PoseTrack) -> float:
    """Total revolutions turned over the clip."""
    angle = body_axis_angle(track)
    return float(abs(angle[-1] - angle[0]) / (2.0 * np.pi))


def arm_extension_proxy(track: PoseTrack) -> np.ndarray:
    """Per-frame arm extension in ``[0, 1]``-ish units.

    Defined as mean wrist distance from the spin axis, normalized by shoulder
    half-width. Large when the arms are flung out, small when drawn in -- the
    observable counterpart of the ``arm_extension`` knob in
    :func:`skating.physics.rigid_body.skater_spin_inertia`.
    """
    center = body_center(track)[:, :2]
    lw = track.landmark("left_wrist")[:, :2]
    rw = track.landmark("right_wrist")[:, :2]
    ls = track.landmark("left_shoulder")[:, :2]
    rs = track.landmark("right_shoulder")[:, :2]

    wrist_r = 0.5 * (
        np.linalg.norm(lw - center, axis=1) + np.linalg.norm(rw - center, axis=1)
    )
    shoulder_half = 0.5 * np.linalg.norm(ls - rs, axis=1)
    return wrist_r / np.clip(shoulder_half, 1e-6, None)


def inertia_proxy(track: PoseTrack) -> np.ndarray:
    """Dimensionless moment-of-inertia proxy ``sum m_i r_i^2`` per frame.

    Sums mass-weighted squared distances of shoulders (trunk), wrists (arms),
    and ankles (legs) from the spin axis. The absolute value is arbitrary, but
    its *time profile* -- falling as the arms draw in -- is directly comparable
    to the model ``I(t)``, and ``omega(t) * I(t)`` should be roughly flat
    (conserved angular momentum) through the air-borne portion.
    """
    center = body_center(track)[:, :2]

    def r2(name: str) -> np.ndarray:
        p = track.landmark(name)[:, :2]
        return np.sum((p - center) ** 2, axis=1)

    trunk = SEGMENT_MASS_FRACTION["trunk"] * 0.5 * (
        r2("left_shoulder") + r2("right_shoulder")
    )
    arms = SEGMENT_MASS_FRACTION["arm"] * (r2("left_wrist") + r2("right_wrist"))
    legs = SEGMENT_MASS_FRACTION["leg"] * (r2("left_ankle") + r2("right_ankle"))
    legs = np.nan_to_num(legs)  # ankles may be occluded
    return trunk + arms + legs


def _moving_average(x: np.ndarray, w: int) -> np.ndarray:
    if w <= 1:
        return x
    pad = w // 2
    # Edge-pad so the boundaries are not dragged toward zero by the convolution
    # (zero-padding would create huge spurious rotation rates at the clip ends).
    xp = np.pad(x, pad, mode="edge")
    kernel = np.ones(w) / w
    return np.convolve(xp, kernel, mode="valid")[: x.size]
