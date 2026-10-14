#!/usr/bin/env bash
# aws-diagram installer: link the skill into ~/.claude/skills and ~/.codex/skills.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"

echo "==> aws-diagram install"
echo "    skill:   $SKILL_DIR"
echo "    targets: $CLAUDE_SKILLS_DIR/aws-diagram, $CODEX_SKILLS_DIR/aws-diagram"

command -v drawio >/dev/null || echo "    [warn] drawio not found; install draw.io desktop for exports"
command -v uv >/dev/null || echo "    [warn] uv not found; scripts/ need uv"

link_skill() {
  local dir="$1" link="$1/aws-diagram"
  mkdir -p "$dir"
  if [[ -L "$link" ]]; then
    local current
    current="$(readlink "$link")"
    if [[ "$current" == "$SKILL_DIR" ]]; then
      echo "    [skip] $link already points to $SKILL_DIR"
    else
      echo "    [warn] $link points to $current (leaving as-is)"
    fi
  elif [[ -e "$link" ]]; then
    echo "    [warn] $link exists and is not a symlink (leaving as-is)"
  else
    ln -s "$SKILL_DIR" "$link"
    echo "    [link] $link -> $SKILL_DIR"
  fi
}

[[ -d "$HOME/.claude" ]] && link_skill "$CLAUDE_SKILLS_DIR"
[[ -d "$HOME/.codex" ]] && link_skill "$CODEX_SKILLS_DIR"

echo "==> done"
