"""
Example 1 -- The falling cat: reorientation with zero angular momentum.

Runs the planar two-body model through one bend-and-counter-twist cycle and
shows that the body nets a real rotation even though (a) it carries no angular
momentum and (b) it returns to its exact starting shape. Then it verifies the
"gauge theory" bookkeeping: the net rotation computed by walking the loop (line
integral of the connection) equals the curvature flux through the loop
(Green's theorem). That equality *is* the falling-cat theorem, checked numerically.

Run:  python examples/01_falling_cat_reorientation.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from skating.sim import FallingCat

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)


def main() -> None:
    cat = FallingCat(bend=np.pi / 2, i_out=1.2, i_in=0.35, i_rear=1.0)

    net_line = cat.net_rotation()
    net_area = cat.net_rotation_from_curvature()
    print("Net reorientation, one shape cycle, L = 0")
    print(f"  line integral  (do the move):   {np.degrees(net_line):7.2f} deg")
    print(f"  curvature flux (Green's thm):   {np.degrees(net_area):7.2f} deg")
    print(f"  agreement (|line - area|):      {abs(net_line - net_area):.2e} rad")

    traj = cat.trajectory()
    maxL = np.max(np.abs(traj["total_angular_momentum"]))
    print(f"  max |total angular momentum|:   {maxL:.2e}  (should be ~0)")

    # ---- figure ----
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

    # shape-space loop, colored by progress
    psi = traj["psi"]
    iu = traj["i_upper"]
    s = np.linspace(0, 1, psi.size)
    ax[0].scatter(np.degrees(psi), iu, c=s, cmap="viridis", s=6)
    ax[0].set_xlabel(r"relative twist  $\psi$  (deg)")
    ax[0].set_ylabel(r"upper-body inertia  $I_U$")
    ax[0].set_title("Loop in shape space\n(area enclosed = net rotation)")

    # orientations of the two halves through the maneuver
    k = np.arange(psi.size)
    ax[1].plot(k, np.degrees(traj["theta_upper"]), label="upper body (torso)")
    ax[1].plot(k, np.degrees(traj["theta_lower"]), label="lower body (hips/legs)")
    ax[1].axhline(np.degrees(net_line), ls="--", c="gray",
                  label=f"net torso = {np.degrees(net_line):.0f} deg")
    ax[1].set_xlabel("maneuver step")
    ax[1].set_ylabel("absolute orientation (deg)")
    ax[1].set_title("Both halves move; the body reorients")
    ax[1].legend(fontsize=8)

    fig.tight_layout()
    path = os.path.join(OUT, "01_falling_cat.png")
    fig.savefig(path, dpi=130)
    print(f"\nsaved {path}")


if __name__ == "__main__":
    main()
