"""Tests for the video kinematics and the planner (end-to-end-ish)."""

import numpy as np

from skating.planning import JumpGoal, plan_jump
from skating.video import (
    arm_extension_proxy,
    count_revolutions,
    inertia_proxy,
    rotation_rate,
)
from skating.video.pose import synthetic_spin


def test_kinematics_recovers_revolutions():
    track = synthetic_spin(n_frames=240, fps=60, revolutions=3.0, draw_in=False)
    assert abs(count_revolutions(track) - 3.0) < 0.05


def test_arm_pull_shows_up_as_rising_omega_and_falling_inertia():
    track = synthetic_spin(n_frames=240, fps=60, revolutions=3.0, draw_in=True)
    omega = np.abs(rotation_rate(track))
    inertia = inertia_proxy(track)
    ext = arm_extension_proxy(track)
    # arms draw in over the clip
    assert ext[0] > ext[-1]
    # inertia falls, late spin is faster than early spin
    assert inertia[5] > inertia[-5]
    assert np.mean(omega[-30:]) > np.mean(omega[:30])


def test_planner_hits_target_revolutions():
    goal = JumpGoal(target_revolutions=3.0, snap_revolutions=0.1)
    plan = plan_jump(goal)
    assert abs(plan.summary["revs_total"] - 3.0) < 0.25
    # landed with the twist essentially checked
    assert abs(plan.trajectory["psi"][-1]) < 0.1
