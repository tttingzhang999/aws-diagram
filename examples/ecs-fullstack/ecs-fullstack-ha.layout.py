#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write ecs-fullstack-ha.drawio (ha preset) beside this script."""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import quoteattr

HERE = Path(__file__).resolve().parent
ICONS = json.loads((HERE.parent.parent / "references" / "aws-icons.json").read_text())["services"]

G = (
    "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],"
    "[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;"
    "fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;"
    "shape=mxgraph.aws4.group;verticalAlign=top;align=left;spacingLeft=30;"
)
GROUPS = {
    "cloud": "grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;fontColor=#232F3E;dashed=0;",
    "vpc": "grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;fontColor=#AAB7B8;dashed=0;",
    "public": "grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;fontColor=#248814;dashed=0;",
    "private": "grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;fontColor=#147EBA;dashed=0;",
    "az": "fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;align=left;spacingLeft=10;fontStyle=0;fontColor=#147EBA;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;",
}
GHOST = "rounded=0;dashed=1;fillColor=none;strokeColor=#7D8998;fontColor=#5A6B86;fontSize=11;html=1;whiteSpace=wrap;"
LABEL_POS = {
    "bottom": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    "top": "verticalLabelPosition=top;verticalAlign=bottom;align=center;",
}
EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;endFill=1;html=1;strokeColor=#545B64;strokeWidth=1.5;"

# id: (parent, kind, absolute x, y, w, h, label)
groups = [
    ("cloud", "1", "cloud", 160, 60, 1100, 1170, "AWS Cloud"),
    ("vpc", "cloud", "vpc", 200, 150, 830, 1050, "VPC 10.120.0.0/16"),
    ("az_a", "vpc", "az", 220, 190, 790, 480, "Availability zone a"),
    ("a_public", "az_a", "public", 240, 230, 220, 420, "Public subnet<br>10.120.2.0/23"),
    ("a_client", "az_a", "private", 500, 230, 220, 420, "Private subnet (client)<br>10.120.6.0/23"),
    ("a_server", "az_a", "private", 770, 230, 220, 420, "Private subnet (server)<br>10.120.10.0/23"),
    ("az_b", "vpc", "az", 220, 710, 790, 470, "Availability zone b (mirror of a: same flows, arrows omitted)"),
    ("b_public", "az_b", "public", 240, 750, 220, 410, "Public subnet<br>10.120.4.0/23"),
    ("b_client", "az_b", "private", 500, 750, 220, 410, "Private subnet (client)<br>10.120.8.0/23"),
    ("b_server", "az_b", "private", 770, 750, 220, 410, "Private subnet (server)<br>10.120.12.0/23"),
]
# id: (parent, absolute x, y, w, h, label)
ghosts = [
    ("ghost_client_b", "b_client", 520, 810, 180, 80, "No second client task<br>desired 1, AZ not pinned<br>(autoscaling 1–4)"),
    ("ghost_server_b", "b_server", 790, 930, 180, 80, "No second server task<br>desired 1, AZ not pinned<br>(autoscaling 1–4)"),
    ("ghost_nat_b", "b_public", 260, 1060, 180, 70, "No NAT gateway<br>egress depends on AZ a"),
]
# id: (parent, icon, x, y, label, label side)
icons = [
    ("users", "1", "users", 40, 360, "Users<br>(browser)", "bottom"),
    ("a_alb_client", "a_public", "alb", 321, 320, "Client ALB node", "bottom"),
    ("a_alb_server", "a_public", "alb", 321, 440, "Server ALB node", "bottom"),
    ("nat", "a_public", "nat_gateway", 321, 540, "NAT gateway<br>(only one)", "bottom"),
    ("ecs_client", "a_client", "ecs_service", 581, 320, "Client task<br>AZ not pinned", "top"),
    ("ecs_server", "a_server", "ecs_service", 851, 440, "Server task<br>AZ not pinned", "top"),
    ("b_alb_client", "b_public", "alb", 321, 840, "Client ALB node", "bottom"),
    ("b_alb_server", "b_public", "alb", 321, 960, "Server ALB node", "bottom"),
    ("s3_assets", "cloud", "s3", 1110, 81, "Assets bucket<br>(regional)", "bottom"),
    ("dynamodb", "cloud", "dynamodb", 1110, 440, "Products table<br>(regional)", "bottom"),
]
# id: (source, target, exit, entry, waypoints)
edges = [
    ("e_users_alb_client", "users", "a_alb_client", (1, 0.25), (0, 0.5), [(130, 374.5), (130, 349)]),
    ("e_users_alb_server", "users", "a_alb_server", (1, 0.75), (0, 0.5), [(140, 403.5), (140, 469)]),
    ("e_users_s3", "users", "s3_assets", (0.5, 0), (0, 0.5), [(69, 110)]),
    ("e_alb_ecs_client", "a_alb_client", "ecs_client", (1, 0.5), (0, 0.5), []),
    ("e_alb_ecs_server", "a_alb_server", "ecs_server", (1, 0.5), (0, 0.5), []),
    ("e_server_ddb", "ecs_server", "dynamodb", (1, 0.5), (0, 0.5), []),
]

ICON = 58
origin: dict[str, tuple[float, float]] = {"1": (0, 0)}
cells: list[str] = []


def cell(attrs: dict[str, str], geometry: str) -> None:
    rendered = " ".join(f"{k}={quoteattr(v)}" for k, v in attrs.items())
    cells.append(f"<mxCell {rendered}>{geometry}</mxCell>")


def rel(parent: str, x: float, y: float) -> tuple[float, float]:
    ox, oy = origin[parent]
    return x - ox, y - oy


def icon_style(name: str, side: str) -> str:
    spec = ICONS[name]
    if spec.get("kind") == "standalone":
        base = f"shape=mxgraph.aws4.{spec['shape']};fillColor={spec['fill']};strokeColor=none;aspect=fixed;"
    else:
        base = (
            f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{spec['shape']};"
            f"fillColor={spec['fill']};strokeColor=#ffffff;"
        )
    return base + LABEL_POS[side] + "html=1;whiteSpace=wrap;fontSize=12;fontColor=#232F3E;labelWidth=150;"


cell(
    {"id": "title", "parent": "1", "vertex": "1", "value": "Amazon ECS full-stack app: HA view (aws-samples/amazon-ecs-fullstack-app-terraform)",
     "style": "text;html=1;align=left;verticalAlign=middle;fontSize=16;fontStyle=1;"},
    '<mxGeometry x="160" y="20" width="700" height="30" as="geometry"/>',
)
for gid, parent, kind, x, y, w, h, label in groups:
    rx, ry = rel(parent, x, y)
    origin[gid] = (x, y)
    cell({"id": gid, "parent": parent, "vertex": "1", "value": label, "style": GROUPS[kind] if kind == "az" else G + GROUPS[kind]},
         f'<mxGeometry x="{rx}" y="{ry}" width="{w}" height="{h}" as="geometry"/>')
for gid, parent, x, y, w, h, label in ghosts:
    rx, ry = rel(parent, x, y)
    cell({"id": gid, "parent": parent, "vertex": "1", "value": label, "style": GHOST},
         f'<mxGeometry x="{rx}" y="{ry}" width="{w}" height="{h}" as="geometry"/>')
for iid, parent, name, x, y, label, side in icons:
    rx, ry = rel(parent, x, y)
    cell({"id": iid, "parent": parent, "vertex": "1", "value": label, "style": icon_style(name, side)},
         f'<mxGeometry x="{rx}" y="{ry}" width="{ICON}" height="{ICON}" as="geometry"/>')
for eid, src, tgt, (ex, ey), (nx, ny), points in edges:
    style = EDGE + f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={nx};entryY={ny};entryDx=0;entryDy=0;"
    pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in points)
    array = f'<Array as="points">{pts}</Array>' if pts else ""
    geometry = f'<mxGeometry relative="1" as="geometry">{array}</mxGeometry>'
    cell({"id": eid, "parent": "1", "edge": "1", "source": src, "target": tgt, "value": "", "style": style}, geometry)

xml = (
    '<mxfile host="aws-diagram"><diagram id="ecs-fullstack-ha" name="ecs-fullstack-ha">'
    '<mxGraphModel dx="1400" dy="1000" grid="1" gridSize="10" page="0"><root>'
    '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>\n"
)
(HERE / "ecs-fullstack-ha.drawio").write_text(xml)
print(HERE / "ecs-fullstack-ha.drawio")
