#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write ecs-fullstack.drawio (network preset) beside this script."""

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
}
LABEL_POS = {
    "bottom": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    "top": "verticalLabelPosition=top;verticalAlign=bottom;align=center;",
}
EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;endFill=1;html=1;strokeColor=#545B64;strokeWidth=1.5;"

# id: (parent, kind, absolute x, y, w, h, label)
groups = [
    ("cloud", "1", "cloud", 160, 60, 1100, 840, "AWS Cloud"),
    ("vpc", "cloud", "vpc", 200, 150, 830, 550, "VPC 10.120.0.0/16"),
    ("sn_public", "vpc", "public", 230, 200, 230, 470, "Public subnets<br>10.120.2.0/23 · 10.120.4.0/23"),
    ("sn_client", "vpc", "private", 500, 200, 230, 470, "Private subnets (client)<br>10.120.6.0/23 · 10.120.8.0/23"),
    ("sn_server", "vpc", "private", 770, 200, 230, 470, "Private subnets (server)<br>10.120.10.0/23 · 10.120.12.0/23"),
]
# id: (parent, icon, x, y, label, label side)
icons = [
    ("users", "1", "users", 40, 360, "Users<br>(browser)", "bottom"),
    ("github", "1", "resource", 40, 780, "GitHub repo<br>(generic icon)", "bottom"),
    ("alb_client", "sn_public", "alb", 316, 290, "Client ALB", "bottom"),
    ("alb_server", "sn_public", "alb", 316, 440, "Server ALB", "bottom"),
    ("nat", "sn_public", "nat_gateway", 316, 560, "NAT gateway<br>(single, AZ a)", "bottom"),
    ("ecs_client", "sn_client", "ecs_service", 586, 290, "Client (Vue SPA)<br>Fargate · 1–4 tasks", "top"),
    ("ecs_server", "sn_server", "ecs_service", 856, 440, "Server (Node API)<br>Fargate · 1–4 tasks", "top"),
    ("s3_assets", "cloud", "s3", 1110, 81, "Assets bucket<br>(product images)", "bottom"),
    ("dynamodb", "cloud", "dynamodb", 1110, 440, "Products table", "bottom"),
    ("pipeline", "cloud", "codepipeline", 220, 780, "CodePipeline", "top"),
    ("codebuild", "cloud", "codebuild", 400, 780, "CodeBuild<br>(client, server)", "bottom"),
    ("ecr", "cloud", "ecr", 580, 780, "ECR<br>(client, server)", "bottom"),
    ("codedeploy", "cloud", "codedeploy", 720, 780, "CodeDeploy<br>blue/green", "bottom"),
    ("sns", "cloud", "sns", 900, 780, "SNS<br>deploy events", "bottom"),
    ("s3_artifacts", "cloud", "s3", 1060, 640, "Pipeline<br>artifacts", "bottom"),
    ("logs", "cloud", "cloudwatch", 1180, 640, "CloudWatch<br>Logs", "bottom"),
    ("iam", "cloud", "identity_and_access_management", 1180, 780, "IAM roles", "bottom"),
]
# id: (source, target, exit, entry, waypoints)
edges = [
    ("e_users_alb_client", "users", "alb_client", (1, 0.25), (0, 0.5), [(130, 374.5), (130, 319)]),
    ("e_users_alb_server", "users", "alb_server", (1, 0.75), (0, 0.5), [(140, 403.5), (140, 469)]),
    ("e_users_s3", "users", "s3_assets", (0.5, 0), (0, 0.5), [(69, 110)]),
    ("e_alb_ecs_client", "alb_client", "ecs_client", (1, 0.5), (0, 0.5), []),
    ("e_alb_ecs_server", "alb_server", "ecs_server", (1, 0.5), (0, 0.5), []),
    ("e_server_ddb", "ecs_server", "dynamodb", (1, 0.5), (0, 0.5), []),
    ("e_github_pipeline", "github", "pipeline", (1, 0.5), (0, 0.5), []),
    ("e_pipeline_build", "pipeline", "codebuild", (1, 0.5), (0, 0.5), []),
    ("e_build_ecr", "codebuild", "ecr", (1, 0.5), (0, 0.5), []),
    ("e_pipeline_deploy", "pipeline", "codedeploy", (0.5, 1), (0, 0.75), [(249, 880), (690, 880), (690, 823.5)]),
    ("e_deploy_ecs_client", "codedeploy", "ecs_client", (0.25, 0), (0.5, 1), [(734.5, 760), (615, 760)]),
    ("e_deploy_ecs_server", "codedeploy", "ecs_server", (0.75, 0), (0.5, 1), [(763.5, 740), (885, 740)]),
    ("e_deploy_sns", "codedeploy", "sns", (1, 0.5), (0, 0.5), []),
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
    {"id": "title", "parent": "1", "vertex": "1", "value": "Amazon ECS full-stack app (aws-samples/amazon-ecs-fullstack-app-terraform)",
     "style": "text;html=1;align=left;verticalAlign=middle;fontSize=16;fontStyle=1;"},
    '<mxGeometry x="160" y="20" width="700" height="30" as="geometry"/>',
)
for gid, parent, kind, x, y, w, h, label in groups:
    rx, ry = rel(parent, x, y)
    origin[gid] = (x, y)
    cell({"id": gid, "parent": parent, "vertex": "1", "value": label, "style": G + GROUPS[kind]},
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
    '<mxfile host="aws-diagram"><diagram id="ecs-fullstack" name="ecs-fullstack">'
    '<mxGraphModel dx="1400" dy="1000" grid="1" gridSize="10" page="0"><root>'
    '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>\n"
)
(HERE / "ecs-fullstack.drawio").write_text(xml)
print(HERE / "ecs-fullstack.drawio")
