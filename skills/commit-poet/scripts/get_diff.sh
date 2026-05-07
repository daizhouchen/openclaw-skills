#!/usr/bin/env bash
#
# get_diff.sh - Get formatted git diff with file statistics
#
# Usage: ./get_diff.sh [--cached] [path]
#
# Options:
#   --cached    Show staged changes (default: unstaged changes)
#   path        Optional path filter
#
# Output:
#   1. File change statistics summary
#   2. Full diff content

set -euo pipefail

CACHED=""
TARGET_PATH=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cached)
            CACHED="--cached"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--cached] [path]"
            echo ""
            echo "Options:"
            echo "  --cached    Show staged changes (default: unstaged)"
            echo "  path        Optional path filter"
            exit 0
            ;;
        *)
            TARGET_PATH="$1"
            shift
            ;;
    esac
done

# Check we are in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: not inside a git repository" >&2
    exit 1
fi

# Build git diff command args: flags go before --, paths go after
FLAG_ARGS=($CACHED)
PATH_ARGS=()
if [[ -n "$TARGET_PATH" ]]; then
    PATH_ARGS=(-- "$TARGET_PATH")
fi

# Helper: run git diff with given extra flags, then path args
run_diff() {
    git diff "${FLAG_ARGS[@]}" "$@" "${PATH_ARGS[@]}" 2>/dev/null
}

echo "========================================"
echo "  Git Diff Summary"
echo "========================================"
echo ""

# Show diffstat
STAT_OUTPUT=$(run_diff --stat || true)
if [[ -z "$STAT_OUTPUT" ]]; then
    if [[ -n "$CACHED" ]]; then
        echo "No staged changes found."
    else
        echo "No unstaged changes found."
    fi
    echo ""
    echo "Tip: use --cached for staged changes, or omit for unstaged."
    exit 0
fi

echo "$STAT_OUTPUT"
echo ""

# Count files changed
FILES_CHANGED=$(run_diff --name-only | wc -l)
INSERTIONS=$(run_diff --shortstat | grep -oP '\d+ insertion' | grep -oP '\d+' || echo "0")
DELETIONS=$(run_diff --shortstat | grep -oP '\d+ deletion' | grep -oP '\d+' || echo "0")

echo "Files changed: $FILES_CHANGED"
echo "Insertions:    +${INSERTIONS}"
echo "Deletions:     -${DELETIONS}"
echo ""

# List affected files
echo "Affected files:"
run_diff --name-status | while IFS=$'\t' read -r status file; do
    case "$status" in
        A) echo "  [NEW]      $file" ;;
        M) echo "  [MODIFIED] $file" ;;
        D) echo "  [DELETED]  $file" ;;
        R*) echo "  [RENAMED]  $file" ;;
        C*) echo "  [COPIED]   $file" ;;
        *) echo "  [$status]  $file" ;;
    esac
done

echo ""
echo "========================================"
echo "  Full Diff"
echo "========================================"
echo ""

run_diff
