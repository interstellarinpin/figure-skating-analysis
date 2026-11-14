"""
Example 4 -- From (synthetic) video to physics.

Builds a synthetic spin pose-track (no video or vision deps needed), then runs
the kinematics layer to recover the azimuth, the rotation rate, the arm-
extension proxy, and the moment-of-inertia proxy. As the arms draw in, I(t)
falls and omega(t) rises -- and their product (angular momentum) stays roughly
flat, exactly as conservation demands.

To run on a real clip instead:

    from skating.video import extract_pose
    track = extract_pose("my_jump.mp4")       # needs: pip install 'skating[video]'

Run:  python examples/04_video_kinematics.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from skating.video import (
    arm_extension_proxy,
    count_revolutions,
    inertia_proxy,
    rotation_rate,
)
from skating.video.pose import synthetic_spin

OUT = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT, exist_ok=True)


def main() -> None:
    track = synthetic_spin(n_frames=180, fps=60, revolutions=3.0, draw_in=True)

    revs = count_revolutions(track)
    omega = rotation_rate(track)
    ext = arm_extension_proxy(track)
    inertia = inertia_proxy(track)
    L = omega * inertia  # proxy angular momentum

    print(f"recovered revolutions: {revs:.2f}")
    print(f"peak omega:            {np.max(np.abs(omega)):.1f} rad/s")
    print(f"arm extension:         {ext[0]:.2f} -> {ext[-1]:.2f}")
    print(f"angular-momentum proxy drift: "
          f"{(np.std(L[10:-10]) / np.mean(np.abs(L[10:-10]))):.1%}")

    t = track.times
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    ax[0].plot(t, np.abs(omega))
    ax[0].set_title("rotation rate (rad/s)")
    ax[0].set_xlabel("time (s)")
    ax[1].plot(t, ext, label="arm extension")
    ax[1].plot(t, inertia / inertia[0], label="inertia (norm.)")
    ax[1].set_title("arms draw in, I falls")
    ax[1].set_xlabel("time (s)")
    ax[1].legend(fontsize=8)
    ax[2].plot(t, np.abs(L) / np.mean(np.abs(L[10:-10])))
    ax[2].axhline(1.0, ls="--", c="gray")
    ax[2].set_title(r"$\omega\, I$  (angular momentum proxy)")
    ax[2].set_xlabel("time (s)")
    ax[2].set_ylim(0, 2)

    fig.tight_layout()
    path = os.path.join(OUT, "04_video_kinematics.png")
    fig.savefig(path, dpi=130)
    print(f"\nsaved {path}")


if __name__ == "__main__":
    main()
