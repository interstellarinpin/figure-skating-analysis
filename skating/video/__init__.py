"""Monocular video -> pose -> skating kinematics."""

from .pose import PoseTrack, extract_pose, LANDMARKS
from .kinematics import (
    body_axis_angle,
    rotation_rate,
    count_revolutions,
    arm_extension_proxy,
    inertia_proxy,
)

__all__ = [
    "PoseTrack",
    "extract_pose",
    "LANDMARKS",
    "body_axis_angle",
    "rotation_rate",
    "count_revolutions",
    "arm_extension_proxy",
    "inertia_proxy",
]
