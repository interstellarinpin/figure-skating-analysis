r"""
A jump = dynamic phase + geometric phase.

A real jump is not a zero-angular-momentum maneuver: the skater rakes angular
momentum ``L`` off the ice at takeoff (toe pick / edge), and ``L`` is then
conserved in the air. So the air-borne rotation splits cleanly into two parts:

* **Dynamic phase** -- the spin you get for free from ``L``:
  ``theta_dyn(t) = integral L / I(t) dt``. Pulling the arms in shrinks ``I`` and
  spins you faster. This is the familiar part.

* **Geometric phase** -- the *extra* reorientation from changing shape, the
  holonomy of the connection on shape space (see :mod:`.geometric_phase`). This
  is the "snap": open the upper body before the tap so that, as you draw in,
  the lower body swings into alignment on its own. It would be there even with
  ``L = 0``; it rides on top of the dynamic spin.

This module layers the two so you can see their separate contributions. The
decomposition is exact for an axisymmetric spin with a slowly-reconfiguring
two-body shape; it is a faithful caricature, not a full 3-D rigid-body solve.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .geometric_phase import connection_coeff
from .rigid_body import skater_spin_inertia


@dataclass
class JumpConfig:
    """Parameters of a single airborne phase."""

    flight_time: float = 0.60            # s, time in the air (~triple jump)
    angular_momentum: float = 22.0       # kg m^2 / s, set at takeoff
    i_lower: float = 1.0                 # kg m^2, lower-body spin inertia

    # Arm-draw schedule: extension goes from arms_out to arms_in over the
    # fraction [draw_start, draw_end] of the flight.
    arm_out: float = 1.0
    arm_in: float = 0.05
    draw_start: float = 0.15
    draw_end: float = 0.55

    # Upper-body "open then check" that produces the geometric snap. The
    # relative twist psi is opened early (before the tap) and checked as the
    # arms come in, closing a loop in shape space.
    psi_open: float = 0.9                # rad, how far the upper body opens
    open_start: float = 0.0
    open_end: float = 0.20
    check_start: float = 0.20
    check_end: float = 0.50

    n_steps: int = 600


def _ramp(t: np.ndarray, t0: float, t1: float, a: float, b: float) -> np.ndarray:
    """Smooth (cosine) ramp from ``a`` to ``b`` over ``[t0, t1]``, clamped."""
    x = np.clip((t - t0) / max(t1 - t0, 1e-9), 0.0, 1.0)
    s = 0.5 - 0.5 * np.cos(np.pi * x)
    return a + (b - a) * s


def simulate_jump(cfg: JumpConfig | None = None) -> dict[str, np.ndarray]:
    """Simulate one airborne phase and return separated rotation tracks.

    Returns a dict with ``time``, the inertia ``i_upper`` / total ``inertia``,
    the dynamic, geometric, and total rotation angles (rad), and the relative
    twist ``psi``. ``theta_total = theta_dyn + theta_geo``.
    """
    cfg = cfg or JumpConfig()
    t = np.linspace(0.0, cfg.flight_time, cfg.n_steps)

    # --- shape schedule -------------------------------------------------
    extension = _ramp(t, cfg.draw_start * cfg.flight_time,
                      cfg.draw_end * cfg.flight_time, cfg.arm_out, cfg.arm_in)
    i_total = skater_spin_inertia(0.0) + (
        skater_spin_inertia(1.0) - skater_spin_inertia(0.0)
    ) * extension
    # normalize so the user-facing i_lower / L units are self-consistent
    i_total = i_total / skater_spin_inertia(1.0) * (
        cfg.i_lower + skater_spin_inertia(0.0) / skater_spin_inertia(1.0)
    )

    # upper-body inertia tracks the arms; lower body is fixed
    i_upper = i_total - cfg.i_lower
    i_upper = np.clip(i_upper, 1e-3, None)

    # Open-then-check twist profile (a loop in shape space). The upper body
    # OPENS against the spin while the arms are still out (winding the light
    # lower body forward), then CHECKS -- untwists -- as the arms draw in. By
    # the connection, the check (arms in, c near 1) drives the torso forward
    # more than the open (arms out, c small) took it back, so the net geometric
    # phase adds to the spin. psi returns to 0 => clean, checked landing.
    psi_open = _ramp(t, cfg.open_start * cfg.flight_time,
                     cfg.open_end * cfg.flight_time, 0.0, -cfg.psi_open)
    psi = psi_open + _ramp(t, cfg.check_start * cfg.flight_time,
                           cfg.check_end * cfg.flight_time, 0.0, cfg.psi_open)

    # --- dynamic phase: omega = L / I ----------------------------------
    omega_dyn = cfg.angular_momentum / i_total
    theta_dyn = _cumtrapz(t, omega_dyn)

    # --- geometric phase: holonomy of the connection along psi(t) -------
    c = connection_coeff(i_upper, cfg.i_lower)
    psi_dot = np.gradient(psi, t)
    omega_geo = c * psi_dot
    theta_geo = _cumtrapz(t, omega_geo)

    return {
        "time": t,
        "extension": extension,
        "inertia": i_total,
        "i_upper": i_upper,
        "psi": psi,
        "omega_dynamic": omega_dyn,
        "omega_geometric": omega_geo,
        "theta_dynamic": theta_dyn,
        "theta_geometric": theta_geo,
        "theta_total": theta_dyn + theta_geo,
    }


def _cumtrapz(t: np.ndarray, y: np.ndarray) -> np.ndarray:
    out = np.zeros_like(y, dtype=float)
    if t.size > 1:
        out[1:] = np.cumsum(0.5 * (y[:-1] + y[1:]) * np.diff(t))
    return out


def summarize(result: dict[str, np.ndarray]) -> dict[str, float]:
    """Human-readable totals: revolutions from each phase and overall."""
    twopi = 2.0 * np.pi
    return {
        "revs_dynamic": float(result["theta_dynamic"][-1] / twopi),
        "revs_geometric": float(result["theta_geometric"][-1] / twopi),
        "revs_total": float(result["theta_total"][-1] / twopi),
        "peak_rpm": float(np.max(result["omega_dynamic"]) * 60.0 / twopi),
    }
