"""System Info — display hardware overview, disk usage, network status, and services.

系统信息 — 显示硬件概览、磁盘使用情况、网络状态和服务信息。
"""

from pathlib import Path

from tools.base import Tool
from . import system_info_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_cmd
from utils.i18n import t
from utils.platform import IS_WINDOWS
from utils.shell import get_windows_shell_cmd
from utils.ui import print_error, print_info, console, prompt_selection, BACK_ACTION

# Menu options for system info queries / 系统信息查询的菜单选项
INFO_OPTIONS = [
    {
        "id": "hardware",
        "name_key": "msg.info_hardware",
        "desc_key": "msg.info_hardware_desc",
    },
    {
        "id": "disk",
        "name_key": "msg.info_disk",
        "desc_key": "msg.info_disk_desc",
    },
    {
        "id": "network",
        "name_key": "msg.info_network",
        "desc_key": "msg.info_network_desc",
    },
    {
        "id": "services",
        "name_key": "msg.info_services",
        "desc_key": "msg.info_services_desc",
    },
    {
        "id": "all",
        "name_key": "msg.info_all",
        "desc_key": "msg.info_all_desc",
    },
]


# Display hardware overview.
#
# 显示硬件概览信息。

def _show_hardware() -> bool:
    print_info(t("msg.info_hardware_running"))

    if IS_WINDOWS:
        return _show_hardware_windows()

    # CPU info / CPU 信息
    code, cpu = run_cmd(["lscpu"])
    if code == 0:
        for line in cpu.split("\n"):
            if "Model name" in line:
                print_info(line.strip())
                break

    # Memory info / 内存信息
    code, mem = run_cmd(["free", "-h"])
    if code == 0:
        lines = mem.split("\n")
        if len(lines) >= 2:
            print_info(lines[1].strip())

    # GPU info (if available) / GPU 信息（如果可用）
    code, gpu = run_cmd(["lspci"])
    if code == 0:
        for line in gpu.split("\n"):
            if "VGA" in line or "3D" in line:
                print_info(line.strip())
                break

    return True


# Display hardware overview on Windows.
#
# 在 Windows 系统上显示硬件概览信息。

def _show_hardware_windows() -> bool:
    # CPU info via WMIC / 通过 WMIC 获取 CPU 信息
    code, cpu = run_cmd(["wmic", "cpu", "get", "name"])
    if code == 0 and cpu:
        lines = cpu.strip().split("\n")
        if len(lines) >= 2:
            print_info(f"CPU: {lines[1].strip()}")

    # Memory info via WMIC / 通过 WMIC 获取内存信息
    code, mem = run_cmd(["wmic", "memorychip", "get", "capacity"])
    if code == 0 and mem:
        lines = mem.strip().split("\n")
        total = 0
        for line in lines[1:]:
            line = line.strip()
            if line.isdigit():
                total += int(line)
        if total > 0:
            total_gb = total / (1024 ** 3)
            print_info(f"Memory: {total_gb:.1f} GB")

    # GPU info via WMIC / 通过 WMIC 获取 GPU 信息
    code, gpu = run_cmd(["wmic", "path", "win32_videocontroller", "get", "name"])
    if code == 0 and gpu:
        lines = gpu.strip().split("\n")
        if len(lines) >= 2:
            print_info(f"GPU: {lines[1].strip()}")

    return True


# Display disk usage.
#
# 显示磁盘使用情况。

def _show_disk() -> bool:
    print_info(t("msg.info_disk_running"))

    if IS_WINDOWS:
        return _show_disk_windows()

    # Disk usage summary / 磁盘使用摘要
    code, disk = run_cmd(["df", "-h", "--type=ext4", "--type=xfs", "--type=btrfs", "--type=ntfs"])
    if code == 0:
        print_info(disk)
    else:
        # Fallback to basic df / 回退到基本 df 命令
        code, disk = run_cmd(["df", "-h"])
        if code == 0:
            print_info(disk)

    # Largest directories in home / 主目录中最大的目录
    print_info(t("msg.info_disk_home"))
    code, home_usage = run_cmd(["du", "-sh", "--max-depth=1", str(Path.home())])
    if code == 0 and home_usage:
        lines = home_usage.strip().split("\n")
        lines.sort(reverse=True)
        for line in lines[:6]:  # Skip the home dir itself, show top 5
            if not line.endswith(str(Path.home())):
                print_info(line)

    return True


# Display disk usage on Windows.
#
# 在 Windows 系统上显示磁盘使用情况。

def _show_disk_windows() -> bool:
    # Disk usage via WMIC / 通过 WMIC 获取磁盘使用情况
    code, disk = run_cmd(["wmic", "logicaldisk", "get", "size,freespace,caption"])
    if code == 0 and disk:
        lines = disk.strip().split("\n")
        print_info(f"{'Drive':<8} {'Free':<12} {'Total':<12}")
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    drive = parts[0]
                    free = int(parts[1]) / (1024 ** 3)
                    total = int(parts[2]) / (1024 ** 3)
                    print_info(f"{drive:<8} {free:.1f} GB{'':<4} {total:.1f} GB")
                except (ValueError, IndexError):
                    pass

    # Largest directories in home / 主目录中最大的目录
    print_info(t("msg.info_disk_home"))
    home = Path.home()
    try:
        dirs = sorted(
            [(d, sum(f.stat().st_size for f in d.rglob("*") if f.is_file()))
             for d in home.iterdir() if d.is_dir()],
            key=lambda x: x[1],
            reverse=True,
        )
        for d, size in dirs[:5]:
            size_mb = size / (1024 ** 2)
            print_info(f"{d.name:<30} {size_mb:.1f} MB")
    except (PermissionError, OSError):
        pass

    return True


# Display network status.
#
# 显示网络状态信息。

def _show_network() -> bool:
    print_info(t("msg.info_network_running"))

    if IS_WINDOWS:
        return _show_network_windows()

    # IP addresses / IP 地址
    code, ip = run_cmd(["ip", "-brief", "addr"])
    if code == 0:
        print_info(ip)

    # DNS servers / DNS 服务器
    code, dns = run_cmd(["resolvectl", "status"])
    if code == 0:
        for line in dns.split("\n"):
            if "DNS Servers" in line:
                print_info(line.strip())
                break

    # Active connections / 活动连接
    code, conn = run_cmd(["ss", "-tuln"])
    if code == 0:
        lines = conn.split("\n")
        if len(lines) > 1:
            print_info(t("msg.info_network_connections"))
            for line in lines[:6]:  # Show first 5 connections
                print_info(line)

    return True


# Display network status on Windows.
#
# 在 Windows 系统上显示网络状态信息。

def _show_network_windows() -> bool:
    # IP addresses / IP 地址
    code, ip = run_cmd(["ipconfig"])
    if code == 0 and ip:
        # Show just the key lines / 仅显示关键行
        for line in ip.split("\n"):
            line = line.strip()
            if "IPv4" in line or "Ethernet" in line or "Wi-Fi" in line:
                print_info(line)

    # Active connections / 活动连接
    code, conn = run_cmd(["netstat", "-an"])
    if code == 0 and conn:
        lines = conn.strip().split("\n")
        if len(lines) > 1:
            print_info(t("msg.info_network_connections"))
            for line in lines[1:6]:  # Show first 5 connections
                print_info(line.strip())

    return True


# Display running services.
#
# 显示正在运行的服务信息。

def _show_services() -> bool:
    print_info(t("msg.info_services_running"))

    if IS_WINDOWS:
        return _show_services_windows()

    # Failed services / 失败的服务
    code, failed = run_cmd(["systemctl", "--failed"])
    if code == 0:
        lines = failed.split("\n")
        if len(lines) > 1:
            print_info(t("msg.info_services_failed"))
            for line in lines[1:6]:  # Show first 5 failed services
                print_info(line)

    # Running services count / 正在运行的服务数量
    code, count = run_cmd(["systemctl", "list-units", "--type=service", "--state=running", "--no-legend", "--no-pager"])
    if code == 0:
        running_count = len(count.strip().split("\n"))
        print_info(t("msg.info_services_count", count=running_count))

    # Recent service logs / 最近的服务日志
    code, logs = run_cmd(["journalctl", "-p", "err", "-n", "5", "--no-pager"])
    if code == 0 and logs:
        print_info(t("msg.info_services_recent_errors"))
        print_info(logs)

    return True


# Display running services on Windows.
#
# 在 Windows 系统上显示正在运行的服务信息。

def _show_services_windows() -> bool:
    # Running services via sc / 通过 sc 查询正在运行的服务
    code, services = run_cmd(["sc", "query", "type=", "service", "state=", "running"])
    if code == 0 and services:
        lines = services.strip().split("\n")
        running = [line for line in lines if "SERVICE_NAME" in line]
        print_info(t("msg.info_services_count", count=len(running)))
        # Show first 5 / 显示前 5 个
        for line in running[:5]:
            name = line.split(":", 1)[-1].strip() if ":" in line else line.strip()
            print_info(f"  {name}")

    # Recent event log errors / 最近的事件日志错误
    win_shell = get_windows_shell_cmd()
    code, logs = run_cmd([
        win_shell, "-Command",
        "Get-EventLog -LogName System -EntryType Error -Newest 5 | Format-Table -AutoSize"
    ])
    if code == 0 and logs:
        print_info(t("msg.info_services_recent_errors"))
        for line in logs.strip().split("\n")[:6]:
            print_info(line.strip())

    return True


class SystemInfo(Tool):
    """System information tool for displaying hardware, disk, network, and services.

    系统信息工具，用于显示硬件、磁盘、网络和服务信息。
    """
    name = "system-info"  # Tool identifier / 工具标识符
    display_name = "System Info"  # Display name shown in menus / 在菜单中显示的名称
    description = "Display hardware overview, disk usage, network status, and services"  # Tool description / 工具描述
    distros = ["arch", "debian", "fedora", "suse", "unknown", "windows"]  # Supported distros / 支持的发行版
    platforms = ["linux", "windows"]  # Supported platforms / 支持的平台
    mutates_system = False  # Does not modify system / 不修改系统
    safe_for_run_all = True  # Safe to run all info at once / 可以安全地一次运行所有信息

    # Run all system info displays in sequence.
    #
    # 依次运行所有系统信息显示。

    def run_all(self) -> bool | None:
        _show_hardware()
        console.print()
        _show_disk()
        console.print()
        _show_network()
        console.print()
        _show_services()
        return True

    # Run the tool interactively, prompting user to select which info to display.
    #
    # 交互式运行工具，提示用户选择要显示的信息类型。

    def run(self) -> bool | None:
        choice = prompt_selection(t("msg.info_select"), INFO_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        console.print()

        if choice == "hardware":
            return _show_hardware()
        elif choice == "disk":
            return _show_disk()
        elif choice == "network":
            return _show_network()
        elif choice == "services":
            return _show_services()
        elif choice == "all":
            return self.run_all()

        print_error(t("ui.invalid_selection"))
        return False
