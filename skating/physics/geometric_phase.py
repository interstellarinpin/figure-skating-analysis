r"""
Geometric phase of a mid-air reorientation (the "falling cat", in a plane).

Why this module exists
----------------------
A falling cat with **zero** total angular momentum still lands on its feet.
It does so by changing *shape*: it bends and counter-rotates its front and
rear halves. The net reorientation after one cycle of shape change is a
*geometric phase* -- the holonomy of a connection on the space of body shapes.
This is the content of the "gauge theory of the falling cat" (Shapere &
Wilczek; Montgomery; Iwai): physical rotation is a gauge field over shape space.

A figure skater's "open the upper body, let the lower body snap into line"
is the same move. The skater does carry nonzero angular momentum (they grab
it off the ice), but the *snap* -- the part that is not just "spinning faster
because you pulled your arms in" -- is exactly this shape-change reorientation.
This module isolates that part in the cleanest honest model: two coaxial
rigid halves (upper = torso+arms, lower = hips+legs) with **L = 0**.

The model
---------
Two bodies, upper (U) and lower (L), share the spin axis. Internal muscles set
the relative twist ``psi = theta_U - theta_L`` and the upper-body inertia
``I_U`` (arms out -> large, arms in -> small). Zero total angular momentum is
the constraint

    I_U * d(theta_U)/dt + I_L * d(theta_L)/dt = 0.

Eliminating ``theta_L`` using ``d psi/dt = d theta_U/dt - d theta_L/dt`` gives
the torso's rotation rate purely in terms of the *shape* rates::

    d theta_U / dt = c(I_U, I_L) * d psi/dt,      c = I_L / (I_U + I_L).

So ``A = c dpsi`` is a **connection one-form** on shape space (coordinates
``psi`` and ``I_U``): it tells you how much the torso turns for a given shape
change. The net torso rotation over a closed loop in shape space is the line
integral of ``A`` -- the **holonomy** -- which by Green's theorem equals the
flux of the curvature ``F = dA`` through the loop. If you twist with the arms
out and untwist with the arms in, the loop encloses area in shape space and
the holonomy is nonzero: the body reorients with no angular momentum at all.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# NumPy 2.0 renamed np.trapz -> np.trapezoid (and later removed np.trapz).
try:
    _trapezoid = np.trapezoid  # NumPy >= 2.0
except AttributeError:  # pragma: no cover - NumPy < 2.0
    _trapezoid = np.trapz

# ---------------------------------------------------------------------------
# The connection one-form A = c(I_U, I_L) dpsi
# ---------------------------------------------------------------------------


def connection_coeff(i_upper: float, i_lower: float) -> float:
    """``c = I_L / (I_U + I_L)``: torso rotation per unit relative twist.

    This is the single nonzero component of the mechanical connection for the
    two-body zero-angular-momentum model. ``c`` ranges over ``(0, 1)``:

    * arms out, ``I_U`` large  -> ``c`` small: twisting barely moves the torso,
      it mostly swings the light lower body (the wind-up).
    * arms in,  ``I_U`` small  -> ``c`` near 1: the same twist now turns the
      torso itself (the snap).
    """
    return i_lower / (i_upper + i_lower)


def torso_rate(psi_dot: float, i_upper: float, i_lower: float) -> float:
    """``d theta_U/dt`` for zero total angular momentum given twist rate ``psi_dot``."""
    return connection_coeff(i_upper, i_lower) * psi_dot


def lower_rate(psi_dot: float, i_upper: float, i_lower: float) -> float:
    """``d theta_L/dt`` for zero total angular momentum (equal and opposite flux)."""
    return -i_upper / (i_upper + i_lower) * psi_dot


# ---------------------------------------------------------------------------
# A closed loop in shape space, and its holonomy computed two independent ways
# ---------------------------------------------------------------------------


@dataclass
class ShapeLoop:
    """A rectangular loop in ``(psi, I_U)`` shape space -- the cat's maneuver.

    The four legs are the archetypal reorientation cycle:

    1. **wind up** -- twist ``psi: 0 -> psi_max`` with arms out (``I_U = i_out``);
    2. **pull in** -- ``I_U: i_out -> i_in`` at fixed ``psi`` (no torso rotation);
    3. **snap**    -- untwist ``psi: psi_max -> 0`` with arms in (``I_U = i_in``);
    4. **reset**   -- ``I_U: i_in -> i_out`` at ``psi = 0`` (no torso rotation).

    Legs 2 and 4 change only ``I_U`` (``dpsi = 0``), so they contribute nothing
    to ``theta_U`` directly -- yet they are what makes the loop enclose area,
    and therefore what makes the *net* reorientation nonzero.
    """

    psi_max: float = np.pi / 2.0
    i_out: float = 1.2
    i_in: float = 0.35
    i_lower: float = 1.0
    n_per_leg: int = 200

    def path(self) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(psi, I_U)`` samples tracing the closed loop once (CCW-ish)."""
        n = self.n_per_leg
        # leg 1: twist out
        p1 = np.linspace(0.0, self.psi_max, n)
        u1 = np.full(n, self.i_out)
        # leg 2: pull in
        p2 = np.full(n, self.psi_max)
        u2 = np.linspace(self.i_out, self.i_in, n)
        # leg 3: untwist in
        p3 = np.linspace(self.psi_max, 0.0, n)
        u3 = np.full(n, self.i_in)
        # leg 4: push back out
        p4 = np.zeros(n)
        u4 = np.linspace(self.i_in, self.i_out, n)
        psi = np.concatenate([p1, p2, p3, p4])
        i_u = np.concatenate([u1, u2, u3, u4])
        return psi, i_u


def holonomy_line_integral(loop: ShapeLoop) -> float:
    r"""Net torso rotation as the line integral ``oint A = oint c dpsi``.

    This is the "do the maneuver and read the protractor" answer: integrate the
    torso rate along the shape path. It is also, by construction, exactly the
    reorientation a forward simulation of the two-body model would produce.
    """
    psi, i_u = loop.path()
    c = connection_coeff(i_u, loop.i_lower)
    dpsi = np.diff(psi)
    c_mid = 0.5 * (c[:-1] + c[1:])
    return float(np.sum(c_mid * dpsi))


def holonomy_area_integral(loop: ShapeLoop, n_grid: int = 400) -> float:
    r"""Same holonomy as the curvature flux ``int int F`` (Green's theorem).

    With ``A = c dpsi`` (no ``dI_U`` component), Green's theorem gives

        oint c dpsi = - int int (d c / d I_U) dpsi dI_U

    over the rectangle ``psi in [0, psi_max]``, ``I_U in [i_in, i_out]``. Here
    ``d c / d I_U = - I_L / (I_U + I_L)^2``, so the integrand (the **curvature**)
    is ``I_L / (I_U + I_L)^2``. That this matches :func:`holonomy_line_integral`
    is the numerical statement that reorientation is the flux of a gauge field
    through the shape-space loop -- the falling-cat theorem, checked by hand.
    """
    psi_grid = np.linspace(0.0, loop.psi_max, n_grid)
    iu_grid = np.linspace(loop.i_in, loop.i_out, n_grid)
    PSI, IU = np.meshgrid(psi_grid, iu_grid, indexing="ij")
    curvature = loop.i_lower / (IU + loop.i_lower) ** 2  # -dc/dI_U
    # Sign: our loop traverses leg 1 (arms out) then leg 3 (arms in) with
    # opposite dpsi; the enclosed flux carries a leading minus to match it.
    flux = _trapezoid(_trapezoid(curvature, iu_grid, axis=1), psi_grid)
    return float(-flux)


def simulate_two_body(loop: ShapeLoop) -> dict[str, np.ndarray]:
    """Forward-integrate the two coaxial halves along the shape loop.

    Returns time-like tracks for ``psi``, ``I_U``, and the absolute orientations
    ``theta_U`` and ``theta_L``, plus the running total angular momentum (which
    must stay ~0). Useful for plots and as an end-to-end sanity check that the
    connection bookkeeping matches an actual integration.
    """
    psi, i_u = loop.path()
    i_l = loop.i_lower
    theta_u = np.zeros_like(psi)
    theta_l = np.zeros_like(psi)
    dpsi = np.diff(psi)
    for k in range(1, psi.size):
        iu_mid = 0.5 * (i_u[k - 1] + i_u[k])
        du_dot = connection_coeff(iu_mid, i_l) * dpsi[k - 1]
        dl_dot = -iu_mid / (iu_mid + i_l) * dpsi[k - 1]
        theta_u[k] = theta_u[k - 1] + du_dot
        theta_l[k] = theta_l[k - 1] + dl_dot
    # instantaneous total L (should be ~0 up to discretization)
    omega_u = np.gradient(theta_u)
    omega_l = np.gradient(theta_l)
    total_L = i_u * omega_u + i_l * omega_l
    return {
        "psi": psi,
        "i_upper": i_u,
        "theta_upper": theta_u,
        "theta_lower": theta_l,
        "total_angular_momentum": total_L,
    }
