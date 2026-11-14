"""Tests that pin down the physics claims the project makes."""

import numpy as np

from skating.physics.geometric_phase import (
    ShapeLoop,
    connection_coeff,
    holonomy_area_integral,
    holonomy_line_integral,
    simulate_two_body,
)
from skating.physics.jump import JumpConfig, simulate_jump
from skating.physics.rigid_body import (
    angular_velocity_from_L,
    skater_spin_inertia,
)


def test_pull_in_speeds_up_spin():
    """omega = L / I: drawing the arms in must increase the spin rate."""
    i_out = skater_spin_inertia(1.0)
    i_in = skater_spin_inertia(0.0)
    assert i_out > i_in
    L = 20.0
    assert angular_velocity_from_L(L, i_in) > angular_velocity_from_L(L, i_out)


def test_connection_coeff_bounds():
    assert 0.0 < connection_coeff(2.0, 1.0) < 1.0
    # arms in (small I_U) -> coefficient near 1 (torso turns)
    assert connection_coeff(0.01, 1.0) > connection_coeff(5.0, 1.0)


def test_holonomy_stokes_consistency():
    """Falling-cat theorem, numerically: line integral == curvature flux."""
    loop = ShapeLoop(psi_max=np.pi / 2, i_out=1.2, i_in=0.35, i_lower=1.0)
    line = holonomy_line_integral(loop)
    area = holonomy_area_integral(loop)
    assert abs(line) > 0.05  # the reorientation is real, not round-off
    assert abs(line - area) < 1e-2


def test_zero_angular_momentum_but_nonzero_rotation():
    """The two-body model reorients with ~zero total angular momentum."""
    loop = ShapeLoop(psi_max=np.pi / 2)
    traj = simulate_two_body(loop)
    # start and end shapes identical
    assert abs(traj["psi"][0] - traj["psi"][-1]) < 1e-9
    # yet the torso has a net orientation
    assert abs(traj["theta_upper"][-1]) > 0.05
    # and total angular momentum stayed near zero throughout
    assert np.max(np.abs(traj["total_angular_momentum"])) < 1e-2


def test_jump_decomposition_adds_up():
    r = simulate_jump(JumpConfig())
    total = r["theta_dynamic"] + r["theta_geometric"]
    assert np.allclose(total, r["theta_total"])
    # a real triple is mostly dynamic spin with a small geometric snap
    assert r["theta_dynamic"][-1] > r["theta_geometric"][-1] > 0.0


def test_jump_geometric_phase_closes():
    """Opening then checking the upper body returns psi to ~0 (clean landing)."""
    r = simulate_jump(JumpConfig())
    assert abs(r["psi"][-1]) < 0.05
