"""Device initialization tool — SSH access, password, firewall, python alias.

设备初始化工具 — SSH 访问、密码、防火墙、Python 别名。

Supports Linux (arch/debian/fedora/suse) and Windows.
On Windows, uses PowerShell commands and registry edits for OpenSSH Server setup.
On Linux, uses systemd and distro-specific package managers.

支持 Linux（arch/debian/fedora/suse）和 Windows。
Windows 上使用 PowerShell 命令和注册表配置 OpenSSH Server。
Linux 上使用 systemd 和发行版专属包管理器。
"""

import getpass
import socket
import platform as platform_mod
from pathlib import Path

from tools.base import Tool
from . import device_init_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_cmd, run_cmd_with_stdin, run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.platform import IS_WINDOWS, command_exists
from utils.sudo_utils import write_file, copy_file
from utils.ui import (
    print_success,
    print_error,
    print_info,
    print_warning,
    confirm,
    console,
    prompt_selection,
    BACK_ACTION,
)

DISTRO_CONFIG = {
    "arch": {"service": "sshd", "package": "openssh"},
    "debian": {"service": "ssh", "package": "openssh-server"},
    "fedora": {"service": "sshd", "package": "openssh-server"},
    "suse": {"service": "sshd", "package": "openssh"},
    "windows": {"service": "sshd", "package": "OpenSSH.Server~~~~0.0.1.0"},
}

PYTHON_SYMLINK = Path("/usr/local/bin/python")
SSHD_CONFIG = Path("/etc/ssh/sshd_config")

INIT_OPTIONS = [
    {
        "id": "all",
        "name_key": "msg.init_all",
        "desc_key": "msg.init_all_desc",
    },
    {
        "id": "preview",
        "name_key": "msg.init_preview",
        "desc_key": "msg.init_preview_desc",
    },
    {
        "type": "separator",
        "text_key": "msg.sep_ssh_service",
    },
    {
        "id": "install-ssh",
        "name_key": "msg.init_install_ssh",
        "desc_key": "msg.init_install_ssh_desc",
    },
    {
        "id": "start-ssh",
        "name_key": "msg.init_start_ssh",
        "desc_key": "msg.init_start_ssh_desc",
    },
    {
        "id": "enable-ssh",
        "name_key": "msg.init_enable_ssh",
        "desc_key": "msg.init_enable_ssh_desc",
    },
    {
        "id": "config-sshd",
        "name_key": "msg.init_config_sshd",
        "desc_key": "msg.init_config_sshd_desc",
    },
    {
        "id": "open-firewall",
        "name_key": "msg.init_open_firewall",
        "desc_key": "msg.init_open_firewall_desc",
    },
    {
        "type": "separator",
        "text_key": "msg.sep_other",
    },
    {
        "id": "set-password",
        "name_key": "msg.init_set_password",
        "desc_key": "msg.init_set_password_desc",
    },
    {
        "id": "python-alias",
        "name_key": "msg.init_python_alias",
        "desc_key": "msg.init_python_alias_desc",
    },
    {
        "id": "connection-info",
        "name_key": "msg.init_connection_info",
        "desc_key": "msg.init_connection_info_desc",
    },
]


# ── Windows helpers ─────────────────────────────────────────────

# Execute a PowerShell command and return (returncode, output).
#
# 执行 PowerShell 命令并返回 (返回码, 输出)。
#
# Args:
#     command: PowerShell command string to execute / 要执行的 PowerShell 命令字符串
#     check: If True and returncode != 0, print error / 为 True 且返回码非 0 时打印错误
#
# Returns:
#     (returncode, stdout_stripped) / (返回码, 去除空白的 stdout)
def _run_ps(command: str, check: bool = True) -> tuple[int, str]:
    code, output = run_cmd(["powershell", "-NoProfile", "-Command", command])
    if check and code != 0:
        print_error(t("msg.win_ps_failed", cmd=command[:60], err=output))
    return code, output


# ── Linux helpers ───────────────────────────────────────────────

# Return service/package config for the given distro.

def _get_config(distro: str) -> dict:
    return DISTRO_CONFIG.get(distro, DISTRO_CONFIG["debian"])


# Check if a package is installed via the system package manager.
#
# 通过系统包管理器检查软件包是否已安装。
#
# Args:
#     package: Package name to check / 要检查的软件包名称
#     distro: Distribution identifier / 发行版标识符
#
# Returns:
#     True if installed / 已安装返回 True
def _is_installed(package: str, distro: str) -> bool:
    if distro == "arch":
        code, _ = run_cmd(["pacman", "-Qi", package])
    elif distro in ("fedora", "suse"):
        code, _ = run_cmd(["rpm", "-q", package])
    else:
        code, _ = run_cmd(["dpkg", "-s", package])
    return code == 0


# Install a package using the distro's package manager.
#
# 使用发行版的包管理器安装软件包。
#
# Args:
#     package: Package name to install / 要安装的软件包名称
#     distro: Distribution identifier / 发行版标识符
#
# Returns:
#     True if installed successfully / 安装成功返回 True
def _install_package(package: str, distro: str) -> bool:
    print_info(t("msg.installing", package=package))
    if distro == "arch":
        code = run_verbose(["sudo", "pacman", "-S", "--noconfirm", package])
    elif distro == "fedora":
        code = run_verbose(["sudo", "dnf", "install", "-y", package])
    elif distro == "suse":
        code = run_verbose(["sudo", "zypper", "install", "-y", package])
    else:
        code = run_verbose(["sudo", "apt-get", "install", "-y", package])
    return code == 0


# Check if a systemd service is currently running.

def _is_active(service: str) -> bool:
    code, _ = run_cmd(["systemctl", "is-active", service])
    return code == 0


# Check if a systemd service is enabled on boot.

def _is_enabled(service: str) -> bool:
    code, _ = run_cmd(["systemctl", "is-enabled", service])
    return code == 0


# Check if user has a password set by reading shadow file.

def _has_password(user: str) -> bool:
    code, out = run_cmd(["sudo", "grep", f"^{user}:", "/etc/shadow"])
    if code != 0:
        return False
    fields = out.split(":")
    if len(fields) < 2:
        return False
    pw_hash = fields[1]
    return pw_hash not in ("!", "!!", "", "*")


# Prompt for and set user password (Linux).

def _set_password(user: str) -> None:
    try:
        pw1 = getpass.getpass(t("msg.enter_password"))
        pw2 = getpass.getpass(t("msg.confirm_password"))
    except (KeyboardInterrupt, EOFError):
        print()
        return
    if pw1 != pw2:
        print_warning(t("msg.password_mismatch"))
        return
    code, _ = run_cmd_with_stdin(["sudo", "chpasswd"], f"{user}:{pw1}")
    if code != 0:
        print_error(t("msg.password_set_failed"))
        return
    print_success(t("msg.password_set_success", user=user))


# Ensure PasswordAuthentication yes in sshd_config (Linux).

def _configure_sshd() -> None:
    print_info(t("msg.checking_sshd_config"))

    code, content = run_cmd(["sudo", "cat", str(SSHD_CONFIG)])
    if code != 0:
        return

    if "PasswordAuthentication no" in content:
        backup = str(SSHD_CONFIG) + ".bak"
        copy_file(str(SSHD_CONFIG), backup)
        print_info(t("msg.sshd_config_backup", path=backup))

        new_content = content.replace("PasswordAuthentication no", "PasswordAuthentication yes")
        write_file(str(SSHD_CONFIG), new_content)

        run_cmd(["sudo", "systemctl", "restart", "sshd"])
        print_success(t("msg.password_auth_enabled"))
        print_success(t("msg.sshd_restarted"))
    else:
        print_info(t("msg.password_auth_already"))


# Allow SSH through the active firewall (Linux).

def _open_firewall_ssh_linux() -> None:
    print_info(t("msg.step_firewall"))

    fw = None
    if command_exists("ufw"):
        fw = "ufw"
    elif command_exists("firewall-cmd"):
        fw = "firewalld"
    elif command_exists("iptables"):
        fw = "iptables"

    if fw is None:
        print_info(t("msg.firewall_no_active"))
        return

    print_info(t("msg.firewall_detected", fw=fw))
    if not confirm(t("msg.firewall_allow_ssh")):
        return

    if fw == "ufw":
        run_cmd(["sudo", "ufw", "allow", "ssh"])
    elif fw == "firewalld":
        run_cmd(["sudo", "firewall-cmd", "--permanent", "--add-service=ssh"])
        run_cmd(["sudo", "firewall-cmd", "--reload"])
    elif fw == "iptables":
        run_cmd(["sudo", "iptables", "-I", "INPUT", "-p", "tcp", "--dport", "22", "-j", "ACCEPT"])

    print_success(t("msg.firewall_rule_added"))


# Create persistent 'python' symlink if python3 exists but python doesn't (Linux).

def _setup_python_alias_linux() -> None:
    has_python3 = command_exists("python3")
    has_python = command_exists("python")

    if not has_python3:
        print_warning(t("msg.python3_not_found"))
        return

    if has_python:
        print_info(t("msg.python_already_exists"))
        return

    _, python3_path = run_cmd(["which", "python3"])
    run_cmd(["sudo", "ln", "-sf", python3_path, str(PYTHON_SYMLINK)])
    print_success(t("msg.python_alias_created", path=str(PYTHON_SYMLINK)))


# ── Individual step functions ───────────────────────────────────

# Install OpenSSH server if not already present.

def _step_install_ssh(distro: str) -> bool:
    if IS_WINDOWS:
        print_info(t("msg.win_checking_openssh"))
        code, output = _run_ps(
            "Get-WindowsCapability -Online "
            "| Where-Object Name -like 'OpenSSH.Server*' "
            "| Select-Object -ExpandProperty State"
        )
        if code != 0:
            return False
        if "Installed" in output:
            print_info(t("msg.win_openssh_installed"))
            return True
        print_info(t("msg.win_installing_openssh"))
        code, _ = _run_ps("Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0")
        if code != 0:
            print_error(t("msg.install_failed", package="OpenSSH Server"))
            return False
        print_success(t("msg.win_openssh_install_success"))
        return True

    # Linux
    cfg = _get_config(distro)
    package = cfg["package"]
    if _is_installed(package, distro):
        print_info(t("msg.already_installed", package=package))
        return True
    if not _install_package(package, distro):
        print_error(t("msg.install_failed", package=package))
        return False
    print_success(t("msg.install_success", package=package))
    return True


# Start or enable the sshd service.
#
# 启动或启用 sshd 服务。
#
# Args:
#     distro: Distribution identifier / 发行版标识符
#     action: "start" or "enable" / "start" 或 "enable"
#
# Returns:
#     True if successful / 成功返回 True
def _step_manage_ssh_service(distro: str, action: str) -> bool:
    if IS_WINDOWS:
        if action == "start":
            print_info(t("msg.win_starting_sshd"))
            code, _ = _run_ps("Start-Service sshd")
            if code != 0:
                print_error(t("msg.service_start_failed", service="sshd"))
                return False
            _, status = _run_ps("Get-Service sshd | Select-Object -ExpandProperty Status", check=False)
            print_success(t("msg.win_sshd_status", status=status))
        else:
            print_info(t("msg.win_enabling_sshd"))
            code, _ = _run_ps("Set-Service -Name sshd -StartupType Automatic")
            if code != 0:
                print_error(t("msg.service_enable_failed", service="sshd"))
                return False
            print_success(t("msg.win_sshd_auto_enabled"))
        return True

    # Linux
    cfg = _get_config(distro)
    service = cfg["service"]
    is_active_fn = _is_active if action == "start" else _is_enabled
    already_msg = "msg.service_already_running" if action == "start" else "msg.service_already_enabled"
    success_msg = "msg.service_started" if action == "start" else "msg.service_enabled"
    failed_msg = "msg.service_start_failed" if action == "start" else "msg.service_enable_failed"

    if is_active_fn(service):
        print_info(t(already_msg, service=service))
        return True
    code, _ = run_cmd(["sudo", "systemctl", action, service])
    if code != 0:
        print_error(t(failed_msg, service=service))
        return False
    print_success(t(success_msg, service=service))
    return True


# Set user password if not already set.

def _step_set_password() -> bool:
    if IS_WINDOWS:
        print_warning(t("msg.win_password_note"))
        user = getpass.getuser()
        print_info(t("msg.win_password_hint", user=user))
        return True

    # Linux
    user = getpass.getuser()
    if _has_password(user):
        print_info(t("msg.password_already_set", user=user))
        return True
    print_warning(t("msg.password_not_set", user=user))
    _set_password(user)
    return True


# Configure sshd — on Linux enable PasswordAuthentication, on Windows set default shell.

def _step_config_sshd() -> bool:
    if IS_WINDOWS:
        print_info(t("msg.win_config_sshd_shell"))
        ps_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        code, current = _run_ps(
            "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\OpenSSH' "
            "-Name DefaultShell -ErrorAction SilentlyContinue "
            "| Select-Object -ExpandProperty DefaultShell",
            check=False,
        )
        if current == ps_path:
            print_info(t("msg.win_shell_already_set"))
            return True
        code, _ = _run_ps(
            f'New-ItemProperty -Path "HKLM:\\SOFTWARE\\OpenSSH" '
            f'-Name DefaultShell -Value "{ps_path}" '
            f'-PropertyType String -Force'
        )
        if code != 0:
            print_error(t("msg.win_shell_set_failed"))
            return False
        print_success(t("msg.win_shell_set_success"))
        return True

    # Linux
    _configure_sshd()
    return True


# Open firewall for SSH access.

def _step_open_firewall() -> bool:
    if IS_WINDOWS:
        print_info(t("msg.win_checking_firewall"))
        code, exists = _run_ps(
            "Get-NetFirewallRule -Name 'sshd' -ErrorAction SilentlyContinue "
            "| Select-Object -ExpandProperty Enabled",
            check=False,
        )
        if "True" in exists:
            print_info(t("msg.win_firewall_exists"))
            return True
        code, _ = _run_ps(
            "New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' "
            "-Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22"
        )
        if code != 0:
            print_error(t("msg.win_firewall_failed"))
            return False
        print_success(t("msg.win_firewall_success"))
        return True

    # Linux
    _open_firewall_ssh_linux()
    return True


# Create python -> python3 symlink.

def _step_python_alias() -> bool:
    if IS_WINDOWS:
        print_info(t("msg.win_python_alias_skip"))
        return True

    # Linux
    _setup_python_alias_linux()
    return True


# Print SSH connection information.

def _step_connection_info() -> bool:
    user = getpass.getuser()
    hostname = socket.gethostname()

    # Get LAN IP address
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
    except Exception:
        ip_address = socket.gethostbyname(hostname)

    if IS_WINDOWS:
        os_version = f"Windows {platform_mod.version()}"
    else:
        os_version = f"Linux {platform_mod.release()}"

    print()
    console.print("=" * 55)
    console.print(f"  {t('msg.conn_info_header')}")
    console.print("=" * 55)
    console.print(f"  {t('msg.conn_info_os', version=os_version)}")
    console.print(f"  {t('msg.conn_info_user', user=user)}")
    console.print(f"  {t('msg.conn_info_host', host=hostname)}")
    console.print(f"  {t('msg.conn_info_ip', ip=ip_address)}")
    console.print(f"  {t('msg.conn_info_port', port='22')}")
    console.print("-" * 55)
    console.print(f"  {t('msg.conn_info_cmd', cmd=f'ssh {user}@{ip_address}')}")
    console.print("=" * 55)
    print()

    if IS_WINDOWS:
        print_info(t("msg.win_conn_info_notes"))
    else:
        print_info(t("msg.conn_info_notes"))

    return True


# ── Preview ─────────────────────────────────────────────────────

# Generate a preview of what the full setup would do.

def _generate_preview() -> str:
    lines = [t("msg.init_preview_header"), ""]
    # Use the same i18n keys as the submenu options for consistency
    # 与子菜单选项使用相同的国际化键以保持一致
    preview_steps = [
        "install-ssh", "start-ssh", "enable-ssh",
        "set-password", "config-sshd", "open-firewall",
        "python-alias", "connection-info",
    ]
    for i, step_id in enumerate(preview_steps, 1):
        opt = next(o for o in INIT_OPTIONS if o["id"] == step_id)
        lines.append(f"  {i}. {t(opt['name_key'])}")
    lines.append("")
    lines.append(t("msg.init_preview_files"))
    return "\n".join(lines)


# ── Tool class ──────────────────────────────────────────────────

class DeviceInitializer(Tool):
    name = "device-init"
    display_name = "Initialize Device"
    description = "Set up SSH access, password, config, firewall and python alias"
    distros = list(DISTRO_CONFIG.keys())
    platforms = ("linux", "windows")
    requires_network = True
    requires_sudo = True

    # Main entry point: present submenu and dispatch to selected step.

    def run(self) -> bool | None:
        distro = detect_distro()

        choice = prompt_selection(t("msg.init_select"), INIT_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        console.print()

        # Dispatch table for individual steps / 单个步骤的分发表
        dispatch = {
            "install-ssh": lambda: _step_install_ssh(distro),
            "start-ssh": lambda: _step_manage_ssh_service(distro, "start"),
            "enable-ssh": lambda: _step_manage_ssh_service(distro, "enable"),
            "set-password": _step_set_password,
            "config-sshd": _step_config_sshd,
            "open-firewall": _step_open_firewall,
            "python-alias": _step_python_alias,
            "connection-info": _step_connection_info,
        }

        if choice == "all":
            # install-ssh is required; remaining steps continue even if they fail
            # install-ssh 是必需的；剩余步骤即使失败也会继续
            if not _step_install_ssh(distro):
                return False
            _step_manage_ssh_service(distro, "start")
            _step_manage_ssh_service(distro, "enable")
            _step_set_password()
            _step_config_sshd()
            _step_open_firewall()
            _step_python_alias()
            _step_connection_info()
            return True
        elif choice == "preview":
            console.print(f"\n[bold cyan]{_generate_preview()}[/bold cyan]\n")
            return None
        elif choice in dispatch:
            return dispatch[choice]()
        else:
            print_error(t("ui.invalid_selection"))
            return False
