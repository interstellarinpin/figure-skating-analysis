"""
Example 2 -- A jump = dynamic spin + geometric snap.

Simulates one airborne phase of a triple-ish jump and separates the rotation
into its two physical contributions:

  * dynamic phase  -- omega = L / I(t): you spin faster because you pulled in;
  * geometric phase -- the holonomy of the shape change: the "snap" you'd get
    even with no angular momentum, from opening the upper body before the tap
    and checking it as the arms come in.

The plot shows I(t) falling, the two omega contributions, and the two angle
tracks adding up to the total rotation.

Run:  python examples/02_jump_two_phases.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from skating.physics.jump import JumpConfig, simulate_jump, summarize

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)


def main() -> None:
    cfg = JumpConfig()
    r = simulate_jump(cfg)
    s = summarize(r)

    print("Airborne phase summary")
    print(f"  flight time:            {cfg.flight_time:.2f} s")
    print(f"  peak spin:              {s['peak_rpm']:.0f} rpm")
    print(f"  revolutions (dynamic):  {s['revs_dynamic']:.2f}")
    print(f"  revolutions (geometric):{s['revs_geometric']:.2f}  <- the snap")
    print(f"  revolutions (total):    {s['revs_total']:.2f}")

    t = r["time"]
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))

    ax[0].plot(t, r["inertia"], color="tab:blue")
    ax[0].set_xlabel("time (s)")
    ax[0].set_ylabel(r"moment of inertia $I(t)$")
    ax[0].set_title("Arms draw in: $I$ falls")

    ax[1].plot(t, r["omega_dynamic"], label=r"dynamic  $L/I$")
    ax[1].plot(t, r["omega_geometric"], label="geometric (snap)")
    ax[1].set_xlabel("time (s)")
    ax[1].set_ylabel(r"$\omega$ (rad/s)")
    ax[1].set_title("Rotation rate, by source")
    ax[1].legend(fontsize=8)

    import numpy as np

    ax[2].plot(t, r["theta_dynamic"] / (2 * np.pi), label="dynamic")
    ax[2].plot(t, r["theta_geometric"] / (2 * np.pi), label="geometric")
    ax[2].plot(t, r["theta_total"] / (2 * np.pi), "k--", label="total")
    ax[2].set_xlabel("time (s)")
    ax[2].set_ylabel("revolutions")
    ax[2].set_title("Accumulated rotation")
    ax[2].legend(fontsize=8)

    fig.tight_layout()
    path = os.path.join(OUT, "02_jump_two_phases.png")
    fig.savefig(path, dpi=130)
    print(f"\nsaved {path}")


if __name__ == "__main__":
    main()
