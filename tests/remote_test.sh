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
    local host="$1"
    shift
    local cmd="$*"
    local sudo_pass="${TEST_SUDO_PASS:-$TEST_PASS}"

    if [[ -n "$sudo_pass" ]]; then
        local quoted_pass
        quoted_pass="$(printf '%q' "$sudo_pass")"
        cmd="export LST_SUDO_PASSWORD=$quoted_pass; printf '%s\n' $quoted_pass | sudo -S -v >/dev/null 2>&1; $cmd"
    fi

    sshpass -p "$TEST_PASS" ssh -o StrictHostKeyChecking=no "$TEST_USER@$host" \
        "bash -lc $(printf '%q' "$cmd")"
}

run_remote_sudo() {
    local host="$1"
    shift
    local sudo_pass="${TEST_SUDO_PASS:-$TEST_PASS}"
    local quoted_pass
    quoted_pass="$(printf '%q' "$sudo_pass")"
    run_remote "$host" "printf '%s\n' $quoted_pass | sudo -S -p '' $*"
}

sync_project() {
    local host="$1"
    echo "==> Syncing project to $host..."
    if run_remote "$host" "command -v rsync >/dev/null"; then
        sshpass -p "$TEST_PASS" rsync -az --delete \
            --exclude '__pycache__' \
            --exclude '.pytest_cache' \
            --exclude '.ruff_cache' \
            --exclude '.venv' \
            --exclude 'config.json' \
            --exclude 'tests/test_config.py' \
            --exclude 'tests/test_config.sh' \
            --exclude '.git' \
            "$PROJECT_DIR/" "$TEST_USER@$host:~/LinuxScriptToolbox/"
    else
        echo "==> rsync not found on $host; using tar fallback..."
        tar -C "$PROJECT_DIR" \
            --exclude='.git' \
            --exclude='.pytest_cache' \
            --exclude='.ruff_cache' \
            --exclude='.venv' \
            --exclude='config.json' \
            --exclude='tests/test_config.py' \
            --exclude='tests/test_config.sh' \
            --exclude='*/__pycache__' \
            -czf - . | sshpass -p "$TEST_PASS" ssh -o StrictHostKeyChecking=no "$TEST_USER@$host" \
                "bash -lc 'mkdir -p ~/LinuxScriptToolbox && find ~/LinuxScriptToolbox -mindepth 1 -maxdepth 1 ! -name .venv -exec rm -rf {} + && tar -C ~/LinuxScriptToolbox -xzf -'"
    fi
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
    # Use --tool parameter instead of menu position
    run_remote "$host" "cd ~/LinuxScriptToolbox && python3 main.py --tool device-init" || true
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

    # Test ARM GCC installation (sub-menu option 1)
    echo "==> Installing ARM GCC toolchain..."
    run_remote "$host" "cd ~/LinuxScriptToolbox && printf '1\n' | python3 main.py --tool dev-tools" || true
    echo ""
    echo "==> Verifying ARM GCC:"
    run_remote "$host" "arm-none-eabi-gcc --version | head -1" || echo "arm-none-eabi-gcc not found"
    echo ""

    # Test RISC-V GCC installation (sub-menu option 2)
    echo "==> Installing RISC-V GCC toolchain..."
    run_remote "$host" "cd ~/LinuxScriptToolbox && printf '2\n' | python3 main.py --tool dev-tools" || true
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

    # Use --tool parameter and select STM32CubeMX Wayland Fix (option 1)
    echo "==> Running STM32CubeMX Wayland Fix..."
    run_remote "$host" "cd ~/LinuxScriptToolbox && printf '1\n\n' | python3 main.py --tool quick-fixes" || true

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

    local pm
    local sources_path
    local refresh_cmd

    if run_remote "$host" "test -f /etc/pacman.d/mirrorlist" 2>/dev/null; then
        pm="pacman"
        sources_path="/etc/pacman.d/mirrorlist"
        refresh_cmd="sudo pacman -Sy --noconfirm"
    elif run_remote "$host" "test -f /etc/apt/sources.list.d/ubuntu.sources" 2>/dev/null; then
        pm="apt"
        sources_path="/etc/apt/sources.list.d/ubuntu.sources"
        refresh_cmd="sudo apt update"
    elif run_remote "$host" "test -f /etc/apt/sources.list" 2>/dev/null; then
        pm="apt"
        sources_path="/etc/apt/sources.list"
        refresh_cmd="sudo apt update"
    elif run_remote "$host" "test -d /etc/yum.repos.d" 2>/dev/null; then
        pm="dnf"
        sources_path="/etc/yum.repos.d"
        refresh_cmd="sudo dnf makecache"
    elif run_remote "$host" "test -d /etc/zypp/repos.d" 2>/dev/null; then
        pm="zypper"
        sources_path="/etc/zypp/repos.d"
        refresh_cmd="sudo zypper refresh"
    else
        echo "No supported package manager config found."
        return 1
    fi
    echo "==> Package manager: $pm"
    echo "==> Sources file: $sources_path"
    echo "==> BEFORE:"
    run_remote "$host" "if test -d $sources_path; then ls -1 $sources_path; else head -40 $sources_path; fi"
    echo ""
    # Use --tool parameter instead of menu position
    run_remote "$host" "cd ~/LinuxScriptToolbox && python3 main.py --tool mirror-optimizer" || true
    echo ""
    echo "==> AFTER:"
    run_remote "$host" "if test -d $sources_path; then ls -1 $sources_path; else head -40 $sources_path; fi"
    echo ""
    echo "==> Package metadata refresh test:"
    run_remote "$host" "$refresh_cmd 2>&1 | tail -20"
    echo ""
    echo "==> Restoring backup..."
    if [[ "$pm" == "dnf" || "$pm" == "zypper" ]]; then
        run_remote "$host" "for backup in $sources_path/*.repo.bak; do test -e \"\$backup\" || continue; printf '%s\n' \"\$LST_SUDO_PASSWORD\" | sudo -S -p '' cp \"\$backup\" \"\${backup%.bak}\"; done"
    else
        run_remote_sudo "$host" "cp ${sources_path}.bak $sources_path"
    fi
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
