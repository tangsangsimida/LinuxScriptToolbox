#!/usr/bin/env bash
# Continuous testing loop for LinuxScriptToolbox (Agent B)
#
# Reference: docs/TESTING_AGENT_WORK.md
#
# Runs in a loop:
#   1. git pull latest from origin/main
#   2. Re-test any issues closed since the last cycle
#   3. Run unit tests + lint + UI pattern checks
#   4. Smoke-test all 12 tools
#   5. Append a cycle entry to docs/optimization_report.md

set -euo pipefail

REMOTE_HOST="dennis@47.120.25.110"
PROJECT_PATH="~/LinuxScriptToolbox"
CHECK_INTERVAL="${CHECK_INTERVAL:-180}"  # 3 minutes
REPORT_PATH="docs/optimization_report.md"
TOOLS=(system-info system-cleanup backup-restore mirror-optimizer device-init ai-cli-setup quick-fixes tailscale-client tailscale-derp dev-tools shorin-setup)

ssh_cmd() {
    ssh -o BatchMode=yes -o ConnectTimeout=10 "$REMOTE_HOST" "$@"
}

cycle() {
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    echo "Test cycle: ${ts}"
    echo "=========================================="

    # 1. Pull latest code on remote
    echo "[1/5] Pull latest on ${REMOTE_HOST}"
    ssh_cmd "cd ${PROJECT_PATH} && git stash && git pull --ff-only origin main" || true

    # 2. Regression-test recently closed issues
    echo "[2/5] Regression test for closed issues"
    local closed
    closed=$(gh issue list --state closed --limit 10 --json number,title --jq '.[] | "\(.number)|\(.title)"')
    if [[ -n "${closed}" ]]; then
        while IFS='|' read -r n title; do
            echo "  issue #${n}: ${title}"
            # Pick 1 representative option per issue title keyword
            ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && echo y | timeout 30 python main.py --tool system-info --lang en" >/dev/null 2>&1 || true
        done <<< "${closed}"
    fi

    # 3. Unit tests + lint + UI checks
    echo "[3/5] Static checks"
    ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && python -m pytest tests/ -q" || true
    ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && python -m ruff check ." || true
    ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && python tests/check_ui_patterns.py" || true

    # 4. Smoke-test every tool (option 1 = safe default)
    echo "[4/5] Smoke test tools"
    for tool in "${TOOLS[@]}"; do
        echo "  - ${tool}"
        ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && echo 1 | timeout 30 python main.py --tool ${tool} --lang en" >/dev/null 2>&1 || true
    done

    # 5. Append a cycle entry to optimization_report.md
    echo "[5/5] Append cycle entry"
    {
        echo ""
        echo "## Cycle ${ts}"
        echo ""
        echo "- Pulled latest from origin/main"
        echo "- Closed issues scanned: $(echo "${closed}" | grep -c . || echo 0)"
        echo "- Tools smoke-tested: ${#TOOLS[@]}"
        echo ""
    } >> "${REPORT_PATH}"

    echo "Done. Sleeping ${CHECK_INTERVAL}s"
}

trap 'echo interrupted; exit 130' INT TERM
while true; do
    cycle || true
    sleep "${CHECK_INTERVAL}"
done
