#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./sync_skills.sh [--to-codex|--to-claude] [--mirror]

Options:
  --to-codex   Sync .claude/skills -> ~/.codex/skills (default)
  --to-claude  Sync ~/.codex/skills -> .claude/skills
  --mirror     Delete skills on destination that are not in source
EOF
}

direction="to-codex"
mirror=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to-codex)
      direction="to-codex"
      shift
      ;;
    --to-claude)
      direction="to-claude"
      shift
      ;;
    --mirror)
      mirror=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${direction}" == "to-codex" ]]; then
  src="${root_dir}/.claude/skills/"
  dest="${HOME}/.codex/skills/"
else
  src="${HOME}/.codex/skills/"
  dest="${root_dir}/.claude/skills/"
fi

if [[ ! -d "${src}" ]]; then
  echo "Source directory not found: ${src}" >&2
  exit 1
fi

mkdir -p "${dest}"

rsync_args=(-a --exclude ".system")
if [[ ${mirror} -eq 1 ]]; then
  rsync_args+=(--delete)
fi

rsync "${rsync_args[@]}" "${src}" "${dest}"

echo "Synced skills:"
echo "  ${src} -> ${dest}"
if [[ "${direction}" == "to-codex" ]]; then
  echo "Tip: restart Codex CLI to reload skills."
fi
