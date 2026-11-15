r"""
Example 7 -- Two-body overlay on real skating footage.

Draws the Vercel demo's two-body model straight onto a real skating clip so the
footage and the sim line up: **blue = upper body (it leads)**, **amber/orange =
lower body (it barely turns at first, then snaps into line)**. The on-skater
glyph shows the *relative twist* psi -- the angle the upper body opens ahead of
the lower -- which is the honest early-jump picture: the skater does NOT spin the
whole body 180 deg at takeoff; the upper body twists by psi (up to ~50 deg) while
the lower stays put, and the lower only swings around as the arms draw in (the
snap, psi -> 0). The separate whole-body spin (omega = L/I) is shown only in the
synced sim inset and a small rev read-out, so it is never confused with the twist.

The twist/snap profile is taken from the real jump sim (:func:`simulate_jump`):
psi opens over the first fifth of the flight, then checks back to zero -- a closed
loop in shape space whose holonomy is the geometric "snap."

Modes:
  spin  -- a jump/spin clip; adds a whole-body-rotation read-out.
  snap  -- a jump-analysis clip; emphasises the upper-lead / lower-snap.

The clips are NOT committed (personal screen recordings; the repo ignores
*.mp4/*.mov). Point it at any single-skater front/side clip:

    python examples/07_skating_two_body_overlay.py <clip.mp4> --mode snap

Writes an annotated MP4 to examples/figures/. Use --probe to dump a few sample
PNGs instead of encoding the whole clip.

NOTE on honesty: the skater is followed by a simple motion/darkness centroid, not
true pose estimation, so the nodes sit on the torso/hips schematically rather than
rigged to real joints; and the jump window is aligned to the sim by eye. The
upper-leads / lower-snaps *relationship* is faithful; exact per-frame registration
is not a measurement.

Run:  python examples/07_skating_two_body_overlay.py clip.mp4 --mode snap
Deps: pip install imageio imageio-ffmpeg
"""

import argparse
import os

import numpy as np
import imageio

from skating.physics.jump import JumpConfig, simulate_jump, summarize

# demo colors (dark-mode variants read better over video)
BLUE = (100, 160, 255)     # --dyn : upper body, leads
ORANGE = (241, 168, 98)    # --geo : lower body, counter-rotates -> snaps
WHITE = (236, 241, 248)

PSI_PEAK = 0.9
OPEN_END_U = 0.20          # psi finishes opening by this fraction of flight
SIM = simulate_jump(JumpConfig(angular_momentum=8.0, psi_open=PSI_PEAK))
TH, PSI, IU, EXT = (SIM["theta_total"], SIM["psi"], SIM["i_upper"], SIM["extension"])
NS = TH.size
TOTAL_REV = summarize(SIM)["revs_total"]

# rot_dir sets the on-screen handedness. Image/canvas y points DOWN, so a
# positive angle renders clockwise; rot_dir = -1 draws counterclockwise -- the
# way ~90% of skaters rotate, matching the Vercel demo. Flip per clip if a
# camera angle shows the opposite apparent spin.
MODES = {
    "spin": dict(
        air=(0.22, 0.70), roi=(0.00, 1.00, 0.13, 0.80), rot_dir=-1, spin_readout=True,
        phases=[(0.00, "WIND-UP", "edge loaded, upper body wound, arms out"),
                (0.22, "TAKEOFF", "leave the ice; upper body starts to open"),
                (0.40, "UPPER LEADS", "blue twists ahead — lower barely turns"),
                (0.56, "SNAP", "arms in: lower swings into line (ψ → 0)"),
                (0.74, "CHECK / LAND", "aligned — clean checked exit")]),
    "snap": dict(
        air=(0.34, 0.74), roi=(0.00, 1.00, 0.10, 0.74), rot_dir=-1, spin_readout=False,
        phases=[(0.00, "ENTRY GLIDE", "long edge, upper body wound back"),
                (0.34, "TAKEOFF", "rake L off the ice; upper body opens first"),
                (0.50, "UPPER LEADS", "blue opens ahead by ψ — hips barely turn"),
                (0.62, "SNAP", "lower snaps up into line (ψ → 0)"),
                (0.80, "LANDING", "checked — the geometric phase is banked")]),
}


def sim_u(frac, air):
    a0, a1 = air
    return float(np.clip((frac - a0) / (a1 - a0), 0.0, 1.0))


def phase_at(frac, phases):
    i, name, rel = 0, phases[0][1], phases[0][2]
    for k, (f0, nm, rl) in enumerate(phases):
        if frac >= f0:
            i, name, rel = k, nm, rl
    return i, name, rel


def twist_split(u):
    """From the sim psi(u): how far the upper has opened and the lower caught up.

    Returns (open_mag, catch, psi_mag) in radians. The *visible* twist is
    psi_mag = open_mag - catch: the upper leads by open_mag, the lower trails
    until it swings up by catch to erase it.
    """
    idx = int(u * (NS - 1))
    amag = abs(PSI[idx])
    if u <= OPEN_END_U:
        open_mag, catch = amag, 0.0
    else:
        open_mag, catch = PSI_PEAK, PSI_PEAK - amag
    return open_mag, max(0.0, catch), amag


# ---------------------------------------------------------------------------
def font(sz, bold=True):
    from PIL import ImageFont
    try:
        import matplotlib.font_manager as fm
        p = fm.findfont("DejaVu Sans:bold" if bold else "DejaVu Sans")
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()


def track(frames, roi):
    """Follow the skater: brightest-difference-from-background AND darker-than-ice
    blob within an ROI, centroid smoothed over time. Returns [(cx, cy, r)]."""
    H, W = frames[0].shape[:2]
    x0, x1 = int(roi[0] * W), int(roi[1] * W)
    y0, y1 = int(roi[2] * H), int(roi[3] * H)
    bg = np.median(np.stack(frames[::max(1, len(frames) // 20)]), axis=0)
    cen = []
    for f in frames:
        sub = f[y0:y1, x0:x1].astype(float)
        diff = np.abs(sub - bg[y0:y1, x0:x1]).mean(2)
        gray = sub.mean(2)
        score = diff + 0.6 * (gray.max() - gray)
        mask = score > score.mean() + 1.2 * score.std()
        if mask.sum() < 30:
            cen.append(cen[-1] if cen else (W / 2, (y0 + y1) / 2, 80.0))
            continue
        ys, xs = np.where(mask)
        cen.append((xs.mean() + x0, ys.mean() + y0, np.sqrt(mask.sum()) + 40))
    cen = np.array(cen, float)
    for j in range(3):  # smooth
        cen[:, j] = np.convolve(np.pad(cen[:, j], 3, mode="edge"),
                                np.ones(7) / 7, "valid")
    return cen


def arc(draw, cx, cy, r, a0, a1, color, alpha, width):
    n = max(8, int(abs(a1 - a0) / 0.12))
    pts = [(cx + r * np.cos(a0 + (a1 - a0) * i / n),
            cy + r * np.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    draw.line(pts, fill=color + (alpha,), width=width)
    return pts


def arrowhead(draw, tip, ang, size, color, alpha=255):
    x, y = tip
    l = (x - size * np.cos(ang - 0.45), y - size * np.sin(ang - 0.45))
    r = (x - size * np.cos(ang + 0.45), y - size * np.sin(ang + 0.45))
    draw.polygon([tip, l, r], fill=color + (alpha,))


def draw_sim_panel(draw, box, u, rot_dir):
    from PIL import ImageDraw  # noqa
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=14, fill=(10, 18, 34, 205),
                           outline=(90, 120, 160, 230), width=2)
    pad = 12
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 10
    R = min(x1 - x0, y1 - y0) * 0.30
    f_t = font(max(12, int((x1 - x0) * 0.055)))
    f_s = font(max(10, int((x1 - x0) * 0.042)), bold=False)
    draw.text((x0 + pad, y0 + 8), "VERCEL SIM · two-body model", font=f_t,
              fill=(210, 225, 245, 255))
    idx = int(u * (NS - 1))
    theta, psi, iu, ext = TH[idx], PSI[idx], IU[idx], EXT[idx]
    lag = (iu / (iu + 1.0)) * abs(psi)
    dU, dL = rot_dir * theta, rot_dir * (theta - lag)
    for rr in (0.45, 0.72, 1.0):
        draw.ellipse([cx - R * rr, cy - R * rr, cx + R * rr, cy + R * rr],
                     outline=(70, 95, 130, 160), width=1)
    arc(draw, cx, cy, R * 0.92, -np.pi / 2, -np.pi / 2 - rot_dir * (theta % (2 * np.pi)),
        BLUE, 70, 4)
    # lower (orange): hip bar + legs
    vx, vy = np.cos(dL), np.sin(dL); px, py = -vy, vx
    draw.line([cx + px * R * 0.42, cy + py * R * 0.42,
               cx - px * R * 0.42, cy - py * R * 0.42], fill=ORANGE, width=7)
    for s in (0.42, -0.42):
        draw.line([cx, cy, cx + np.cos(dL + s) * R * 0.6, cy + np.sin(dL + s) * R * 0.6],
                  fill=ORANGE, width=6)
    # upper (blue): shoulder bar + arms
    ux, uy = np.cos(dU), np.sin(dU); qx, qy = -uy, ux
    arm = R * (0.18 + 0.5 * ext)
    draw.line([cx + qx * R * 0.46, cy + qy * R * 0.46,
               cx - qx * R * 0.46, cy - qy * R * 0.46], fill=BLUE, width=8)
    for s in (1, -1):
        sx, sy = cx + qx * R * 0.46 * s, cy + qy * R * 0.46 * s
        draw.line([sx, sy, sx + ux * arm, sy + uy * arm], fill=BLUE, width=6)
    draw.ellipse([cx + ux * R * 0.1 - 5, cy + uy * R * 0.1 - 5,
                  cx + ux * R * 0.1 + 5, cy + uy * R * 0.1 + 5], fill=WHITE + (255,))
    draw.text((x0 + pad, y1 - 40), "blue = upper (leads)", font=f_s, fill=BLUE + (255,))
    draw.text((x0 + pad, y1 - 22), "orange = lower (snaps)", font=f_s, fill=ORANGE + (255,))
    draw.text((x1 - pad - 92, y1 - 22), f"{theta / (2 * np.pi):.2f} rev", font=f_s,
              fill=(220, 230, 245, 255))


def annotate(img, frac, mode, cen_i):
    from PIL import Image, ImageDraw
    cfg = MODES[mode]
    im = Image.fromarray(img).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im, "RGBA")
    f_big = font(max(18, W // 26))
    f_md = font(max(14, W // 38))
    f_sm = font(max(12, W // 46), bold=False)

    u = sim_u(frac, cfg["air"])
    pidx, name, rel = phase_at(frac, cfg["phases"])
    cx, cy, rr = cen_i
    rr = float(np.clip(rr, 60, W * 0.19))
    dirr = cfg["rot_dir"]

    open_mag, catch, psi_mag = twist_split(u)
    in_snap = 0.40 <= u <= 0.62

    # ---- on-skater glyph: lower = fixed reference, upper leads by psi ----
    sh = (cx, cy - rr * 0.5)     # shoulder (upper) node
    hp = (cx, cy + rr * 0.5)     # hip (lower) node
    bar = rr * 0.62
    d.line([sh, hp], fill=WHITE + (140,), width=3)                      # spine

    # lower bar: horizontal reference -- "barely turns"
    aL = 0.0
    lp = [(hp[0] - np.cos(aL) * bar * 0.9, hp[1] - np.sin(aL) * bar * 0.9),
          (hp[0] + np.cos(aL) * bar * 0.9, hp[1] + np.sin(aL) * bar * 0.9)]
    d.line(lp, fill=ORANGE + (255,), width=9)
    # upper bar: rotated ahead by the twist psi
    aU = -dirr * psi_mag
    up = [(sh[0] - np.cos(aU) * bar, sh[1] - np.sin(aU) * bar),
          (sh[0] + np.cos(aU) * bar, sh[1] + np.sin(aU) * bar)]
    d.line(up, fill=BLUE + (255,), width=9)
    # twist wedge at the shoulder (between horizontal and the upper bar)
    if psi_mag > 0.05:
        arc(d, sh[0], sh[1], bar * 0.55, 0.0, -dirr * psi_mag, WHITE, 180, 3)
        mid = -dirr * psi_mag * 0.5
        d.text((sh[0] + np.cos(mid) * bar * 0.62, sh[1] + np.sin(mid) * bar * 0.62),
               f"ψ = {np.degrees(psi_mag):.0f}°", font=f_sm, fill=WHITE + (255,))
    for p, col in [(sh, BLUE), (hp, ORANGE)]:
        d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=col + (255,),
                  outline=WHITE + (235,), width=2)
    d.text((max(up[0][0], up[1][0]) + 8, sh[1] - 20), "upper — leads",
           font=f_sm, fill=BLUE + (255,))
    d.text((lp[1][0] + 8, hp[1] - 8),
           "lower — barely turns" if not in_snap else "lower — snapping in",
           font=f_sm, fill=ORANGE + (255,))

    # snap: orange arrow of the lower swinging up to meet the upper
    if in_snap:
        a0, a1 = 0.0, -dirr * PSI_PEAK
        tip = arc(d, hp[0], hp[1], bar * 0.8, a0, a1, ORANGE, 255, 5)[-1]
        arrowhead(d, tip, a1 + dirr * np.pi / 2, max(12, int(rr * 0.2)), ORANGE)
        d.text((cx - rr * 0.5, cy + rr * 0.95), "SNAP → lower into line",
               font=f_md, fill=(255, 226, 158, 255))

    # ---- top banner ----
    bh = int(H * 0.085)
    d.rectangle([0, 0, W, bh], fill=(10, 18, 34, 180))
    d.text((16, 8), f"{pidx + 1}/5  {name}", font=f_big, fill=(255, 255, 255, 255))
    d.text((16, 8 + bh // 2), rel, font=f_sm, fill=(190, 215, 250, 255))

    # ---- sim inset ----
    pw = int(W * 0.34)
    box = (W - 14 - pw, int(H * 0.135), W - 14, int(H * 0.135) + pw)
    draw_sim_panel(d, box, u, dirr)

    # ---- small whole-body spin read-out (kept separate from the twist) ----
    if cfg["spin_readout"]:
        rev = TH[int(u * (NS - 1))] / (2 * np.pi)
        d.text((16, bh + 10), f"whole-body spin: {rev:.2f} rev  (ω = L / I)",
               font=f_sm, fill=WHITE + (235,))

    # ---- progress bar ----
    d.rectangle([0, H - 7, W, H], fill=(255, 255, 255, 45))
    d.rectangle([0, H - 7, int(W * frac), H], fill=ORANGE + (235,))
    return np.asarray(im)


def _discover(mode):
    """Best-effort default clip: newest file matching the mode's prefix. Pass an
    explicit path when the folder holds several candidates."""
    import glob
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pref = "RPReplay" if mode == "spin" else "ScreenRecording"
    hits = [p for p in glob.glob(os.path.join(root, pref + "*"))
            if p.lower().endswith((".mp4", ".mov", ".m4v"))]
    return max(hits, key=os.path.getmtime) if hits else None


def main():
    ap = argparse.ArgumentParser(description="Two-body overlay on skating footage.")
    ap.add_argument("clip", nargs="?", default=None)
    ap.add_argument("--mode", choices=["spin", "snap"], default="snap")
    ap.add_argument("--probe", action="store_true", help="dump sample PNGs, no encode")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from PIL import Image
    clip = args.clip or _discover(args.mode)
    if not clip or not os.path.exists(clip):
        raise SystemExit(f"no clip found for mode={args.mode}; pass a path")

    r = imageio.get_reader(clip, "ffmpeg")
    fps = r.get_meta_data().get("fps", 30)
    frames = [np.asarray(f)[..., :3] for f in r]; r.close()
    N = len(frames)
    cen = track(frames, MODES[args.mode]["roi"])
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
    os.makedirs(outdir, exist_ok=True)

    if args.probe:
        for fr in (0.15, 0.4, 0.52, 0.66, 0.9):
            i = int(fr * (N - 1))
            Image.fromarray(annotate(frames[i], i / (N - 1), args.mode, cen[i])).save(
                os.path.join(outdir, f"probe_{args.mode}_{int(fr * 100):02d}.png"))
        print(f"probe frames -> {outdir}")
        return

    out = args.out or os.path.join(
        outdir, f"07_skater_{'rotation' if args.mode == 'spin' else 'snap'}_two_body.mp4")
    H0, W0 = frames[0].shape[:2]
    scale = min(1.0, 720 / W0)
    Wt, Ht = int(round(W0 * scale / 16)) * 16, int(round(H0 * scale / 16)) * 16
    step = max(1, int(round(fps / 25)))
    w = imageio.get_writer(out, fps=25, codec="libx264", quality=7, macro_block_size=None)
    for i in range(0, N, step):
        fr = annotate(frames[i], i / (N - 1), args.mode, cen[i])
        w.append_data(np.asarray(Image.fromarray(fr).resize((Wt, Ht), Image.LANCZOS)))
    w.close()
    print(f"saved {out}  (total model spin {TOTAL_REV:.2f} rev)")


if __name__ == "__main__":
    main()
