# aws-diagram

An [Agent Skill](https://agentskills.io) that turns requirements, a repository, or Terraform into an **editable** AWS architecture diagram.

The output is a single-page `.drawio` file with official AWS icons. You can adjust the layout by hand in draw.io; the skill keeps your edits and then exports PNG / PDF / SVG.

## Features

- **Three presets**: `connectivity` shows services and calls only; `network` adds VPC, subnets, and CIDRs; `ha` adds AZs, HA roles, and single points of failure.
- **Evidence-based**: every arrow must trace back to IaC or application code. Security group rules and IAM grants do not count as calls. Evidence is recorded in a sibling `<name>.architecture.json`.
- **No AWS access**: static reading only. It never runs `terraform plan` or calls AWS APIs.
- **Round-trip editing**: after generation you adjust and save in draw.io. Later changes patch only the affected cells instead of redrawing the page.
- **Automatic checks**: `scripts/drawio_check.py` validates structure and flags edges through icons or labels, overlapping edges, and crossing counts.

## Demo

Source: the official AWS sample [aws-samples/amazon-ecs-fullstack-app-terraform](https://github.com/aws-samples/amazon-ecs-fullstack-app-terraform) (MIT-0), read at commit `98ee8e6`.

### `network` preset

The frontend (Vue) and the API (Node) each run on ECS Fargate behind their own ALB. The bottom row is the CodePipeline blue/green deployment flow.

![network](examples/ecs-fullstack/ecs-fullstack.drawio.png)

### `ha` preset

The same repository from an HA perspective. Both ALBs have nodes in two AZs. There is only one NAT gateway, in AZ a. Each ECS service starts with one task, and its AZ is not pinned. Dashed boxes mark what AZ b is missing.

![ha](examples/ecs-fullstack/ecs-fullstack-ha.drawio.png)

All files for both diagrams live in [`examples/ecs-fullstack/`](examples/ecs-fullstack/):

| File                              | Purpose                                                                         |
| --------------------------------- | ------------------------------------------------------------------------------- |
| `*.drawio`                        | Editable source                                                                 |
| `*.drawio.png` / `*.drawio.svg`   | Exports with the diagram XML embedded; they open directly in draw.io            |
| `*.layout.py`                     | Layout script that generates the `.drawio`                                      |
| `ecs-fullstack.architecture.json` | Evidence record: resources, relationships, source files, and HA limitations     |

## Requirements

- **[draw.io desktop](https://github.com/jgraph/drawio-desktop)** with the `drawio` CLI (macOS: `brew install --cask drawio`)
- **[uv](https://docs.astral.sh/uv/)** to run the Python in `scripts/`
- **[Claude Code](https://docs.claude.com/en/docs/claude-code)** or **[Codex](https://developers.openai.com/codex)**

## Install

```bash
git clone https://github.com/tttingzhang999/aws-diagram.git
cd aws-diagram
./install.sh
```

The script symlinks the skill into `~/.claude/skills/aws-diagram` and `~/.codex/skills/aws-diagram`, only for agents that are installed.

## Usage

In Claude Code or Codex:

```text
/aws-diagram draw the architecture of ./infra
/aws-diagram draw the HA view of this Terraform repo
```

The skill asks at most three questions (preset, optional details, output format), then shows you a preview. Adjust the diagram in draw.io, reply when done, and it continues with edits or exports.

Regenerate the demo:

```bash
uv run examples/ecs-fullstack/ecs-fullstack.layout.py
uv run scripts/drawio_check.py examples/ecs-fullstack/ecs-fullstack.drawio
drawio -x -f png -e --scale 2 --border 20 -o examples/ecs-fullstack/ecs-fullstack.drawio.png examples/ecs-fullstack/ecs-fullstack.drawio
```

## Layout

```text
SKILL.md                      # Workflow: interview → generate and adjust → deliver
references/drawio.md          # draw.io XML structure and connector rules
references/style.md           # Group styles, spacing, HA layout rules
references/aws-icons.json     # Verified AWS4 stencils and colors
references/terraform-mapping.md
scripts/drawio_check.py       # Structure and routing checks
scripts/layout_metrics.py
scripts/export_drawio.py      # Fallback exporter when draw.io desktop is unavailable
examples/ecs-fullstack/
```

## License

[MIT](LICENSE). The demo architecture comes from aws-samples under MIT-0.
