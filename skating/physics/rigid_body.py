"""
Rigid-body quantities for a skater spinning about a vertical axis.

Everything here is deliberately simple and *honest*: closed-form moments of
inertia for rods and cylinders, composed into a crude whole-body model whose
only free parameter is how far the arms are extended. The point is not an
anatomically exact inertia tensor -- it is a transparent model in which the
air-borne physics (``L`` conserved, ``omega = L / I``) is exactly right.

Units are SI (kg, m, kg*m^2, rad/s) throughout.
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Primitive moments of inertia (about an axis through the center of mass)
# ---------------------------------------------------------------------------


def rod_inertia(mass: float, length: float, axis: str = "perp_center") -> float:
    """Moment of inertia of a thin uniform rod.

    Parameters
    ----------
    mass, length
        Rod mass (kg) and length (m).
    axis
        ``"perp_center"`` -> axis perpendicular to the rod through its center
        (I = m L^2 / 12); ``"perp_end"`` -> through one end (I = m L^2 / 3).
    """
    if axis == "perp_center":
        return mass * length**2 / 12.0
    if axis == "perp_end":
        return mass * length**2 / 3.0
    raise ValueError(f"unknown axis {axis!r}")


def cylinder_inertia(mass: float, radius: float) -> float:
    """Moment of inertia of a solid cylinder about its symmetry (long) axis."""
    return 0.5 * mass * radius**2


def point_mass_inertia(mass: float, distance: float) -> float:
    """Parallel-axis contribution of a point mass at ``distance`` from the axis."""
    return mass * distance**2


# ---------------------------------------------------------------------------
# A whole-body spin model parametrized by arm extension
# ---------------------------------------------------------------------------


def skater_spin_inertia(
    arm_extension: float,
    torso_mass: float = 45.0,
    torso_radius: float = 0.15,
    arm_mass: float = 3.5,
    arm_length: float = 0.65,
    shoulder_offset: float = 0.18,
) -> float:
    """Moment of inertia about the vertical spin axis as a function of arm pose.

    ``arm_extension`` in ``[0, 1]`` linearly interpolates each arm from fully
    tucked against the torso (``0``) to fully abducted / horizontal (``1``).
    This single knob is what a skater actually controls to spin faster or
    slower, so it is the natural handle for the "pull in to accelerate" effect.

    The model is: a solid cylinder torso plus two rods (arms) whose center of
    mass swings out to ``shoulder_offset + arm_extension * arm_length / 2`` and
    whose own spin inertia is added via the parallel-axis theorem.
    """
    if not 0.0 <= arm_extension <= 1.0:
        raise ValueError("arm_extension must lie in [0, 1]")

    i_torso = cylinder_inertia(torso_mass, torso_radius)

    # Each arm: its CM distance from the spin axis grows with extension.
    cm_distance = shoulder_offset + arm_extension * (arm_length / 2.0)
    i_arm_cm = rod_inertia(arm_mass, arm_length, axis="perp_center")
    # Only the component of arm length that lies perpendicular to the spin axis
    # contributes to the swing-out radius; tucked arms lie nearly vertical.
    i_arm = i_arm_cm * arm_extension + point_mass_inertia(arm_mass, cm_distance)

    return i_torso + 2.0 * i_arm


# ---------------------------------------------------------------------------
# Airborne kinematics: L is conserved, so omega follows I
# ---------------------------------------------------------------------------


def angular_velocity_from_L(angular_momentum: float, inertia: np.ndarray | float):
    """omega = L / I. Works on scalars or arrays of I(t)."""
    return angular_momentum / np.asarray(inertia, dtype=float)


def rotation_angle(times: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """Cumulative rotation angle theta(t) = integral of omega dt (trapezoid)."""
    times = np.asarray(times, dtype=float)
    omega = np.asarray(omega, dtype=float)
    theta = np.zeros_like(times)
    if times.size > 1:
        dt = np.diff(times)
        incr = 0.5 * (omega[:-1] + omega[1:]) * dt
        theta[1:] = np.cumsum(incr)
    return theta


def revolutions(theta: np.ndarray) -> np.ndarray:
    """Convert an angle track (rad) to revolutions."""
    return np.asarray(theta, dtype=float) / (2.0 * np.pi)
