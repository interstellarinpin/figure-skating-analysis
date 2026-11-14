# Roadmap

How the four pillars fit together, and what is built vs. planned.

## The through-line

Everything points at one picture (see
[the theory writeup](theory/gauge-theory-of-skating.md)): a jump's airborne
rotation is a **dynamic phase** ($\omega = L/I$) plus a **geometric phase**
(the holonomy of a connection on shape space — the "snap," the same trick a
falling cat uses). Each pillar below either *measures*, *reproduces*, or
*designs* against that picture.

```
   video ----measure----> I(t), omega(t), psi(t) on real jumps
     |                              |
     v                              v
  physics  <--validate--  does omega*I stay flat? does the snap appear?
     |
     v
   sim  ----reproduce---> dynamic + geometric phase of a full jump
     |
     v
 planning --design------> schedule (when to pull in / open-then-check)
     |                     that hits a target, as verified "skills"
     v
 (future) policy learning (flow matching, cf. robopolicy) fits the plans
```

## Status

| Pillar | Module | Built | Next |
|--------|--------|-------|------|
| Physics | `skating.physics` | ✅ inertia, connection, holonomy (Stokes-checked), jump decomposition | full 3-D inertia tensor; off-axis tilt/precession |
| Simulation | `skating.sim` | ✅ planar falling cat; two-phase jump | 3-link torso/arms/legs; MuJoCo rigid-body cross-check |
| Video | `skating.video` | ✅ pose scaffold (MediaPipe-optional), kinematics on arrays, synthetic spin | calibrate axis from real clips; multi-view depth; jump detection |
| Planning | `skating.planning` | ✅ trajectory optimization to a goal; SciPy + fallback | skill library of jumps; sequence on a timeline; export as demos |

## Milestones

1. **M1 — Physics + examples (done).** Connection/holonomy with a numerical
   Stokes check; dynamic+geometric jump decomposition; four runnable examples
   with figures; tests pinning every physical claim.
2. **M2 — Real video.** Run `extract_pose` on a few consented clips, recover
   $I(t)$ and $\omega(t)$, and show on real data that (a) $\omega I$ is roughly
   flat through the air and (b) the geometric snap is visible at the tap.
3. **M3 — Higher-fidelity sim.** Replace the planar caricature with a 3-link
   articulated body and a full inertia tensor; validate the phase decomposition
   against a rigid-body integrator (e.g. MuJoCo).
4. **M4 — Planning as skills.** Grow `plan_jump` into a small library of
   verified jump "skills" (single/double/triple, Axel/Lutz/loop entries) with
   pre/post conditions, sequence-able on a timeline — the figure-skating mirror
   of the robotics motion-planning / VLA work (see
   `skating/planning/jump_planner.py`).
5. **M5 — Policy fit (stretch).** Fit the planned trajectories with a
   flow-matching policy (as in the `robopolicy` project) to get a reactive
   controller, and compare planned vs. learned schedules.

## Non-goals (for now)

- Scoring or judging jumps.
- Anatomically exact biomechanics (segment masses are rough proxies).
- Real-time / on-ice deployment.
