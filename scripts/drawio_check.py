#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Decode and structurally validate a single-page .drawio file.

  drawio_check.py <file.drawio>            validate; exit 1 on problems
  drawio_check.py <file.drawio> --decode   print uncompressed XML (editor-saved files are compressed)
"""

from __future__ import annotations

import argparse
import base64
import sys
import zlib
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from layout_metrics import analyze, summary


def load_model(path: Path) -> ET.Element:
    root = ET.parse(path).getroot()
    diagrams = root.findall("diagram")
    if len(diagrams) != 1:
        raise ValueError(f"expected exactly one page, found {len(diagrams)}")
    diagram = diagrams[0]
    model = diagram.find("mxGraphModel")
    if model is not None:
        return model
    raw = zlib.decompress(base64.b64decode(diagram.text or ""), -15)
    return ET.fromstring(unquote(raw.decode("utf-8")))


def _geometry(cell: ET.Element) -> tuple[float, float, float, float] | None:
    g = cell.find("mxGeometry")
    if g is None or g.get("relative") == "1":
        return None
    return tuple(float(g.get(k, 0)) for k in ("x", "y", "width", "height"))


def problems(model: ET.Element) -> list[str]:
    cells = model.findall("./root/mxCell") + model.findall("./root/*/mxCell")
    found: list[str] = []
    by_id: dict[str, ET.Element] = {}
    for c in cells:
        cid = c.get("id", "")
        if cid in by_id:
            found.append(f"duplicate id: {cid}")
        by_id[cid] = c

    for cid, c in by_id.items():
        parent = c.get("parent")
        if cid != "0" and parent not in by_id:
            found.append(f"{cid}: missing parent {parent}")
        if c.get("edge") == "1":
            for end in ("source", "target"):
                if c.get(end) not in by_id:
                    found.append(f"{cid}: detached or unknown {end} {c.get(end)}")

    for cid in by_id:
        seen, cur = set(), cid
        while cur in by_id and cur != "0":
            if cur in seen:
                found.append(f"{cid}: containment cycle")
                break
            seen.add(cur)
            cur = by_id[cur].get("parent")

    for cid, c in by_id.items():
        parent = by_id.get(c.get("parent", ""))
        if c.get("vertex") != "1" or parent is None or parent.get("vertex") != "1":
            continue
        child, box = _geometry(c), _geometry(parent)
        if child and box and (child[0] < 0 or child[1] < 0
                              or child[0] + child[2] > box[2] or child[1] + child[3] > box[3]):
            found.append(f"{cid}: outside parent {parent.get('id')} bounds")
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    ap.add_argument("--decode", action="store_true")
    args = ap.parse_args()
    try:
        model = load_model(args.file)
    except (ET.ParseError, ValueError, zlib.error) as exc:
        print(f"cannot read {args.file}: {exc}", file=sys.stderr)
        return 2
    if args.decode:
        print(ET.tostring(model, encoding="unicode"))
        return 0
    found = problems(model)
    if not found:
        report = analyze(model)
        found = report.problems
        print(summary(report), file=sys.stderr)
    for p in found:
        print(p)
    print("OK" if not found else f"{len(found)} problem(s)", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
