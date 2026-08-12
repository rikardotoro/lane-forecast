"""Regenerate the README charts from the demo data so they can never drift from behaviour.

Writes light and dark SVG variants to docs/charts/. No plotting library:
the charts are plain SVG, so the repo's only dependencies stay the runtime four.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lane_forecast.data import add_transit_days, load_shipments
from lane_forecast.quantiles import km_survival

ROOT = Path(__file__).parent.parent
OUT = ROOT / "docs" / "charts"

FONT = "system-ui, -apple-system, Segoe UI, sans-serif"

# Palette validated for both GitHub surfaces (#ffffff / #0d1117):
# CVD dE >= 24, normal-vision dE >= 31, contrast >= 3:1 in both modes.
TOKENS = {
    "light": {
        "arrived": "#2a78d6", "transit": "#eb6834",
        "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
        "grid": "#e1e0d9", "axis": "#c3c2b7",
    },
    "dark": {
        "arrived": "#3987e5", "transit": "#d95926",
        "ink": "#ffffff", "ink2": "#c3c2b7", "muted": "#898781",
        "grid": "#2c2c2a", "axis": "#383835",
    },
}


def _text(x, y, s, size, fill, anchor="start", weight="normal", tabular=False):
    style = "font-variant-numeric: tabular-nums;" if tabular else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" style="{style}">{s}</text>'
    )


def _line(x1, y1, x2, y2, stroke, width=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}"{d}/>'
    )


def _round_top_bar(x, y, w, h, fill, r=4.0):
    """Vertical bar, rounded at the data end (top), square on the baseline."""
    r = min(r, w / 2, h)
    return (
        f'<path d="M {x:.1f} {y + h:.1f} V {y + r:.1f} Q {x:.1f} {y:.1f} {x + r:.1f} {y:.1f} '
        f'H {x + w - r:.1f} Q {x + w:.1f} {y:.1f} {x + w:.1f} {y + r:.1f} V {y + h:.1f} Z" '
        f'fill="{fill}"/>'
    )


def _round_right_bar(x, y, w, h, fill, r=4.0):
    """Horizontal bar, rounded at the data end (right), square at departure."""
    r = min(r, h / 2, w)
    return (
        f'<path d="M {x:.1f} {y:.1f} H {x + w - r:.1f} Q {x + w:.1f} {y:.1f} {x + w:.1f} {y + r:.1f} '
        f'V {y + h - r:.1f} Q {x + w:.1f} {y + h:.1f} {x + w - r:.1f} {y + h:.1f} H {x:.1f} Z" '
        f'fill="{fill}"/>'
    )


def _legend_right(x_end, y, entries, t):
    """Legend row, right-aligned so it can never collide with the title."""
    width = sum(15 + 7.2 * len(label) + 22 for _, label in entries) - 22
    x, parts = x_end - width, []
    for color, label in entries:
        parts.append(f'<rect x="{x:.1f}" y="{y - 9:.1f}" width="10" height="10" rx="2" fill="{color}"/>')
        parts.append(_text(x + 15, y, label, 12, t["ink2"]))
        x += 15 + 7.2 * len(label) + 22
    return parts


def _svg(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">\n' + "\n".join(body) + "\n</svg>\n"
    )


# ---------------------------------------------------------------- chart 1
def chart_timeline(frame, mode):
    t = TOKENS[mode]
    as_of = frame["departure"].max()
    window = frame[frame["departure"] >= as_of - pd.Timedelta(days=21)]
    completed = window[~window["censored"]].sort_values("departure")
    censored = window[window["censored"]].sort_values("departure")

    def spread(group, n):
        idx = np.linspace(0, len(group) - 1, n).round().astype(int)
        return group.iloc[sorted(set(idx))]

    rows = pd.concat([spread(completed, 7), spread(censored, 5)]).sort_values("departure")

    W, H = 760, 330
    left, right, top, bottom = 20, 178, 64, 34
    x0, x1 = left, W - right
    start = as_of - pd.Timedelta(days=22)
    span = (as_of + pd.Timedelta(days=1) - start).days

    def X(d):
        return x0 + (d - start).days / span * (x1 - x0)

    body = [_text(20, 26, "A shipment that hasn't arrived is not missing data", 16, t["ink"], weight="600"),
            _text(20, 44, "Last three weeks of the demo lane. Every orange bar is evidence: transit is at least this long.", 12, t["ink2"])]
    # vertical legend in the right margin, clear of the title row
    for k, (color, label) in enumerate([(t["arrived"], "arrived"), (t["transit"], "still in transit")]):
        y = 86 + k * 20
        body.append(f'<rect x="{W - right + 16:.1f}" y="{y - 9:.1f}" width="10" height="10" rx="2" fill="{color}"/>')
        body.append(_text(W - right + 31, y, label, 12, t["ink2"]))

    plot_top, plot_bot = top + 8, H - bottom
    row_h, bar_h = (plot_bot - plot_top) / len(rows), 8

    # weekly gridlines + date labels
    for k in range(0, span + 1, 7):
        d = start + pd.Timedelta(days=k)
        body.append(_line(X(d), plot_top - 4, X(d), plot_bot, t["grid"]))
        body.append(_text(X(d), plot_bot + 18, d.strftime("%b %d"), 11, t["muted"], anchor="middle", tabular=True))

    today_x = X(as_of)
    body.append(_line(today_x, plot_top - 10, today_x, plot_bot, t["ink2"], 1.4, dash="4 3"))
    body.append(_text(today_x, plot_top - 16, "today", 12, t["ink2"], anchor="middle", weight="600"))

    longest = censored["transit_days"].max()
    labelled = False
    for i, (_, r) in enumerate(rows.iterrows()):
        y = plot_top + i * row_h + (row_h - bar_h) / 2
        xs = X(r["departure"])
        if r["censored"]:
            body.append(_round_right_bar(xs, y, today_x - xs, bar_h, t["transit"], r=0))
            body.append(
                f'<path d="M {today_x + 3:.1f} {y:.1f} L {today_x + 10:.1f} {y + bar_h / 2:.1f} '
                f'L {today_x + 3:.1f} {y + bar_h:.1f} Z" fill="{t["transit"]}"/>'
            )
            if r["transit_days"] == longest and not labelled:
                body.append(_text(today_x + 16, y + bar_h, f"≥ {longest:.0f} days and counting", 12, t["transit"], weight="600"))
                labelled = True
        else:
            xe = X(r["arrival"])
            body.append(_round_right_bar(xs, y, max(xe - xs, 6), bar_h, t["arrived"]))

    body.append(_text(W - right + 16, plot_bot + 18, "drop these rows and the lane", 11, t["muted"]))
    body.append(_text(W - right + 16, plot_bot + 31, "looks faster than it is", 11, t["muted"]))
    return _svg(W, H, body)


# ---------------------------------------------------------------- chart 2
def chart_histogram(frame, mode):
    t = TOKENS[mode]
    completed = frame[~frame["censored"]]["transit_days"]
    counts = completed.value_counts().sort_index()
    mean = completed.mean()

    times, surv = km_survival(frame["transit_days"].to_numpy(), (~frame["censored"]).to_numpy())
    p80 = float(times[np.nonzero(surv <= 0.2)[0][0]])

    W, H = 760, 320
    left, right, top, bottom = 52, 26, 74, 40
    x0, x1, y0, y1 = left, W - right, H - bottom, top + 6
    days = np.arange(0, 8)
    slot = (x1 - x0) / len(days)
    ymax = 1200

    def X(d):
        return x0 + (d + 0.5) * slot

    def Y(v):
        return y0 - v / ymax * (y0 - y1)

    body = [_text(20, 26, "The average is not a commitment", 16, t["ink"], weight="600"),
            _text(20, 44, "Completed transit times on the demo lane. Booking the average means arriving late half the time.", 12, t["ink2"])]

    for v in range(0, ymax + 1, 300):
        body.append(_line(x0, Y(v), x1, Y(v), t["grid"]))
        body.append(_text(x0 - 8, Y(v) + 4, f"{v:,}", 11, t["muted"], anchor="end", tabular=True))

    bar_w = slot * 0.62
    for d in days:
        n = int(counts.get(float(d), 0))
        if n:
            body.append(_round_top_bar(X(d) - bar_w / 2, Y(n), bar_w, y0 - Y(n), t["arrived"]))
        body.append(_text(X(d), y0 + 18, f"{d}", 11, t["muted"], anchor="middle", tabular=True))
    body.append(_text(X(3.5), y0 + 33, "transit days", 11, t["muted"], anchor="middle"))

    tallest = counts.idxmax()
    body.append(_text(X(tallest), Y(counts.max()) - 8, f"{int(counts.max()):,} shipments", 11, t["ink2"], anchor="middle"))

    body.append(_line(X(mean), y0, X(mean), y1 + 12, t["muted"], 1.4, dash="4 3"))
    body.append(_text(X(mean), y1 + 6, f"average {mean:.1f}", 12, t["ink2"], anchor="middle"))

    body.append(_line(X(p80), y0, X(p80), y1 + 12, t["transit"], 2))
    body.append(_text(X(p80), y1 + 6, f"book day {p80:.0f} (P80, corrected)", 12, t["transit"], anchor="middle", weight="600"))

    body.append(_line(x0, y0, x1, y0, t["axis"], 1.2))
    return _svg(W, H, body)


# ---------------------------------------------------------------- chart 3
def chart_skew(frame, mode):
    """Schematic of the archetypal transit distribution — analytic, not data.

    The demo data is order-delivery, truncated at 6 days, so it cannot show
    the ocean-lane shape this section describes. The curve is a gamma density
    shifted to a hard floor, labelled as a schematic.
    """
    t = TOKENS[mode]
    floor, k, theta = 14.0, 3.0, 2.6  # floor + gamma(k, theta), mean ~= 21.8
    xs = np.linspace(floor, 48, 300)
    z = (xs - floor) / theta
    dens = z ** (k - 1) * np.exp(-z)
    dens /= dens.max()
    mean = floor + k * theta

    W, H = 760, 300
    left, right, top, bottom = 24, 24, 74, 40
    x0, x1, y0, y1 = left, W - right, H - bottom, top + 24

    def X(v):
        return x0 + v / 50 * (x1 - x0)

    def Y(p):
        return y0 - p * (y0 - y1)

    body = [_text(20, 26, "The shape of a transit distribution", 16, t["ink"], weight="600"),
            _text(20, 44, "Schematic of a typical ocean lane — not the demo data. A hard floor, a body, and a long tail.", 12, t["ink2"])]

    # filled density curve
    poly = " L ".join(f"{X(x):.1f} {Y(d):.1f}" for x, d in zip(xs, dens))
    body.append(f'<path d="M {X(xs[0]):.1f} {y0:.1f} L {poly} L {X(xs[-1]):.1f} {y0:.1f} Z" '
                f'fill="{t["arrived"]}" fill-opacity="0.16"/>')
    body.append(f'<path d="M {poly}" fill="none" stroke="{t["arrived"]}" stroke-width="2" '
                f'stroke-linejoin="round"/>')

    # hard floor
    body.append(_line(X(floor), y0, X(floor), Y(0.72), t["ink2"], 1.4))
    body.append(_text(X(floor) - 6, Y(0.62), "the hard floor —", 11, t["ink2"], anchor="end"))
    body.append(_text(X(floor) - 6, Y(0.62) + 14, "fastest possible trip;", 11, t["ink2"], anchor="end"))
    body.append(_text(X(floor) - 6, Y(0.62) + 28, "nothing ever beats it", 11, t["ink2"], anchor="end"))

    # mean marker
    body.append(_line(X(mean), y0, X(mean), Y(0.98), t["muted"], 1.4, dash="4 3"))
    body.append(_text(X(mean), Y(0.98) - 8, "the average sits here…", 12, t["ink2"], anchor="middle"))

    # tail annotation
    body.append(_text(X(37.5), Y(0.30), "…and says nothing about the tail:", 12, t["ink2"], anchor="middle", weight="600"))
    body.append(_text(X(37.5), Y(0.30) + 15, "rolled cargo, port congestion, customs holds", 11, t["muted"], anchor="middle"))

    body.append(_line(x0, y0, x1, y0, t["axis"], 1.2))
    for v in (0, 10, 20, 30, 40, 50):
        body.append(_text(X(v), y0 + 18, f"{v}", 11, t["muted"], anchor="middle", tabular=True))
    body.append(_text(X(25), y0 + 33, "transit days", 11, t["muted"], anchor="middle"))
    return _svg(W, H, body)


# ---------------------------------------------------------------- chart 4
def chart_percentiles(frame, mode):
    t = TOKENS[mode]
    completed = frame[~frame["censored"]]["transit_days"].to_numpy()
    days = np.arange(0, 8)
    naive = [(completed <= d).mean() for d in days]

    times, surv = km_survival(frame["transit_days"].to_numpy(), (~frame["censored"]).to_numpy())
    lookup = dict(zip(times.tolist(), (1 - surv).tolist()))
    corrected, cur = [], 0.0
    for d in days:
        cur = lookup.get(float(d), cur)
        corrected.append(cur)

    naive_p80 = int(days[np.argmax(np.array(naive) >= 0.8)])
    corr_p80 = int(days[np.argmax(np.array(corrected) >= 0.8)])

    W, H = 760, 340
    left, right, top, bottom = 52, 26, 74, 40
    x0, x1, y0, y1 = left, W - right, H - bottom, top + 6

    def X(d):
        return x0 + d / 7 * (x1 - x0)

    def Y(p):
        return y0 - p * (y0 - y1)

    body = [_text(20, 26, "When has 80% of the cargo actually arrived?", 16, t["ink"], weight="600"),
            _text(20, 44, "Share of shipments arrived by each day — with and without the in-transit evidence.", 12, t["ink2"])]
    body += _legend_right(x1, 26, [(t["arrived"], "completed only"), (t["transit"], "all evidence")], t)

    for p in (0, 0.2, 0.4, 0.6, 1.0):
        body.append(_line(x0, Y(p), x1, Y(p), t["grid"]))
        body.append(_text(x0 - 8, Y(p) + 4, f"{p:.0%}", 11, t["muted"], anchor="end", tabular=True))
    body.append(_line(x0, Y(0.8), x1, Y(0.8), t["ink2"], 1.2, dash="5 4"))
    body.append(_text(x0 - 8, Y(0.8) + 4, "80%", 11, t["ink2"], anchor="end", weight="600", tabular=True))

    for d in days:
        body.append(_text(X(d), y0 + 18, f"{d}", 11, t["muted"], anchor="middle", tabular=True))
    body.append(_text(X(3.5), y0 + 33, "days since departure", 11, t["muted"], anchor="middle"))

    def steps(values, color):
        pts = [f"M {X(0):.1f} {Y(values[0]):.1f}"]
        for i in range(1, len(days)):
            pts.append(f"H {X(i):.1f} V {Y(values[i]):.1f}")
        return (
            f'<path d="{" ".join(pts)}" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linejoin="round"/>'
        )

    body.append(steps(naive, t["arrived"]))
    body.append(steps(corrected, t["transit"]))

    for d, color, label, dy in (
        (naive_p80, t["arrived"], f"day {naive_p80}", -10),
        (corr_p80, t["transit"], f"day {corr_p80}", -10),
    ):
        body.append(f'<circle cx="{X(d):.1f}" cy="{Y(0.8):.1f}" r="5" fill="{color}"/>')
        body.append(_text(X(d), Y(0.8) + dy, label, 12, color, anchor="middle", weight="600"))

    body.append(_text(X((naive_p80 + corr_p80) / 2), Y(0.55),
                      "one day apart — the optimism", 11, t["muted"], anchor="middle"))
    body.append(_text(X((naive_p80 + corr_p80) / 2), Y(0.55) + 14,
                      "you were about to plan on", 11, t["muted"], anchor="middle"))
    body.append(_line(x0, y0, x1, y0, t["axis"], 1.2))
    return _svg(W, H, body)


def main() -> int:
    frame = add_transit_days(load_shipments(ROOT / "examples" / "demo.csv"))
    OUT.mkdir(parents=True, exist_ok=True)
    charts = {
        "timeline": chart_timeline,
        "histogram": chart_histogram,
        "skew": chart_skew,
        "percentiles": chart_percentiles,
    }
    for name, fn in charts.items():
        for mode in ("light", "dark"):
            path = OUT / f"{name}-{mode}.svg"
            path.write_text(fn(frame, mode))
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
