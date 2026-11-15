# Figure Skating Analysis

**A physics-first toolkit for figure skating jumps** — motion planning, video
analysis, simulation, and a geometric-phase theory of *why the rotation feels
natural*.

The central idea: the "open the upper body, let the lower body snap into line"
moment of a jump is the **same reorientation trick a falling cat uses** to land
on its feet with zero angular momentum. It is a **geometric phase** — the
holonomy of a connection on the space of body shapes — exactly as in the
*gauge theory of the falling cat* (Shapere–Wilczek, Montgomery, Kane–Scher).
A real jump layers that "snap" on top of an ordinary conserved spin.

📖 **Read the theory first:**
[`docs/theory/gauge-theory-of-skating.md`](docs/theory/gauge-theory-of-skating.md)

---

## The one-paragraph physics

In the air, gravity exerts no torque about your center of mass, so **angular
momentum $L$ is conserved**. Pulling your arms in shrinks your moment of
inertia $I$, so $\omega = L/I$ rises — the familiar "spin up." But opening the
upper body and letting the lower body snap around is a *different* effect:
reorientation produced by **changing shape**, not by spending $L$. Over a closed
loop of shape change (open with the arms out, check with them in), the body
nets a real rotation — the **geometric phase** $\Delta\theta = \oint A =
\iint dA$. Speed and flow set $L$; a long, stretched body maximizes the inertia
swing that makes the snap strong; and because a geometric phase depends on the
*path* of the shape change and not its speed, a well-timed jump feels effortless
and repeatable.

$$
\theta_{\text{air}}(t)=\underbrace{\int \frac{L}{I(\tau)}\,d\tau}_{\text{dynamic: the spin}}+\underbrace{\Big(-\!\!\int_{\text{shape path}} A\Big)}_{\text{geometric: the snap}}
$$

---

## Four pillars

| Pillar | What it does | Module |
|--------|--------------|--------|
| **Physics** | Inertia, angular momentum, and the connection/holonomy that *is* the snap (with a numerical Stokes check). | [`skating/physics`](skating/physics) |
| **Simulation** | Minimal honest forward models: a planar falling cat, and a jump that separates dynamic + geometric phase. | [`skating/sim`](skating/sim) |
| **Video** | Monocular pose → azimuth, spin rate, arm-extension and inertia proxies (MediaPipe-optional; runs on arrays). | [`skating/video`](skating/video) |
| **Planning** | Inverse-design the airborne schedule to hit a target, framed as verified "skills" — the skating mirror of the robotics/VLA work. | [`skating/planning`](skating/planning) |

---

## Install

```bash
git clone <your-repo-url> "Figure Skating Analysis"
cd "Figure Skating Analysis"
python -m venv .venv && source .venv/bin/activate
pip install -e .            # core: numpy, scipy, matplotlib
pip install -e '.[video]'   # optional: mediapipe + opencv for real clips
```

Requires Python 3.10+.

## Run the examples

Each writes a figure to `examples/figures/`.

```bash
python examples/01_falling_cat_reorientation.py   # geometric phase, Stokes-checked
python examples/02_jump_two_phases.py             # dynamic spin + geometric snap
python examples/03_plan_a_jump.py                 # plan a triple to spec
python examples/04_video_kinematics.py            # (synthetic) video -> physics
python examples/05_free_floating_reorientation.py # robot falling cat: holonomy = base turn
python examples/06_cat_video_reorientation.py clip.mov  # real cat clip -> annotated video
python examples/07_skating_two_body_overlay.py clip.mp4 --mode snap  # two-body overlay on footage
```

Example 06 maps a real slow-motion righting clip onto the theory (orientation
$\theta:180^\circ\!\to\!0^\circ$ at $L=0$ via a closed loop in shape space) and
writes an **annotated video** with the phase, the live orientation dial, the
`L = 0` badge, and a tracer circling the $\psi$–$s$ shape loop drawn over the
footage. Needs a front-view clip plus `pip install imageio imageio-ffmpeg`; pass
`--no-video` to render just the figures.

Example 07 draws the demo's two-body model straight onto a real skating clip:
**blue = upper body (leads)**, **amber = lower body (barely turns, then snaps
into line)**. The on-skater glyph shows the relative twist $\psi$ — the upper
opening ahead of the near-fixed lower — with the whole-body spin ($\omega=L/I$)
shown separately so it is never confused with the twist, and a synced inset of
the real `simulate_jump` model. `--mode spin` suits a spin/jump clip, `--mode
snap` a jump-analysis clip; `--probe` dumps sample frames instead of encoding.

A 20-second taste in the REPL:

```python
import numpy as np
from skating.sim import FallingCat

cat = FallingCat(bend=np.pi/2)
print(np.degrees(cat.net_rotation()))              # reorientation, L = 0
print(np.degrees(cat.net_rotation_from_curvature()))  # same number via curvature flux
```

```python
from skating.physics.jump import JumpConfig, simulate_jump, summarize
print(summarize(simulate_jump(JumpConfig())))
# {'revs_dynamic': ..., 'revs_geometric': ...(the snap), 'revs_total': ..., 'peak_rpm': ...}
```

## Test

```bash
pip install -e '.[dev]'
pytest -q
```

The tests pin the physical claims: $\omega=L/I$, the connection bounds, the
falling-cat Stokes identity (line integral = curvature flux), zero-$L$-yet-
nonzero-rotation, and the dynamic+geometric decomposition.

---

## Repository layout

```
skating/
  physics/     rigid_body.py · geometric_phase.py · jump.py
  sim/         falling_cat.py · free_floating.py
  video/       pose.py · kinematics.py
  planning/    jump_planner.py
examples/      01..07 runnable scripts -> figures/
docs/
  theory/gauge-theory-of-skating.md   <- the core writeup
  roadmap.md
tests/         test_physics.py · test_pipeline.py
```

## How this connects to the robotics work

The planning layer deliberately mirrors the **motion-planning / VLA** approach
from the `robopolicy` / InteractVLA project: *compute* physically valid
trajectories from a goal (rather than cloning demonstrations), store them as
**verified skills** with pre/post conditions, and sequence them on a timeline.
A future milestone fits those planned trajectories with a **flow-matching
policy**, closing the loop from planning to a reactive controller. See
[`skating/planning/jump_planner.py`](skating/planning/jump_planner.py) and the
[roadmap](docs/roadmap.md).

## Status & caveats

Early, honest, and explicit about its simplifications (planar model, rough
segment masses, axisymmetric-spin decomposition). What it gets *right* is the
mechanism — see §7 of the theory doc. Contributions and corrections welcome.

## References

Montgomery, *Gauge theory of the falling cat* (1991); Shapere & Wilczek,
*Gauge kinematics of deformable bodies* (1989); Kane & Scher (1969);
Marsden & Ratiu, *Introduction to Mechanics and Symmetry*.

## License

MIT — see [LICENSE](LICENSE).
