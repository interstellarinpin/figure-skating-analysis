# The gauge theory of a figure-skating jump

*Why opening the upper body before the tap makes the lower body snap into line.*

---

## 1. The puzzle

Watch a clean triple jump in slow motion. In the last instant before the tap,
the skater **opens the upper body** — chest and leading shoulder rotate open,
away from the direction of the jump. Then, almost without a visible effort, the
**lower body snaps into alignment** and the whole body screws into a tight,
fast, vertical rotation. Coaches describe the feeling as the rotation
"happening to you" rather than being forced. With enough speed, flow, and a
long, stretched body, the turn feels *natural* — effortless.

Two things are worth separating here:

1. **Why you spin faster when you pull in.** This is the familiar one — angular
   momentum is conserved in the air, so shrinking your moment of inertia speeds
   you up. Every physics class covers it.
2. **Why the lower body "snaps" when the upper body opens.** This is the
   interesting one, and it is *not* the same effect. It is a **shape-change
   reorientation**: a rotation produced by reconfiguring the body, not by
   spending angular momentum. It is the same trick a **falling cat** uses to
   land on its feet with zero angular momentum.

The claim of this project is that the second effect is best understood as a
**geometric phase** — the *holonomy of a connection on the space of body
shapes* — exactly as in Shapere and Wilczek's and Montgomery's "gauge theory of
the falling cat." This document builds that picture from the ground up and ties
each step to code you can run.

---

## 2. The falling cat, and what it is really doing

Drop a cat upside-down (gently, from a safe height, over a cushion — this is a
thought experiment). It has **no angular momentum**: nothing gave it any, and
gravity, acting through the center of mass, exerts **no torque** about the
center of mass. Angular momentum is conserved, and it is zero the whole way
down. And yet the cat rotates ~180° and lands on its feet.

How? Not by "pushing off the air." The cat **bends at the waist** and
**counter-rotates** its front and rear halves, with the two halves held at
different effective moments of inertia (front tucked while rear is extended,
then vice versa). Over one cycle of this bend-and-twist, the two counter-
rotations **do not cancel**, and the body nets a real rotation. Then it
straightens out, having turned over, with its angular momentum still exactly
zero.

The key realization (Kane & Scher 1969; Shapere & Wilczek 1987; Montgomery
1990; Iwai) is that **the net rotation depends only on the *path the shape
takes*, not on how fast the cat moves along it.** Do the maneuver slowly or
quickly — same reorientation. That path-dependence-but-not-rate-dependence is
the signature of a **geometric phase**, and it is governed by a **gauge
connection** on shape space.

---

## 3. The gauge-theory picture, in one page

Split the description of the body into two kinds of variables:

- **Shape variables** — the *internal* configuration: joint angles, how tucked
  the arms are, the bend between upper and lower body. Call the space of all
  shapes the **shape space** $M$.
- **Orientation variable** — the overall *rotation* of the body in space. Call
  it $\theta$ (in 3-D it is an element of the rotation group $SO(3)$; for a
  planar caricature it is a single angle).

Physically, orientation is not a free, independent coordinate: the law
"angular momentum is conserved" **ties how the body turns to how its shape
changes.** For zero angular momentum, that tie is a linear relation between the
orientation rate and the shape rate:

$$
\dot\theta \;=\; -\,A(\text{shape})\,\cdot\,\dot{(\text{shape})}.
$$

The object $A$ is a **connection one-form** on shape space — a *gauge field*.
It is the exact analogue of the vector potential in electromagnetism, or the
Christoffel connection in general relativity: it tells you how the "fiber"
(here, the body's orientation) must be carried along as you move through the
base space (here, the shapes).

Two facts make this powerful:

- **Holonomy = net rotation.** Take the body through a **closed loop** in shape
  space (start and end in the *same shape*). The net reorientation is the line
  integral of the connection around the loop:
  $$
  \Delta\theta \;=\; -\oint_{\text{loop}} A .
  $$
  This is generally **nonzero** — that nonzero value is the geometric phase /
  holonomy. The cat lands on its feet because its bend-and-twist traces a loop
  with nonzero holonomy.

- **Curvature = local "twisting efficiency."** By Stokes' theorem the loop
  integral equals the flux of the connection's **curvature** $F = dA$ through
  any surface the loop bounds:
  $$
  \Delta\theta \;=\; -\iint_{\text{area}} F .
  $$
  Where the curvature is large, small wiggles of shape buy a lot of rotation.

This is the whole content of the "gauge theory of the falling cat": **physical
reorientation is the holonomy of a gauge field over the space of shapes.**

---

## 4. The honest minimal model (and the code)

A planar two-body model captures all of the above with nothing to hide. Take an
**upper body** $U$ (torso + arms) and a **lower body** $L$ (hips + legs) sharing
the vertical spin axis. Internally the skater controls:

- the **relative twist** $\psi = \theta_U - \theta_L$, and
- the **upper-body inertia** $I_U$ (arms out → large; arms in → small).

Zero total angular momentum is the single constraint

$$
I_U\,\dot\theta_U + I_L\,\dot\theta_L = 0 .
$$

Eliminate $\theta_L$ using $\dot\psi = \dot\theta_U - \dot\theta_L$:

$$
\boxed{\;\dot\theta_U \;=\; c(I_U, I_L)\,\dot\psi, \qquad
c = \frac{I_L}{I_U + I_L}\;}
$$

So the connection is $A = c\,d\psi$, with a single component $c\in(0,1)$. Read
it physically:

- **Arms out** ($I_U$ large) → $c$ **small**: twisting barely moves the torso;
  it mostly swings the lighter lower body around. *This is the wind-up / open.*
- **Arms in** ($I_U$ small) → $c$ **near 1**: the same twist now turns the
  **torso itself**. *This is the snap.*

Now the maneuver. Trace a **rectangular loop** in the shape space $(\psi, I_U)$:

| leg | motion | effect on torso |
|----|--------|-----------------|
| 1. **open / wind up** | twist $\psi:0\to\Psi$ with arms **out** | torso barely turns ($c$ small) |
| 2. **pull in** | $I_U:\text{out}\to\text{in}$ at fixed $\psi$ | no torso turn ($d\psi=0$) |
| 3. **snap** | untwist $\psi:\Psi\to 0$ with arms **in** | torso turns a lot ($c$ near 1) |
| 4. **reset** | $I_U:\text{in}\to\text{out}$ at $\psi=0$ | no torso turn |

The net torso rotation is

$$
\Delta\theta_U = \oint c\,d\psi
= c_{\text{out}}\,\Psi \;-\; c_{\text{in}}\,\Psi
= (c_{\text{out}} - c_{\text{in}})\,\Psi \neq 0 .
$$

Start and end shapes are identical, angular momentum was zero throughout — and
the body reoriented. **That is the snap, and it is a geometric phase.**

Legs 2 and 4 are the quiet, decisive ones: they rotate the torso by nothing on
their own, but they are what makes the loop *enclose area* in shape space, and
therefore what makes $\Delta\theta_U$ nonzero. In skating language: the snap
only pays off because you **change the arm configuration between the open and
the check**. Open with the arms, check with them in.

### Run it

```python
from skating.sim import FallingCat
import numpy as np

cat = FallingCat(bend=np.pi/2, i_out=1.2, i_in=0.35, i_rear=1.0)
print(np.degrees(cat.net_rotation()))              # do the move
print(np.degrees(cat.net_rotation_from_curvature()))  # curvature flux, Stokes
```

Both numbers agree — the second is the surface integral of $F = dA$ — which is
the falling-cat theorem checked numerically. See
[`skating/physics/geometric_phase.py`](../../skating/physics/geometric_phase.py)
and `examples/01_falling_cat_reorientation.py`.

---

## 5. A real jump is dynamic phase + geometric phase

A skater is **not** a zero-angular-momentum system. At takeoff the toe pick and
edge rake a definite angular momentum $L$ off the ice, and *that* $L$ is
conserved in the air. So the airborne rotation splits exactly into two pieces:

$$
\theta_{\text{air}}(t) \;=\;
\underbrace{\int_0^{t}\frac{L}{I(\tau)}\,d\tau}_{\textbf{dynamic phase}}
\;+\;
\underbrace{\Big(-\!\!\int_{\text{shape path}} A\Big)}_{\textbf{geometric phase}} .
$$

- The **dynamic phase** is the ordinary spin: $\omega = L/I$. Pull the arms in,
  $I$ drops, $\omega$ rises. A triple is *mostly* this term.
- The **geometric phase** is the snap — the holonomy of §4 — layered on top. It
  is there even with $L=0$; it is the part that "happens to you."

For a triple, the dynamic term buys you your ~3 revolutions and the geometric
term is a smaller contribution — but a *decisive* one for timing and feel,
because it is what aligns the lower body **early**, before the fast spin has to
be held. Open the upper body before the tap; by the time the arms are in, the
connection has already swung the lower body into line, and the dynamic spin
then runs clean and tight.

### Run it

```python
from skating.physics.jump import JumpConfig, simulate_jump, summarize
print(summarize(simulate_jump(JumpConfig())))
# -> revs_dynamic, revs_geometric (the snap), revs_total, peak_rpm
```

See [`skating/physics/jump.py`](../../skating/physics/jump.py) and
`examples/02_jump_two_phases.py`.

---

## 6. Why speed, flow, and a stretched body matter

The gauge picture explains the coaching cues that otherwise sound like folklore:

- **Speed and flow → angular momentum $L$.** More horizontal speed converted at
  the edge/toe means more $L$ banked at takeoff, so the *dynamic* term is larger
  and the skater does not have to force rotation. Flow keeps the takeoff on a
  clean curved edge so that conversion is efficient and the axis is vertical.

- **A long, stretched body → a clean axis and a big inertia swing.** Stretching
  tall aligns the principal axis with the rotation axis (less wobble / off-axis
  precession, which the simple model ignores but which wrecks real jumps). It
  also *maximizes the range* of $I_U$ between arms-out and arms-in — and from
  §4, the geometric snap scales with $(c_{\text{out}}-c_{\text{in}})$, i.e. with
  how much the inertia changes between the open and the check. A collapsed,
  short body has a small inertia swing and therefore a weak snap.

- **Timing: open *before* the tap.** The loop in shape space must have the open
  (arms out) and the check (arms in) on *opposite* legs. Opening the upper body
  early, while still extended, and checking as the arms come in is exactly the
  area-enclosing order. Open late, or open and check in the same configuration,
  and the loop collapses — no enclosed area, no holonomy, no snap.

- **"Natural feel" = rate independence.** A geometric phase depends on the shape
  *path*, not the speed along it. That is precisely why a well-timed jump feels
  effortless and repeatable: within limits, doing the maneuver a little faster
  or slower gives the *same* reorientation. The feel is a mathematical property,
  not a mood.

**Direction and sequence (what the video actually shows).** Most skaters rotate
**counterclockwise** — roughly 90% by every count, and jumps for the other ~10%
are just the mirror image. And the sequence is **upper body first, lower body
follows**: coaching sources are consistent that "the upper body rotates against
the hips... the arms drive the turn," with the hips and free leg catching up in
the air. So the picture is: the upper body leads the rotation and opens ahead;
the lower body then snaps into line as everything draws tight. The two-body
model above is deliberately direction-agnostic (the sign of the twist `ψ` is a
convention) — it captures the *magnitude* of the geometric effect and the
open-then-snap *structure*, while the exact 3-D direction of the snap is a
refinement a full rigid-body model would pin down.

---

## 7. What is honest here, and what is a caricature

This project aims to be physically correct about the *mechanism* while being
upfront about the modeling:

- ✔ **Correct:** angular momentum is conserved in the air; $\omega = L/I$; a
  cyclic shape change at $L=0$ produces net reorientation equal to the holonomy
  of a connection on shape space; line integral = curvature flux (Stokes).
- ✔ **Correct in spirit, simplified in form:** the two-body planar model is a
  genuine instance of the general theory, but a jump is 3-D with a full inertia
  *tensor*, off-axis components, and air that is not quite negligible. The
  decomposition into dynamic + geometric phase is exact for an axisymmetric
  spin with slowly reconfiguring shape; real jumps add precession and tilt.
- ✘ **Not claimed:** that a skater has zero angular momentum (they do not), or
  that the snap alone produces the revolutions (it does not — the dynamic term
  dominates the *count*; the geometric term dominates the *alignment and feel*).

The right one-sentence summary: **the skater's "open then snap" is the same
geometric-phase reorientation as the falling cat, running on top of a real,
conserved spin.**

---

## 8. References

- A. Shapere and F. Wilczek, *Geometry of self-propulsion at low Reynolds
  number* and *Gauge kinematics of deformable bodies*, J. Fluid Mech. /
  Am. J. Phys. (1987–89). — the gauge formulation of shape-change locomotion.
- R. Montgomery, *Gauge theory of the falling cat*, in *Dynamics and Control of
  Mechanical Systems* (1991). — the connection/holonomy account this doc follows.
- T. R. Kane and M. P. Scher, *A dynamical explanation of the falling cat
  phenomenon*, Int. J. Solids Structures 5 (1969). — the two-cylinder model.
- J. E. Marsden, *Geometric foundations of motion and control* (1997); Marsden &
  Ratiu, *Introduction to Mechanics and Symmetry*. — reduction and connections.
- J. Wisdom, *Swimming in spacetime* (2003). — same geometric-phase idea for
  reorientation/translation via cyclic shape change.

See also the project [roadmap](../roadmap.md) for where video analysis,
simulation, and planning plug into this picture.
