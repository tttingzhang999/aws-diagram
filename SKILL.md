---
name: aws-diagram
description: Create or revise editable AWS architecture diagrams from requirements, repositories, or IaC. Interviews for scope (connectivity / network / HA preset), generates a single-page draw.io diagram with AWS icons, supports a manual-adjustment round-trip, then exports PNG/PDF/SVG with draw.io desktop. Use for "畫 AWS 架構圖", "AWS architecture diagram", "draw.io 架構圖", or /aws-diagram.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(uv *), Bash(ls *), Bash(test *), Bash(drawio *)
---

# AWS Architecture Diagrams

The deliverable is **one editable `.drawio` page**, a semantic architecture JSON beside it, and exported images. Use the user's requested diagram language; these instructions being English does not require English labels.

The workflow has three stages: **interview → generate and adjust → deliver**. Do not skip the adjustment stage; the user's manual edits in draw.io are part of the process.

## Stage A: Interview

Settle scope before drawing. When the source is a repository or IaC, scan it first (see Evidence rules) so questions can name the services actually found.

Ask once with AskUserQuestion, at most 3 questions. Skip any question the request already answers.

1. **Preset** — how much the diagram covers:

   | Preset         | Shows                                                                                          |
   | -------------- | ---------------------------------------------------------------------------------------------- |
   | `connectivity` | Services and application arrows only. No VPC, subnet, or AZ.                                   |
   | `network`      | Adds VPC boundary, subnet tiers, CIDRs, and placement of VPC-attached resources.               |
   | `ha`           | Adds AZ frames, per-AZ placement, HA roles, failover relationships, and single-AZ bottlenecks. |

2. **Optional details** (multi-select): logical endpoints, SG summaries, exceptional supporting-service dependencies, failure notes.
3. **Output**: label language, export formats (`png` default; `pdf`, `svg`), and save location when not obvious.

For verbal requirements, ask only for facts that change the drawing. Mark the rest unknown instead of asking more.

## Stage B: Generate and adjust

1. **Record evidence.** Save `<name>.architecture.json` with resource IDs, service types, scope, all known placements, meaningful relationships, source file references and revision, configuration provenance, assumptions, and HA limitations. Keep facts the preset hides; hiding is a presentation choice, not deletion.
2. **Generate the page.** Follow [references/drawio.md](references/drawio.md) for XML structure and connectors, [references/style.md](references/style.md) for group styles and spacing, and [references/aws-icons.json](references/aws-icons.json) for icons. Put nontrivial layout in a small `<name>.layout.py` beside the artifact.
3. **Check and preview.** On a newly generated page only, run draw.io's repair pass `drawio -x -f xml --normalize -o <name>.drawio <name>.drawio`; it grows clipped containers and fixes edge parents without moving placed cells. Then run `uv run <skill-dir>/scripts/drawio_check.py <name>.drawio`. Besides structure, it prints routing metrics (bends, crossings) and fails on overlapping edges or an edge/element through an icon or label; fix those by moving cells per `references/style.md`, and when a change reduces crossings or bends without adding failures, keep it. Then export a PNG (Stage C command) and inspect it yourself: missing icons, wrong colors, overlaps, ambiguous edges, VPC membership, readable text. Structural checks alone are insufficient. After three failed repair attempts on the same issue, stop and report the blocker.
4. **Hand over for adjustment.** Show the preview and the `.drawio` path. Tell the user to open it in draw.io, adjust layout and wording, save, and reply when done. Offer to polish label wording on request.
5. **Resume after edits.** Re-read the saved file; editor-saved files are compressed, so read them with `drawio_check.py <file> --decode`. From this point the user's file is the layout source of truth:
   - Never regenerate the page or re-run the layout script.
   - Patch only the cells a requested change touches; preserve IDs, geometry, styles, parents, and waypoints of everything else.
   - Reconcile user-added resources and connections into the architecture JSON.
   - Re-run `drawio_check.py` after each patch.

   Repeat steps 4–5 until the user approves.

## Stage C: Deliver

Export from the approved `.drawio` with draw.io desktop. It runs offline and renders exactly what the user saw:

```bash
drawio -x -f png -e --scale 2 --border 20 -o <name>.drawio.png <name>.drawio
drawio -x -f pdf -e --crop -o <name>.drawio.pdf <name>.drawio
drawio -x -f svg -e -o <name>.drawio.svg <name>.drawio
```

`-e` embeds the diagram XML, so each export also opens as an editable diagram in draw.io; the `.drawio.<ext>` suffix signals that. Keep the `.drawio` source too. Do not redraw the diagram with another library; visual polish belongs in draw.io styles (`references/style.md`), so it survives manual edits. If `drawio` is unavailable, use the fallback exporter in `references/drawio.md`.

Save to the requested location, otherwise beside the source repository's existing docs or architecture folder, or the current working directory. Report absolute paths of the editable file and exports, show the PNG, and briefly state the evidence basis and material unknowns. If no export could be verified, say so and keep the editable source.

## Diagram rules

### Connections

- Arrows mean application connectivity: API calls, data access, or explicitly identified event delivery/invocation. They do not mean network routes, IAM permissions, security-group allowances, or replication.
- Default to unlabeled arrows. Add short labels only where omission would mislead, such as presigned transfers, event triggers, or delivery-failure paths. Omit return traffic. Draw event/scheduled invocations dashed, with a small legend.
- Supporting services such as CloudWatch, ECR, Secrets Manager, IAM, KMS, and SSM normally keep their icons but no arrows. Show an exceptional dependency when it materially explains this architecture.
- Do not infer an application call from an SG rule or IAM grant. Confirm it in integrations, event targets, application clients, or other source evidence.

### Boundaries and HA (`network` and `ha` presets)

- Draw a VPC boundary around VPC-associated resources. Keep regional managed services such as API Gateway, S3, DynamoDB, Cognito, and EventBridge outside it. A private API does not place API Gateway in a subnet.
- Separate resource identity, deployment placements, and visual containment. AZ frames inside a VPC are a layout convention, not a claim that the VPC owns the AZs.
- Place zonal resources in their actual subnet. Show a logical service spanning subnets once, with its attachments identified; do not invent one replica per AZ.
- Show known CIDRs and meaningful subnet tiers. Retain empty subnets when they explain address planning. Derive public/private/isolated from routes, not names.
- Omit ENIs and low-level resources. A single-AZ endpoint can still be a material HA dependency.
- `ha` only: show supported HA roles, failover relationships, and shared dependencies. Two AZ frames alone do not establish HA. Never invent standby instances, capacity, failover guarantees, RTO/RPO, or disaster recovery.

### Icons

Use AWS service icons with their category colors from `aws-icons.json`; IAM is red, ECR is orange. For a missing service, verify the stencil and color, then add it to `aws-icons.json`. Otherwise use the clearly labeled generic resource icon. Never substitute an unrelated product logo.

## Evidence rules

- For a repository, inspect current IaC, application integrations, deployment settings, and relevant instructions. Use [references/terraform-mapping.md](references/terraform-mapping.md) for Terraform.
- Read narrowly selected configuration fields; never copy credentials into diagrams or logs.
- Static inspection is not a live AWS inventory. Do not run Terraform init/plan/apply, CDK synth, or AWS calls merely to draw the architecture.

## Editing an existing diagram

Enter Stage B step 5 directly: read the current `.drawio` and patch it under the same preservation rules. When a substantial re-layout is unavoidable, keep the previous version as `<name>.v<N>.drawio` first.
