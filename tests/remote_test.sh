#!/bin/bash
# Remote test script for LinuxScriptToolbox
# Usage: ./tests/remote_test.sh [tool_name] [host]
#   tool_name: ssh-init | dev-tools | quick-fixes | mirror-opt | all (default: all)
#   host:      run on a specific host only (optional)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/test_config.sh"

run_remote() {
    sshpass -p "$TEST_PASS" ssh -o StrictHostKeyChecking=no "$TEST_USER@$1" "${@:2}"
}

sync_project() {
    local host="$1"
    echo "==> Syncing project to $host..."
    sshpass -p "$TEST_PASS" rsync -az --delete \
        --exclude '__pycache__' \
        --exclude 'config.json' \
        --exclude '.git' \
        "$PROJECT_DIR/" "$TEST_USER@$host:~/LinuxScriptToolbox/"
    echo "==> Sync complete."
}

# Detect SSH service name: Arch uses "sshd", Debian/Ubuntu uses "ssh"
detect_ssh_service() {
    local host="$1"
    if run_remote "$host" "systemctl cat sshd.service" &>/dev/null; then
        echo "sshd"
    else
        echo "ssh"
    fi
}

test_ssh_init() {
    local host="$1"
    local svc
    svc=$(detect_ssh_service "$host")
    echo ""
    echo "========================================"
    echo "  Test: Device Init (SSH) [$host]"
    echo "========================================"
    echo "==> Detected SSH service: $svc"
    echo "==> SSH status BEFORE:"
    run_remote "$host" "systemctl is-active $svc || true; systemctl is-enabled $svc || true"
    echo ""
    run_remote "$host" "cd ~/LinuxScriptToolbox && echo '1' | python3 main.py" || true
    echo ""
    echo "==> SSH status AFTER:"
    run_remote "$host" "systemctl is-active $svc; systemctl is-enabled $svc"
}

test_dev_tools() {
    local host="$1"
    echo ""
    echo "========================================"
    echo "  Test: Dev Tools Setup [$host]"
    echo "========================================"

    # NOTE: Menu position '1' assumes dev-tools is the first tool discovered
    # by pkgutil.walk_packages (common/ directory, alphabetical order).
    # If tools are added/reordered, this position may need updating.
    #
    # First '1' = main menu tool selection, second '1'/'2' = dev-tools sub-menu.

    # Test ARM GCC installation (sub-menu option 1)
    echo "==> Installing ARM GCC toolchain..."
    run_remote "$host" "cd ~/LinuxScriptToolbox && printf '1\n1\n' | python3 main.py" || true
    echo ""
    echo "==> Verifying ARM GCC:"
    run_remote "$host" "arm-none-eabi-gcc --version | head -1" || echo "arm-none-eabi-gcc not found"
    echo ""

    # Test RISC-V GCC installation (sub-menu option 2)
    echo "==> Installing RISC-V GCC toolchain..."
    run_remote "$host" "cd ~/LinuxScriptToolbox && printf '1\n2\n' | python3 main.py" || true
    echo ""
    echo "==> Verifying RISC-V GCC:"
    run_remote "$host" "riscv64-elf-gcc --version 2>/dev/null | head -1 || riscv64-linux-gnu-gcc --version 2>/dev/null | head -1 || echo 'RISC-V GCC not found'"
}

test_quick_fixes() {
    local host="$1"
    echo ""
    echo "========================================"
    echo "  Test: Quick Fixes [$host]"
    echo "========================================"

    # Clean up any previous wrappers
    run_remote "$host" "rm -f ~/.local/bin/STM32CubeMX* ~/.local/bin/stm32cubemx ~/.local/share/applications/stm32cubemx.desktop" || true

    # NOTE: Menu position '4' assumes quick-fixes is the 4th tool discovered
    # by pkgutil.walk_packages (common/ directory, alphabetical order).
    # If tools are added/reordered, this position may need updating.
    #
    # First '4' = main menu quick-fixes, second '1' = STM32CubeMX Wayland Fix.

    echo "==> Running STM32CubeMX Wayland Fix..."
    run_remote "$host" "cd ~/LinuxScriptToolbox && printf '4\n1\n\n' | python3 main.py" || true

    echo ""
    echo "==> Verifying wrapper script:"
    run_remote "$host" "test -x ~/.local/bin/STM32CubeMX && echo 'wrapper OK' || echo 'wrapper NOT FOUND'"

    echo "==> Verifying lowercase symlink:"
    run_remote "$host" "test -L ~/.local/bin/stm32cubemx && echo 'symlink OK' || echo 'symlink NOT FOUND'"

    echo "==> Verifying .desktop file:"
    run_remote "$host" "test -f ~/.local/share/applications/stm32cubemx.desktop && echo 'desktop OK' || echo 'desktop NOT FOUND'"

    echo "==> Verifying PATH resolution:"
    run_remote "$host" "which STM32CubeMX && which stm32cubemx"
}

test_mirror_opt() {
    local host="$1"
    echo ""
    echo "========================================"
    echo "  Test: Mirror Optimizer [$host]"
    echo "========================================"

    # Detect format
    local sources_path
    if run_remote "$host" "test -f /etc/apt/sources.list.d/ubuntu.sources" 2>/dev/null; then
        sources_path="/etc/apt/sources.list.d/ubuntu.sources"
    else
        sources_path="/etc/apt/sources.list"
    fi
    echo "==> Sources file: $sources_path"
    echo "==> BEFORE:"
    run_remote "$host" "cat $sources_path"
    echo ""
    run_remote "$host" "cd ~/LinuxScriptToolbox && echo '2' | python3 main.py" || true
    echo ""
    echo "==> AFTER:"
    run_remote "$host" "cat $sources_path"
    echo ""
    echo "==> apt update test:"
    run_remote "$host" "sudo apt update 2>&1 | tail -5"
    echo ""
    echo "==> Restoring backup..."
    run_remote "$host" "sudo cp ${sources_path}.bak $sources_path"
    echo "==> Restored."
}

test_all() {
    local host="$1"
    test_ssh_init "$host"
    test_dev_tools "$host"
    test_quick_fixes "$host"
    test_mirror_opt "$host"
}

# Main
TOOL="${1:-all}"
SPECIFIED_HOST="$2"

if [[ -n "$SPECIFIED_HOST" ]]; then
    HOSTS=("$SPECIFIED_HOST")
else
    HOSTS=("${TEST_HOSTS[@]}")
fi

for HOST in "${HOSTS[@]}"; do
    sync_project "$HOST"

    case "$TOOL" in
        ssh-init)    test_ssh_init "$HOST" ;;
        dev-tools)   test_dev_tools "$HOST" ;;
        quick-fixes) test_quick_fixes "$HOST" ;;
        mirror-opt)  test_mirror_opt "$HOST" ;;
        all)         test_all "$HOST" ;;
        *)           echo "Usage: $0 [ssh-init|dev-tools|quick-fixes|mirror-opt|all] [host]"; exit 1 ;;
    esac
done

echo ""
echo "==> All tests done."
