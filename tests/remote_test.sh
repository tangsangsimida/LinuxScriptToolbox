#!/bin/bash
# Remote test script for LinuxScriptToolbox
# Usage: ./tests/remote_test.sh [tool_name]
#   tool_name: ssh-init | mirror-opt | all (default: all)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/test_config.sh"

run_remote() {
    sshpass -p "$TEST_PASS" ssh -o StrictHostKeyChecking=no "$TEST_USER@$TEST_HOST" "$@"
}

sync_project() {
    echo "==> Syncing project to remote..."
    sshpass -p "$TEST_PASS" rsync -az --delete \
        --exclude '__pycache__' \
        --exclude 'config.json' \
        --exclude '.git' \
        "$PROJECT_DIR/" "$TEST_USER@$TEST_HOST:~/LinuxScriptToolbox/"
    echo "==> Sync complete."
}

test_ssh_init() {
    echo ""
    echo "========================================"
    echo "  Test: Device Init (SSH)"
    echo "========================================"
    echo "==> SSH status BEFORE:"
    run_remote "systemctl is-active ssh || true; systemctl is-enabled ssh || true"
    echo ""
    run_remote "cd ~/LinuxScriptToolbox && echo '1' | python3 main.py" || true
    echo ""
    echo "==> SSH status AFTER:"
    run_remote "systemctl is-active ssh; systemctl is-enabled ssh"
}

test_mirror_opt() {
    echo ""
    echo "========================================"
    echo "  Test: Mirror Optimizer"
    echo "========================================"

    # Detect format
    local sources_path
    if run_remote "test -f /etc/apt/sources.list.d/ubuntu.sources" 2>/dev/null; then
        sources_path="/etc/apt/sources.list.d/ubuntu.sources"
    else
        sources_path="/etc/apt/sources.list"
    fi
    echo "==> Sources file: $sources_path"
    echo "==> BEFORE:"
    run_remote "cat $sources_path"
    echo ""
    run_remote "cd ~/LinuxScriptToolbox && echo '2' | python3 main.py" || true
    echo ""
    echo "==> AFTER:"
    run_remote "cat $sources_path"
    echo ""
    echo "==> apt update test:"
    run_remote "sudo apt update 2>&1 | tail -5"
    echo ""
    echo "==> Restoring backup..."
    run_remote "sudo cp ${sources_path}.bak $sources_path"
    echo "==> Restored."
}

test_all() {
    test_ssh_init
    test_mirror_opt
}

# Main
sync_project

case "${1:-all}" in
    ssh-init)   test_ssh_init ;;
    mirror-opt) test_mirror_opt ;;
    all)        test_all ;;
    *)          echo "Usage: $0 [ssh-init|mirror-opt|all]"; exit 1 ;;
esac

echo ""
echo "==> All tests done."
