r"""
The planar falling cat: reorientation with exactly zero angular momentum.

This wraps :mod:`skating.physics.geometric_phase` in a cat-flavored interface
so the example scripts read like the physics they illustrate. The "cat" is two
coaxial halves; one cycle of *bend-and-counter-twist* nets a body rotation
equal to the holonomy of the shape-space connection -- no angular momentum
spent, start and end shapes identical.

The same object stands in for the skater's upper/lower body during the "open
then snap" instant of a jump; only the boundary condition differs (the skater
also carries a nonzero ``L`` that this zero-``L`` model deliberately omits, so
that the geometric part is shown on its own).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..physics.geometric_phase import (
    ShapeLoop,
    holonomy_area_integral,
    holonomy_line_integral,
    simulate_two_body,
)


@dataclass
class FallingCat:
    """A two-halves zero-angular-momentum reorienter.

    Parameters mirror :class:`skating.physics.geometric_phase.ShapeLoop`:
    ``bend`` is the peak counter-twist (rad), ``i_out`` / ``i_in`` are the
    front-half moments of inertia with the limbs extended vs. tucked, and
    ``i_rear`` is the (fixed) rear-half inertia.
    """

    bend: float = np.pi / 2.0
    i_out: float = 1.2
    i_in: float = 0.35
    i_rear: float = 1.0

    def _loop(self) -> ShapeLoop:
        return ShapeLoop(
            psi_max=self.bend,
            i_out=self.i_out,
            i_in=self.i_in,
            i_lower=self.i_rear,
        )

    def net_rotation(self) -> float:
        """Net body (front-half) rotation after one shape cycle, in radians."""
        return holonomy_line_integral(self._loop())

    def net_rotation_from_curvature(self) -> float:
        """The same net rotation computed as curvature flux (Green's theorem)."""
        return holonomy_area_integral(self._loop())

    def trajectory(self) -> dict[str, np.ndarray]:
        """Full tracks (shape + both halves' orientations + total ``L``)."""
        return simulate_two_body(self._loop())


def cat_reorientation(bend: float = np.pi / 2.0, **kwargs) -> float:
    """Convenience: net reorientation (deg) for a given peak bend angle."""
    cat = FallingCat(bend=bend, **kwargs)
    return np.degrees(cat.net_rotation())
