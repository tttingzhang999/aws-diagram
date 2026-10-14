# Style preset

Apply this preset to every diagram so exports look consistent without post-processing. Verified by rendering with draw.io desktop 2026-10-13.

## Shared group prefix

Every AWS group below starts with this prefix (`<G>`):

```text
points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;verticalAlign=top;align=left;spacingLeft=30;
```

## Groups

| Group           | Style after `<G>`                                                                                                       |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| AWS Cloud       | `grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;fontColor=#232F3E;dashed=0;`                |
| Region          | `grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;fontColor=#147EBA;dashed=1;`                       |
| VPC             | `grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;fontColor=#AAB7B8;dashed=0;`                         |
| Public subnet   | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;fontColor=#248814;dashed=0;` |
| Private subnet  | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;fontColor=#147EBA;dashed=0;` |
| Isolated subnet | `grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7D8998;fillColor=#F2F3F3;fontColor=#5A6B86;dashed=0;` |

AZ is a plain dashed frame, not an AWS group shape:

```text
fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;
```

The `connectivity` preset uses only AWS Cloud (and Region when more than one Region exists). `network` adds VPC and subnets. `ha` adds AZ frames.

## Icons, text, and spacing

- Service icons: 58×58, label below (`verticalLabelPosition=bottom;verticalAlign=top;align=center;fontSize=12;`). Colors from `aws-icons.json`.
- Labels: service role first, product second only when ambiguous (`Order API` over `Lambda: order-api`). Keep each label to two short lines.
- Spacing: 40 px between icons, 30 px group padding, 60 px routing lanes between groups. Snap coordinates to a 10 px grid.
- Routing goals, in priority order: (1) no edge through an icon or label, and no two edges sharing a segment — hard failures in `drawio_check.py`; (2) fewest crossings; (3) fewest bends. Get there by placement, not waypoints: put each edge's endpoints on one row or column where possible, give every edge on a shared side its own anchor (0.25 / 0.5 / 0.75), and give every vertical lane its own x.
- `ha` layout: AZ frames sit side by side with a gap (≥ 40 px, never shared borders). Each AZ holds its own subnet boxes, one per tier, each titled with its own CIDR. Draw per AZ only what exists per AZ (ALB nodes, Lambda/endpoint ENIs, NAT, each DB instance). Draw a single-copy resource (e.g. ECS services at desired_count 1, a lone DB writer) once, in one AZ, with "AZ not pinned" if IaC does not fix it, and put a dashed ghost box in the other AZ stating what is missing — never centre it across the AZs, which reads as two copies. Mark the second AZ as a mirror and draw arrows there only where it differs (e.g. cross-zone traffic) so edges do not double.
- `network` layout: subnet tiers may be full-width bands with both AZ CIDRs in the title; no AZ frames.
- Page size is not limited. Grow the canvas before compressing a complex architecture.
- Container borders count as lines: no border may cross a title or label (`drawio_check.py` reports `(border) overlaps label`).
- A label occupies one side of its icon. When an edge must leave or enter that side, move the label (`top`, `left`, `right`) instead of routing through it.
- Edges: `#545B64`, `strokeWidth=1.5`; event/scheduled edges add `dashed=1`. Edge labels `fontSize=11` with `labelBackgroundColor=#FFFFFF`.
- Legend: a small frame in the bottom-right corner, only when the diagram uses dashed edges or other non-obvious notation.
- Title: optional text cell above the AWS Cloud group, `fontSize=16;fontStyle=1;`.
