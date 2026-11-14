"""
Example 3 -- Plan a jump to a specification.

Inverse-designs the airborne control schedule (when to draw the arms in, how
far to open-then-check the upper body) to hit a target number of revolutions
with a prescribed geometric "snap", landing with the twist checked. This is the
figure-skating analogue of computing a robot trajectory from a goal instead of
cloning a demonstration -- see skating/planning/jump_planner.py.

Run:  python examples/03_plan_a_jump.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from skating.planning import JumpGoal, plan_jump

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)


def main() -> None:
    goal = JumpGoal(target_revolutions=3.0, flight_time=0.60,
                    angular_momentum=22.0, snap_revolutions=0.12)
    plan = plan_jump(goal)

    c = plan.config
    print(f"Planned a {goal.target_revolutions:.0f}-revolution jump "
          f"({plan.iterations} iterations, cost {plan.cost:.2e})")
    print("  schedule:")
    print(f"    draw arms in:   {c.draw_start:.2f} -> {c.draw_end:.2f} "
          f"(of flight), to extension {c.arm_in:.2f}")
    print(f"    open upper body: psi_open = {c.psi_open:.2f} rad, "
          f"checked by {c.check_end:.2f}")
    print("  achieved:")
    for k, v in plan.summary.items():
        print(f"    {k:16s} {v:.3f}")

    r = plan.trajectory
    t = r["time"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].plot(t, r["extension"], label="arm extension")
    ax[0].plot(t, r["psi"], label=r"upper-body twist $\psi$")
    ax[0].set_xlabel("time (s)")
    ax[0].set_title("Planned control schedule")
    ax[0].legend(fontsize=8)

    import numpy as np

    ax[1].plot(t, r["theta_total"] / (2 * np.pi), "k", label="total")
    ax[1].plot(t, r["theta_geometric"] / (2 * np.pi), label="geometric (snap)")
    ax[1].axhline(goal.target_revolutions, ls="--", c="gray",
                  label=f"target {goal.target_revolutions:.0f} rev")
    ax[1].set_xlabel("time (s)")
    ax[1].set_ylabel("revolutions")
    ax[1].set_title("Achieved rotation")
    ax[1].legend(fontsize=8)

    fig.tight_layout()
    path = os.path.join(OUT, "03_plan_a_jump.png")
    fig.savefig(path, dpi=130)
    print(f"\nsaved {path}")


if __name__ == "__main__":
    main()
