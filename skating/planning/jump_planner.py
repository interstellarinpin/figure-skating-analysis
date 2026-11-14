r"""
Planning a jump: inverse-design the air-borne schedule.

Given a *goal* (how many revolutions, how much flight time, how strong a
geometric "snap"), solve for the skater's control schedule -- when to draw the
arms in and how far to open-then-check the upper body -- that reaches it. This
is the figure-skating analogue of the motion-planning layer in the robotics
work: instead of learning a policy end-to-end, we *compute* a physically valid
trajectory from a specification, and only then (optionally) use it as a target
or a demonstration.

Relation to the robopolicy / InteractVLA approach
-------------------------------------------------
The robotics project generates robot trajectories *from scratch* -- a planner /
code-agent computes every motion, rather than cloning human demos -- and stores
verified skills in a reusable library. The same pattern transfers cleanly here:

* **Skill = a parametrized jump** (the ``JumpConfig`` schedule) with pre/post
  conditions: takeoff ``L`` available, flight time, "lands with the twist
  checked" (``psi -> 0``). This mirrors a RAX-style verified skill with
  pre/post checks.
* **Planner = trajectory optimization** over the schedule parameters
  (:func:`plan_jump` below), the clear-goal-pose branch of a RoboGen-style
  method menu.
* **Library = a catalog of solved jumps** (single / double / triple, different
  axes) a higher-level agent can sequence, exactly as the VLA work sequences
  grasp -> hold -> place skills on a streaming timeline.
* **Policy learning** (flow matching, as in robopolicy) would then *fit* these
  planned trajectories, turning computed schedules into a reactive controller.

The optimizer here is intentionally small and dependency-light (SciPy if
available, a robust coordinate-descent fallback otherwise) so the planning
story is runnable, not just described.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from ..physics.jump import JumpConfig, simulate_jump, summarize


@dataclass
class JumpGoal:
    """What the planned jump should achieve."""

    target_revolutions: float = 3.0     # e.g. 3.0 for a triple
    flight_time: float = 0.60           # s, fixed by the takeoff
    angular_momentum: float = 22.0      # kg m^2 / s, available at takeoff
    snap_revolutions: float = 0.12      # desired geometric-phase contribution
    land_checked: bool = True           # require psi to return to ~0 on landing


@dataclass
class PlanResult:
    config: JumpConfig
    summary: dict
    trajectory: dict
    cost: float
    iterations: int


def _cost(cfg: JumpConfig, goal: JumpGoal) -> tuple[float, dict, dict]:
    traj = simulate_jump(cfg)
    s = summarize(traj)
    rev_err = (s["revs_total"] - goal.target_revolutions) ** 2
    snap_err = (s["revs_geometric"] - goal.snap_revolutions) ** 2
    # penalize landing with the upper body still open (unchecked twist)
    land_err = (traj["psi"][-1]) ** 2 if goal.land_checked else 0.0
    cost = rev_err + 4.0 * snap_err + 0.5 * land_err
    return cost, s, traj


# Parameters we are allowed to tune, with bounds.
_FREE = {
    "arm_in": (0.02, 0.30),
    "draw_start": (0.02, 0.40),
    "draw_end": (0.40, 0.80),
    "psi_open": (0.0, 1.6),
    "check_end": (0.30, 0.70),
}


def plan_jump(goal: JumpGoal | None = None, seed: int = 0) -> PlanResult:
    """Solve for a ``JumpConfig`` that meets ``goal``.

    Tries SciPy's L-BFGS-B; if SciPy is absent, falls back to a bounded random
    + coordinate-descent search. Returns the best config, its summary, the
    simulated trajectory, the final cost, and the iteration count.
    """
    goal = goal or JumpGoal()
    base = JumpConfig(
        flight_time=goal.flight_time,
        angular_momentum=goal.angular_momentum,
    )
    keys = list(_FREE)
    lo = np.array([_FREE[k][0] for k in keys])
    hi = np.array([_FREE[k][1] for k in keys])
    x0 = np.array([getattr(base, k) for k in keys])
    x0 = np.clip(x0, lo, hi)

    def vec_to_cfg(x: np.ndarray) -> JumpConfig:
        return replace(base, **{k: float(v) for k, v in zip(keys, x)})

    def f(x: np.ndarray) -> float:
        return _cost(vec_to_cfg(np.clip(x, lo, hi)), goal)[0]

    iters = 0
    try:
        from scipy.optimize import minimize  # type: ignore

        res = minimize(
            f, x0, method="L-BFGS-B",
            bounds=list(zip(lo, hi)),
            options={"maxiter": 200},
        )
        best_x = res.x
        iters = int(res.nit)
    except Exception:  # pragma: no cover - SciPy optional / numerical fallback
        best_x, iters = _coordinate_descent(f, x0, lo, hi, seed=seed)

    best_cfg = vec_to_cfg(np.clip(best_x, lo, hi))
    cost, summary, traj = _cost(best_cfg, goal)
    return PlanResult(config=best_cfg, summary=summary, trajectory=traj,
                      cost=cost, iterations=iters)


def _coordinate_descent(f, x0, lo, hi, seed=0, rounds=40):
    rng = np.random.default_rng(seed)
    x = x0.copy()
    best = f(x)
    iters = 0
    # a few random restarts, then local coordinate refinement
    for _ in range(12):
        cand = lo + rng.random(x.size) * (hi - lo)
        c = f(cand)
        iters += 1
        if c < best:
            best, x = c, cand
    step = 0.25 * (hi - lo)
    for _ in range(rounds):
        improved = False
        for i in range(x.size):
            for sign in (+1.0, -1.0):
                trial = x.copy()
                trial[i] = np.clip(trial[i] + sign * step[i], lo[i], hi[i])
                c = f(trial)
                iters += 1
                if c < best:
                    best, x, improved = c, trial, True
        if not improved:
            step *= 0.5
    return x, iters
