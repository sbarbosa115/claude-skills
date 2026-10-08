#!/usr/bin/env bash
# Link every skill in this repo into ~/.claude/skills, so the repo is the one copy Claude Code loads.
# Safe to re-run: existing links are refreshed; a real folder in the way is left alone and reported.
set -euo pipefail
repo="$(cd "$(dirname "$0")" && pwd)"
dest="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$dest"
for skill in "$repo"/*/; do
  skill="${skill%/}"
  [ -f "$skill/SKILL.md" ] || continue
  name="$(basename "$skill")"
  target="$dest/$name"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "skip $name: $target is a real folder; move it away and re-run"
    continue
  fi
  ln -sfn "$skill" "$target"
  echo "linked $name -> $skill"
done
