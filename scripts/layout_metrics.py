"""Approximate connector routing quality for an uncompressed mxGraphModel.

Edges are rebuilt as orthogonal polylines from exit/entry anchors and waypoints. Where two
consecutive points are not aligned, an elbow is inserted that continues the previous direction,
which matches draw.io's orthogonal style for explicitly routed edges. Auto-routed edges without
waypoints are approximated the same way, so inspect the rendered preview as well.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

Box = tuple[float, float, float, float]
Pt = tuple[float, float]
EPS = 0.5
CHAR_W, LINE_H = 7.0, 17.0


@dataclass(frozen=True)
class Report:
    bends: dict[str, int]
    crossings: list[tuple[str, str]]
    overlaps: list[tuple[str, str]]
    through_icon: list[tuple[str, str]]
    through_label: list[tuple[str, str]]
    problems: list[str] = field(default_factory=list)


def _style(cell: ET.Element) -> dict[str, str]:
    return dict(kv.split("=", 1) for kv in (cell.get("style") or "").split(";") if "=" in kv)


def _abs_boxes(cells: dict[str, ET.Element]) -> dict[str, Box]:
    boxes: dict[str, Box] = {}

    def box(cid: str) -> Box | None:
        if cid in boxes:
            return boxes[cid]
        c = cells.get(cid)
        if c is None or c.get("vertex") != "1":
            return None
        g = c.find("mxGeometry")
        x, y, w, h = (float(g.get(k, 0)) for k in ("x", "y", "width", "height"))
        parent = box(c.get("parent", ""))
        if parent:
            x, y = x + parent[0], y + parent[1]
        boxes[cid] = (x, y, w, h)
        return boxes[cid]

    for cid in cells:
        box(cid)
    return boxes


def _text_lines(value: str | None) -> list[str]:
    text = re.sub(r"<br\s*/?>", "\n", value or "")
    text = re.sub(r"<[^>]+>", "", text).replace("&amp;", "&").strip()
    return text.split("\n") if text else []


def _label_box(cell: ET.Element, b: Box) -> Box | None:
    """Box of an icon label placed outside the shape (bottom / top / left / right)."""
    s = _style(cell)
    lines = _text_lines(cell.get("value"))
    if not lines:
        return None
    w = max(len(line) for line in lines) * CHAR_W
    h = len(lines) * LINE_H
    if s.get("labelPosition") == "left":
        return (b[0] - w - 4, b[1] + b[3] / 2 - h / 2, w, h)
    if s.get("labelPosition") == "right":
        return (b[0] + b[2] + 4, b[1] + b[3] / 2 - h / 2, w, h)
    w = min(w, float(s.get("labelWidth", b[2])))
    if s.get("verticalLabelPosition") == "top":
        return (b[0] + b[2] / 2 - w / 2, b[1] - h - 2, w, h)
    if s.get("verticalLabelPosition") == "bottom":
        return (b[0] + b[2] / 2 - w / 2, b[1] + b[3] + 2, w, h)
    return None


def _title_box(cell: ET.Element, b: Box) -> Box | None:
    """Box of a container's own title, drawn inside its top edge."""
    s = _style(cell)
    lines = _text_lines(cell.get("value"))
    if not lines:
        return None
    w = max(len(line) for line in lines) * CHAR_W
    pad = float(s.get("spacingLeft", 8))
    align = s.get("align", "center")
    x = {"right": b[0] + b[2] - w - 8, "center": b[0] + b[2] / 2 - w / 2}.get(align, b[0] + pad)
    return (x, b[1] + 2, w, len(lines) * LINE_H + 4)


def _edge_label_box(edge: ET.Element, poly: list[Pt]) -> Box | None:
    """draw.io places an edge label along the path: geometry x = -1 (source) .. 0 (middle) .. 1 (target)."""
    lines = _text_lines(edge.get("value"))
    if not lines or len(poly) < 2:
        return None
    segs = _segments(poly)
    g = edge.find("mxGeometry")
    offset = float(g.get("x", 0)) if g is not None else 0.0
    half = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in segs) * (offset + 1) / 2
    for a, b in segs:
        length = abs(a[0] - b[0]) + abs(a[1] - b[1])
        if half <= length:
            t = half / length if length else 0
            cx, cy = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            break
        half -= length
    pad = 6  # labels closer than this read as belonging to the wrong edge
    w, h = max(len(line) for line in lines) * 6.5 + 2 * pad, len(lines) * 14 + 2 * pad
    return (cx - w / 2, cy - h / 2, w, h)


def _anchor(b: Box, s: dict[str, str], prefix: str) -> Pt | None:
    if f"{prefix}X" not in s:
        return None
    return (b[0] + float(s[f"{prefix}X"]) * b[2], b[1] + float(s[f"{prefix}Y"]) * b[3])


def _side_dir(b: Box, p: Pt) -> str:
    on_lr = abs(p[0] - b[0]) < EPS or abs(p[0] - b[0] - b[2]) < EPS
    return "h" if on_lr else "v"


def _polyline(edge: ET.Element, boxes: dict[str, Box]) -> list[Pt]:
    s = _style(edge)
    src, dst = boxes[edge.get("source")], boxes[edge.get("target")]
    ox, oy, *_ = boxes.get(edge.get("parent", ""), (0, 0, 0, 0))
    pts = [(float(p.get("x", 0)) + ox, float(p.get("y", 0)) + oy) for p in edge.iter("mxPoint")]
    center = lambda b: (b[0] + b[2] / 2, b[1] + b[3] / 2)  # noqa: E731
    start = _anchor(src, s, "exit") or center(src)
    end = _anchor(dst, s, "entry") or center(dst)
    raw = [start, *pts, end]
    direction = _side_dir(src, start)
    out = [raw[0]]
    for q in raw[1:]:
        p = out[-1]
        if abs(p[0] - q[0]) > EPS and abs(p[1] - q[1]) > EPS:
            elbow = (q[0], p[1]) if direction == "h" else (p[0], q[1])
            out.append(elbow)
            direction = "v" if direction == "h" else "h"
        out.append(q)
        if abs(out[-2][1] - q[1]) < EPS and abs(out[-2][0] - q[0]) > EPS:
            direction = "h"
        elif abs(out[-2][0] - q[0]) < EPS and abs(out[-2][1] - q[1]) > EPS:
            direction = "v"
    return [p for i, p in enumerate(out) if i == 0 or abs(p[0] - out[i - 1][0]) + abs(p[1] - out[i - 1][1]) > EPS]


def _segments(poly: list[Pt]) -> list[tuple[Pt, Pt]]:
    return list(zip(poly, poly[1:]))


def _bends(poly: list[Pt]) -> int:
    dirs = ["h" if abs(a[1] - b[1]) < EPS else "v" for a, b in _segments(poly)]
    return sum(1 for a, b in zip(dirs, dirs[1:]) if a != b)


def _hits_box(a: Pt, b: Pt, box: Box) -> bool:
    x0, y0, x1, y1 = box[0] + 1, box[1] + 1, box[0] + box[2] - 1, box[1] + box[3] - 1
    lo_x, hi_x, lo_y, hi_y = min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])
    return lo_x < x1 and hi_x > x0 and lo_y < y1 and hi_y > y0


def _cross(s: tuple[Pt, Pt], t: tuple[Pt, Pt]) -> bool:
    (a, b), (c, d) = s, t
    s_h, t_h = abs(a[1] - b[1]) < EPS, abs(c[1] - d[1]) < EPS
    if s_h == t_h:
        return False
    (h0, h1), (v0, v1) = (s, t) if s_h else (t, s)
    x, y = v0[0], h0[1]
    return (min(h0[0], h1[0]) + EPS < x < max(h0[0], h1[0]) - EPS
            and min(v0[1], v1[1]) + EPS < y < max(v0[1], v1[1]) - EPS)


def _overlap(s: tuple[Pt, Pt], t: tuple[Pt, Pt]) -> bool:
    (a, b), (c, d) = s, t
    if abs(a[1] - b[1]) < EPS and abs(c[1] - d[1]) < EPS and abs(a[1] - c[1]) < EPS:
        lo, hi = max(min(a[0], b[0]), min(c[0], d[0])), min(max(a[0], b[0]), max(c[0], d[0]))
        return hi - lo > 2
    if abs(a[0] - b[0]) < EPS and abs(c[0] - d[0]) < EPS and abs(a[0] - c[0]) < EPS:
        lo, hi = max(min(a[1], b[1]), min(c[1], d[1])), min(max(a[1], b[1]), max(c[1], d[1]))
        return hi - lo > 2
    return False


def analyze(model: ET.Element) -> Report:
    cells = {c.get("id"): c for c in model.iter("mxCell")}
    boxes = _abs_boxes(cells)
    icons = {cid: boxes[cid] for cid, c in cells.items()
             if cid in boxes and _style(c).get("container") != "1" and "text" not in (c.get("style") or "")}
    through_icon, through_label = [], []
    labels = {cid: lb for cid in icons if (lb := _label_box(cells[cid], icons[cid]))}
    labels |= {f"{cid} (title)": tb for cid, c in cells.items()
               if cid in boxes and _style(c).get("container") == "1" and (tb := _title_box(c, boxes[cid]))}
    edges = {cid: c for cid, c in cells.items() if c.get("edge") == "1"}
    polys = {cid: _polyline(e, boxes) for cid, e in edges.items()}
    edge_labels = {cid: lb for cid, e in edges.items() if (lb := _edge_label_box(e, polys[cid]))}

    corners = lambda b: (b[:2], (b[0] + b[2], b[1] + b[3]))  # noqa: E731
    label_ids = list(edge_labels)
    for i, e1 in enumerate(label_ids):
        through_label += [(f"{e1} (label)", f"{e2} (label)") for e2 in label_ids[i + 1:]
                          if _hits_box(*corners(edge_labels[e1]), edge_labels[e2])]
    for cid, lb in edge_labels.items():
        ends = {edges[cid].get("source"), edges[cid].get("target")}
        through_label += [(f"{cid} (label)", v) for v, bx in icons.items() if v not in ends and _hits_box(*corners(lb), bx)]
        through_label += [(f"{cid} (label)", v) for v, bx in labels.items() if _hits_box(*corners(lb), bx)]

    for cid, poly in polys.items():
        ends = {edges[cid].get("source"), edges[cid].get("target")}
        for a, b in _segments(poly):
            through_icon += [(cid, v) for v, bx in icons.items() if v not in ends and _hits_box(a, b, bx)]
            through_label += [(cid, v) for v, lb in labels.items() if _hits_box(a, b, lb)]

    for cid, c in cells.items():
        if cid not in boxes or _style(c).get("container") != "1":
            continue
        x, y, w, h = boxes[cid]
        sides = [((x, y), (x + w, y)), ((x, y + h), (x + w, y + h)), ((x, y), (x, y + h)), ((x + w, y), (x + w, y + h))]
        through_label += [(f"{cid} (border)", v) for v, lb in labels.items()
                          if v != f"{cid} (title)" and any(_hits_box(p, q, lb) for p, q in sides)]

    for cid, lb in labels.items():
        owner = cid.removesuffix(" (title)")
        through_label += [(v, cid) for v, bx in icons.items() if v != owner and _hits_box(*corners(lb), bx)]

    crossings, overlaps = [], []
    ids = list(polys)
    for i, e1 in enumerate(ids):
        for e2 in ids[i + 1:]:
            pairs = [(s, t) for s in _segments(polys[e1]) for t in _segments(polys[e2])]
            crossings += [(e1, e2)] * sum(_cross(s, t) for s, t in pairs)
            if any(_overlap(s, t) for s, t in pairs):
                overlaps.append((e1, e2))

    dedupe = lambda xs: sorted(set(xs))  # noqa: E731
    report = Report({cid: _bends(p) for cid, p in polys.items()}, crossings, dedupe(overlaps),
                    dedupe(through_icon), dedupe(through_label))
    report.problems.extend(f"overlap: {a} / {b}" for a, b in report.overlaps)
    report.problems.extend(f"{e} passes through icon {v}" for e, v in report.through_icon)
    report.problems.extend(f"{e} overlaps label of {v}" for e, v in report.through_label)
    return report


def summary(r: Report) -> str:
    worst = sorted(r.bends.items(), key=lambda kv: -kv[1])[:3]
    return (f"layout: {len(r.bends)} edges, {sum(r.bends.values())} bends "
            f"(max: {', '.join(f'{k}={v}' for k, v in worst)}), {len(r.crossings)} crossings, "
            f"{len(r.overlaps)} overlaps, {len(r.through_icon)} through-icon, {len(r.through_label)} through-label")
