"""System Info — display hardware overview, disk usage, network status, and services."""

from pathlib import Path

from tools.base import Tool
from utils.cmd_utils import run_cmd
from utils.i18n import t
from utils.ui import print_error, print_info, console, prompt_selection, BACK_ACTION

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


def _show_hardware() -> bool:
    """Display hardware overview."""
    print_info(t("msg.info_hardware_running"))

    # CPU info
    code, cpu = run_cmd(["lscpu"])
    if code == 0:
        for line in cpu.split("\n"):
            if "Model name" in line:
                print_info(line.strip())
                break

    # Memory info
    code, mem = run_cmd(["free", "-h"])
    if code == 0:
        lines = mem.split("\n")
        if len(lines) >= 2:
            print_info(lines[1].strip())

    # GPU info (if available)
    code, gpu = run_cmd(["lspci"])
    if code == 0:
        for line in gpu.split("\n"):
            if "VGA" in line or "3D" in line:
                print_info(line.strip())
                break

    return True


def _show_disk() -> bool:
    """Display disk usage."""
    print_info(t("msg.info_disk_running"))

    # Disk usage summary
    code, disk = run_cmd(["df", "-h", "--type=ext4", "--type=xfs", "--type=btrfs", "--type=ntfs"])
    if code == 0:
        print_info(disk)
    else:
        # Fallback to basic df
        code, disk = run_cmd(["df", "-h"])
        if code == 0:
            print_info(disk)

    # Largest directories in home
    print_info(t("msg.info_disk_home"))
    code, home_usage = run_cmd(["du", "-sh", str(Path.home() / "*")])
    if code == 0:
        # Sort by size and show top 5
        lines = home_usage.strip().split("\n")
        lines.sort(reverse=True)
        for line in lines[:5]:
            print_info(line)

    return True


def _show_network() -> bool:
    """Display network status."""
    print_info(t("msg.info_network_running"))

    # IP addresses
    code, ip = run_cmd(["ip", "-brief", "addr"])
    if code == 0:
        print_info(ip)

    # DNS servers
    code, dns = run_cmd(["resolvectl", "status"])
    if code == 0:
        for line in dns.split("\n"):
            if "DNS Servers" in line:
                print_info(line.strip())
                break

    # Active connections
    code, conn = run_cmd(["ss", "-tuln"])
    if code == 0:
        lines = conn.split("\n")
        if len(lines) > 1:
            print_info(t("msg.info_network_connections"))
            for line in lines[:6]:  # Show first 5 connections
                print_info(line)

    return True


def _show_services() -> bool:
    """Display running services."""
    print_info(t("msg.info_services_running"))

    # Failed services
    code, failed = run_cmd(["systemctl", "--failed"])
    if code == 0:
        lines = failed.split("\n")
        if len(lines) > 1:
            print_info(t("msg.info_services_failed"))
            for line in lines[1:6]:  # Show first 5 failed services
                print_info(line)

    # Running services count
    code, count = run_cmd(["systemctl", "list-units", "--type=service", "--state=running", "--no-legend", "--no-pager"])
    if code == 0:
        running_count = len(count.strip().split("\n"))
        print_info(t("msg.info_services_count", count=running_count))

    # Recent service logs
    code, logs = run_cmd(["journalctl", "-p", "err", "-n", "5", "--no-pager"])
    if code == 0 and logs:
        print_info(t("msg.info_services_recent_errors"))
        print_info(logs)

    return True


class SystemInfo(Tool):
    name = "system-info"
    display_name = "System Info"
    description = "Display hardware overview, disk usage, network status, and services"
    distros = ["arch", "debian", "fedora", "suse", "unknown"]

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
            _show_hardware()
            console.print()
            _show_disk()
            console.print()
            _show_network()
            console.print()
            _show_services()
            return True

        print_error(t("ui.invalid_selection"))
        return False
