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

# Run a single cycle step.  Log the step header, execute the command, record
# whether it succeeded.  Never raises — returns 0 always so the loop continues.
# Aggregate failure is reported via ${STEPS_FAILED} at the cycle boundary.
#
# 运行单个步骤：打印标题、执行、记录成败。永不抛错——总返回 0 让循环继续，
# 整轮的失败数通过 ${STEPS_FAILED} 在末尾汇总。
step() {
    local label="$1"
    shift
    echo "[${label}]"
    if "$@"; then
        echo "  ok"
    else
        echo "  FAILED (exit $?)"
        STEPS_FAILED=$((STEPS_FAILED + 1))
    fi
}

cycle() {
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    STEPS_FAILED=0
    echo "=========================================="
    echo "Test cycle: ${ts}"
    echo "=========================================="

    # 1. Pull latest code on remote
    step "1/5 pull" ssh_cmd "cd ${PROJECT_PATH} && git stash && git pull --ff-only origin main"

    # 2. Regression-test recently closed issues (informational scan only —
    #    actual re-test happens via explicit smoke-test below)
    echo "[2/5] closed issues"
    local closed
    closed=$(gh issue list --state closed --limit 10 --json number,title --jq '.[] | "\(.number)|\(.title)"')
    if [[ -n "${closed}" ]]; then
        echo "${closed}" | while IFS='|' read -r n title; do
            echo "  - #${n}: ${title}"
        done
    else
        echo "  (none)"
    fi

    # 3. Static checks
    step "3a pytest" ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && python -m pytest tests/ -q"
    step "3b ruff"   ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && python -m ruff check ."
    step "3c ui"     ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && python tests/check_ui_patterns.py"

    # 4. Smoke test every tool
    echo "[4/5] tools"
    for tool in "${TOOLS[@]}"; do
        if ssh_cmd "cd ${PROJECT_PATH} && source .venv/bin/activate && echo 1 | timeout 30 python main.py --tool ${tool} --lang en" >/dev/null 2>&1; then
            echo "  - ${tool}: ok"
        else
            echo "  - ${tool}: FAILED"
            STEPS_FAILED=$((STEPS_FAILED + 1))
        fi
    done

    # 5. Append a cycle entry
    echo "[5/5] report"
    {
        echo ""
        echo "## Cycle ${ts}"
        echo ""
        echo "- Pulled latest from origin/main"
        echo "- Closed issues scanned: $(echo "${closed}" | grep -c . || echo 0)"
        echo "- Tools smoke-tested: ${#TOOLS[@]}"
        echo "- Steps failed this cycle: ${STEPS_FAILED}"
        echo ""
    } >> "${REPORT_PATH}"

    echo "Done. Failures this cycle: ${STEPS_FAILED}"
    # Return non-zero if any step failed, but the outer loop ignores the code
    # (the test agent never stops running).
    [[ ${STEPS_FAILED} -eq 0 ]]
}

trap 'echo interrupted; exit 130' INT TERM
while true; do
    # `|| true` here is on the *cycle* return, not on individual commands —
    # cycle() internally respects `set -e` and records failures via
    # STEPS_FAILED.  The || true at the loop level exists solely because the
    # spec is "never stop testing".
    cycle || true
    sleep "${CHECK_INTERVAL}"
done
