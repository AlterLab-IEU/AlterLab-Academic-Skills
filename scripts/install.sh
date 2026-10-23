#!/usr/bin/env bash
#
# install.sh — install AlterLab Academic Skills into the right local skills directory.
#
# Agent Skills can live in two standard locations depending on the agent
# (see anthropics/claude-code#1101):
#
#   ~/.claude/skills/   — Claude Code's skills directory
#   ~/.agents/skills/   — the cross-tool agentskills.io standard directory
#
# This script resolves the correct destination, then installs the skill
# directories you ask for (whole domains and/or individual skills). It is
# idempotent: re-running it refreshes existing skills in place and never
# duplicates. Use --project to install into ./.claude/skills instead of $HOME.
#
# The copying itself is done by scripts/build_bundles.py (`install`), the same
# helper that builds the release archives, so an installed skill is
# dependency-complete in the same way:
#   * each skill's shared handoff files travel inside it (<skill>/shared/);
#   * a skill whose instructions call files in a sibling skill pulls that
#     sibling in too (e.g. alterlab-research-pipeline -> alterlab-citation-verifier);
#   * ${CLAUDE_PLUGIN_ROOT} in skill/agent/command markdown is written out as the
#     absolute destination directory (Claude Code fills it in only for plugins);
#   * LICENSE, NOTICE and THIRD_PARTY_NOTICES.md are copied into every skill.
# Requires python3 (3.9+, standard library only). After moving the destination
# directory, re-run the installer so the written-out paths follow.
#
# Usage:
#   scripts/install.sh [options] [SELECTOR ...]
#
# SELECTOR (zero or more):
#   <domain>                  e.g. bioinformatics      (installs every skill in it)
#   <domain>/<skill>          e.g. databases/alterlab-pubmed
#   <skill>                   e.g. alterlab-pubmed     (resolved across all domains)
#   (no selector)             installs ALL skills
#
# Options:
#   --target claude|agents    force destination family (default: auto-detect)
#   --project                 install into ./.claude/skills (project-local)
#   --dest <dir>              install into an explicit directory (overrides all)
#   --list                    list available domains/skills and exit
#   --dry-run                 print what would be installed, write nothing
#   --no-deps                 do not add the sibling skills a selection depends on
#   -h, --help                show this help
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/skills"

TARGET="auto"        # auto | claude | agents
PROJECT=0
EXPLICIT_DEST=""
DRY_RUN=0
NO_DEPS=0
DO_LIST=0
SELECTORS=()

die()  { printf 'error: %s\n' "$*" >&2; exit 1; }
note() { printf '%s\n' "$*" >&2; }

usage() { sed -n '2,44p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

# ---- arg parsing ----
while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --target=*) TARGET="${1#*=}"; shift ;;
    --project) PROJECT=1; shift ;;
    --dest) EXPLICIT_DEST="${2:-}"; shift 2 ;;
    --dest=*) EXPLICIT_DEST="${1#*=}"; shift ;;
    --list) DO_LIST=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-deps) NO_DEPS=1; shift ;;
    -h|--help) usage 0 ;;
    --*) die "unknown option: $1" ;;
    *) SELECTORS+=("$1"); shift ;;
  esac
done

[ -d "$SKILLS_SRC" ] || die "skills/ not found at $SKILLS_SRC"

case "$TARGET" in auto|claude|agents) ;; *) die "--target must be auto|claude|agents" ;; esac

# ---- list mode ----
if [ "$DO_LIST" -eq 1 ]; then
  for dom in "$SKILLS_SRC"/*/; do
    [ -d "$dom" ] || continue
    d="$(basename "$dom")"
    n=$(find "$dom" -mindepth 2 -maxdepth 2 -name SKILL.md -type f | wc -l | tr -d ' ')
    printf '%s (%s skills)\n' "$d" "$n"
    for sk in "$dom"*/; do
      [ -f "$sk/SKILL.md" ] && printf '  %s/%s\n' "$d" "$(basename "$sk")"
    done
  done
  exit 0
fi

# ---- resolve destination ----
resolve_dest() {
  if [ -n "$EXPLICIT_DEST" ]; then
    printf '%s' "$EXPLICIT_DEST"; return
  fi
  if [ "$PROJECT" -eq 1 ]; then
    printf '%s' "$PWD/.claude/skills"; return
  fi
  case "$TARGET" in
    claude) printf '%s' "$HOME/.claude/skills" ;;
    agents) printf '%s' "$HOME/.agents/skills" ;;
    auto)
      # Prefer whichever standard dir already exists; if both/neither, prefer
      # Claude Code when its config dir is present, else the agentskills dir.
      if [ -d "$HOME/.claude/skills" ] && [ ! -d "$HOME/.agents/skills" ]; then
        printf '%s' "$HOME/.claude/skills"
      elif [ -d "$HOME/.agents/skills" ] && [ ! -d "$HOME/.claude/skills" ]; then
        printf '%s' "$HOME/.agents/skills"
      elif [ -d "$HOME/.claude" ]; then
        printf '%s' "$HOME/.claude/skills"
      elif [ -d "$HOME/.agents" ]; then
        printf '%s' "$HOME/.agents/skills"
      else
        printf '%s' "$HOME/.claude/skills"
      fi
      ;;
  esac
}

DEST="$(resolve_dest)"
[ -n "$DEST" ] || die "empty destination"

# ---- expand selectors into a list of source skill directories ----
declare -a SRC_DIRS=()

add_skill_dir() {
  local dir="$1"
  [ -f "$dir/SKILL.md" ] || { note "skip (no SKILL.md): $dir"; return; }
  SRC_DIRS+=("$dir")
}

expand_selector() {
  local sel="$1"
  if [ -d "$SKILLS_SRC/$sel" ] && [ -f "$SKILLS_SRC/$sel/SKILL.md" ]; then
    # domain/skill
    add_skill_dir "$SKILLS_SRC/$sel"; return
  fi
  if [ -d "$SKILLS_SRC/$sel" ]; then
    # whole domain
    local found=0
    for sk in "$SKILLS_SRC/$sel"/*/; do
      [ -f "$sk/SKILL.md" ] && { add_skill_dir "${sk%/}"; found=1; }
    done
    [ "$found" -eq 1 ] || die "no skills under domain '$sel'"
    return
  fi
  # bare skill name — search every domain
  local matches=()
  while IFS= read -r m; do matches+=("$m"); done < <(
    find "$SKILLS_SRC" -mindepth 2 -maxdepth 2 -type d -name "$sel" 2>/dev/null
  )
  [ "${#matches[@]}" -gt 0 ] || die "selector not found: '$sel'"
  for m in "${matches[@]}"; do add_skill_dir "$m"; done
}

if [ "${#SELECTORS[@]}" -eq 0 ]; then
  # install everything (skill folders are exactly two levels below skills/)
  while IFS= read -r sm; do add_skill_dir "$(dirname "$sm")"; done < <(
    find "$SKILLS_SRC" -mindepth 3 -maxdepth 3 -name SKILL.md -type f | sort
  )
else
  for sel in "${SELECTORS[@]}"; do expand_selector "$sel"; done
fi

[ "${#SRC_DIRS[@]}" -gt 0 ] || die "nothing to install"

# ---- install (idempotent) through the shared packaging helper ----
command -v python3 >/dev/null 2>&1 || die "python3 is required (standard library only)"
note "destination: $DEST"
note "skills selected: ${#SRC_DIRS[@]}"

ARGS=(install --dest "$DEST")
if [ "$DRY_RUN" -eq 1 ]; then ARGS+=(--dry-run); fi
if [ "$NO_DEPS" -eq 1 ]; then ARGS+=(--no-deps); fi
python3 "$REPO_ROOT/scripts/build_bundles.py" "${ARGS[@]}" "${SRC_DIRS[@]}"

if [ "$DRY_RUN" -eq 0 ]; then
  printf 'restart your agent to load them.\n'
fi
