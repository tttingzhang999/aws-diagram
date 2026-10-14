# Editable draw.io output

Use one native, uncompressed `.drawio` page by default. Keep semantic evidence in an adjacent JSON and layout in a small per-diagram script when useful. No general IaC parser, automatic layout engine, or topology merge engine is bundled.

## Native shapes and containers

Use `mxfile > diagram > mxGraphModel > root`, with root cell `0` and layer cell `1`. Create resource cells with stable IDs, `vertex="1"`, an actual `parent`, and a child `mxGeometry`. Geometry is **relative to its parent**. Container styles should include `container=1;collapsible=0;recursiveResize=0;` so dragging the group carries its contents without unexpectedly scaling them.

Use IDs derived from source resource identity, not array indexes or labels. A logical service may have several placements in the semantic JSON but appear once on the page. Do not make placement duplicate the actual service identity.

For icons, look up the service in `aws-icons.json`. Its `shape` is the AWS4 stencil key and `fill` is the explicit category color. Use, for example:

```xml
<mxCell id="iam" parent="platform" vertex="1" value="IAM"
  style="shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.identity_and_access_management;fillColor=#DD344C;strokeColor=#ffffff;html=0;whiteSpace=wrap;verticalLabelPosition=bottom;verticalAlign=top;align=center;fontSize=13;labelWidth=150;">
  <mxGeometry x="40" y="60" width="58" height="58" as="geometry"/>
</mxCell>
```

ECR uses `resIcon=mxgraph.aws4.ecr` with `fillColor=#ED7100`. Do not pass unknown services through a generic purple default. Verify stencil names and colors together in the linked draw.io source; use AWS's [official icon package](https://aws.amazon.com/architecture/icons/) for missing/new assets when appropriate. Keep source/version information for imported SVGs, and embed assets or package them with the deliverable so previews do not depend on transient remote URLs.

A generic resource icon must be identified as generic. In particular, do not substitute a similarly named AWS product logo for a service whose icon has not been verified.

## Connectors

An edge is an `mxCell` with `edge="1"`, stable `source` and `target` IDs, and `mxGeometry relative="1" as="geometry"`. Use attached connectors, not detached line segments. For orthogonal routing:

```text
edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;endFill=1;
exitX=1;exitY=0.5;entryX=0;entryY=0.5;
```

Store bends in `Array as="points"` containing `mxPoint` elements. When the edge belongs to root layer `1`, these waypoint coordinates are in page space. Route outside labels and reserve lanes between groups. Line jumps (`jumpStyle=arc;jumpSize=8;`) can disambiguate unavoidable crossings but do not justify a crowded layout. Use dashed edges for meaningful event/scheduled invocation, with a small legend; ordinary service calls stay solid. A shared segment must not imply an untrue resource or connection.

## Editing and checks

- Preserve unaffected native geometry, style and custom annotations when modifying existing XML. Do not regenerate the entire page for a label change.
- Validate unique IDs, existing parents/endpoints, no containment cycles, child bounds, and the semantic scope of each resource. A private access path does not move a regional managed service into a VPC.
- Match visible application edges to source evidence. Do not blindly require every known supporting dependency to be drawn.
- Inspect text extents and actual connector paths in the exported preview; bounding-box checks cannot detect every label collision or confusing intersection.
- Treat compressed editor-saved files through an editor or a correct decoder. Do not overwrite an unreadable file with a newly generated diagram.

## Auto layout

draw.io's `--layout` presets (ELK) suit flat flowcharts, not nested AWS groups; they ignore subnet/AZ containment intent. Position AWS diagrams with the layout script instead. `--layout libavoid` (orthogonal edge routing without moving shapes) is not in draw.io desktop 32.4.1; use it only after confirming `drawio --help` lists it.

## Fallback preview exporter

Use only when draw.io desktop (`drawio`) is unavailable. `scripts/export_drawio.py` opens a single-page file in the real embedded draw.io editor and writes SVG plus PNG. The editor is fetched from `https://embed.diagrams.net`; the input is rendered in that browser iframe. Use a local/offline draw.io editor instead when the task requires offline handling. The script does not publish a hosted diagram or send messages to people.

It requires network access, Playwright, and a locally available browser. Run with `uv`; Playwright is declared as a script dependency, but **browser binaries are not installed by the script**. If Playwright's Chromium is unavailable, supply an existing Chrome/Chromium executable:

```bash
uv run <skill-dir>/scripts/export_drawio.py <diagram.drawio> \
  --browser-executable <existing-browser-path>
```

Outputs default to `<diagram>.svg` and `<diagram>.png` beside the editable source. `--output-prefix <path/stem>` chooses another destination. Use absolute paths when presenting files to the user. A failed browser/editor load is a failed preview verification, not proof the diagram is correct. Preserve the editable file and report the actual limitation if rendering cannot be completed.

Prefer an available native draw.io integration or already-installed desktop editor when that is simpler. The exporter is a reusable fallback, not a reason to install a plugin or browser without need.
