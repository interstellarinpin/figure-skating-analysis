# Interactive demo (`web/`)

A single self-contained page — **Jump Physics Lab** — that animates the physics
from `skating/physics`: a top-down skater whose airborne rotation is a
**dynamic spin** (ω = L/I) plus the **geometric snap**, with a separate
zero-angular-momentum falling-cat reorientation demo. All controls update a live
revolutions chart.

The physics in the page is a faithful JavaScript port of
[`skating/physics/jump.py`](../skating/physics/jump.py) and
[`skating/physics/geometric_phase.py`](../skating/physics/geometric_phase.py):
at the defaults it reproduces the library's numbers (≈3.68 total revolutions =
3.65 dynamic + 0.03 snap; the cat reorients −25.8°, line integral = curvature
flux).

## View it

It's one file with no dependencies — just open it:

```bash
open web/index.html        # macOS
```

or drag `web/index.html` onto any browser.

## Deploy it (optional)

Because it's static and self-contained, it hosts anywhere with zero config:

- **GitHub Pages** — Settings → Pages → deploy from `main`, `/web` (or move the
  file to the repo root). No build step.
- **Vercel / Netlify** — import the repo; set the output/root to `web/`. No
  framework, no build command.

The Python package stays the source of truth; this page mirrors it for viewing.
