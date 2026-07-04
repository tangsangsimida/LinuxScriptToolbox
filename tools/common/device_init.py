"""Device initialization tool — SSH access, password, firewall, python alias.

设备初始化工具 — SSH 访问、密码、防火墙、Python 别名。

Supports Linux (arch/debian/fedora/suse) and Windows.
Uses utils/platform_services for cross-platform service and package operations.

支持 Linux（arch/debian/fedora/suse）和 Windows。
使用 utils/platform_services 进行跨平台服务和包操作。
"""

import getpass
import socket
from pathlib import Path

from tools.base import Tool
from . import device_init_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_cmd, run_cmd_with_stdin
from utils.distro import detect_distro
from utils.i18n import t
from utils.platform import IS_WINDOWS, command_exists
from utils.platform_services import (
    package_install,
    package_is_installed,
    run_ps,
    service_enable,
    service_is_active,
    service_is_enabled,
    service_restart,
    service_start,
    os_version_string,
)
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
    {"id": "all", "name_key": "msg.init_all", "desc_key": "msg.init_all_desc"},
    {"id": "preview", "name_key": "msg.init_preview", "desc_key": "msg.init_preview_desc"},
    {"type": "separator", "text_key": "msg.sep_ssh_service"},
    {"id": "install-ssh", "name_key": "msg.init_install_ssh", "desc_key": "msg.init_install_ssh_desc"},
    {"id": "start-ssh", "name_key": "msg.init_start_ssh", "desc_key": "msg.init_start_ssh_desc"},
    {"id": "enable-ssh", "name_key": "msg.init_enable_ssh", "desc_key": "msg.init_enable_ssh_desc"},
    {"id": "config-sshd", "name_key": "msg.init_config_sshd", "desc_key": "msg.init_config_sshd_desc"},
    {"id": "open-firewall", "name_key": "msg.init_open_firewall", "desc_key": "msg.init_open_firewall_desc"},
    {"type": "separator", "text_key": "msg.sep_other"},
    {"id": "set-password", "name_key": "msg.init_set_password", "desc_key": "msg.init_set_password_desc"},
    {"id": "python-alias", "name_key": "msg.init_python_alias", "desc_key": "msg.init_python_alias_desc"},
    {"id": "connection-info", "name_key": "msg.init_connection_info", "desc_key": "msg.init_connection_info_desc"},
]


# ── Linux helpers (non-service, non-package) ────────────────────

def _get_config(distro: str) -> dict:
    return DISTRO_CONFIG.get(distro, DISTRO_CONFIG["debian"])


def _has_password(user: str) -> bool:
    code, out = run_cmd(["sudo", "grep", f"^{user}:", "/etc/shadow"])
    if code != 0:
        return False
    fields = out.split(":")
    if len(fields) < 2:
        return False
    pw_hash = fields[1]
    return pw_hash not in ("!", "!!", "", "*")


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
        service_restart("sshd")
        print_success(t("msg.password_auth_enabled"))
        print_success(t("msg.sshd_restarted"))
    else:
        print_info(t("msg.password_auth_already"))


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

def _step_install_ssh(distro: str) -> bool:
    """Install OpenSSH server if not already present."""
    if IS_WINDOWS:
        print_info(t("msg.win_checking_openssh"))
        code, output = run_ps(
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
        code, _ = run_ps("Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0")
        if code != 0:
            print_error(t("msg.install_failed", package="OpenSSH Server"))
            return False
        print_success(t("msg.win_openssh_install_success"))
        return True

    # Linux — use platform_services for package check/install
    cfg = _get_config(distro)
    package = cfg["package"]
    if package_is_installed(package, distro):
        print_info(t("msg.already_installed", package=package))
        return True
    print_info(t("msg.installing", package=package))
    if package_install(package, distro) != 0:
        print_error(t("msg.install_failed", package=package))
        return False
    print_success(t("msg.install_success", package=package))
    return True


def _step_manage_ssh_service(distro: str, action: str) -> bool:
    """Start or enable the sshd service using platform_services."""
    cfg = _get_config(distro)
    service = cfg["service"]

    if action == "start":
        if service_is_active(service):
            print_info(t("msg.service_already_running", service=service))
            return True
        print_info(t("msg.service_starting", service=service))
        code, _ = service_start(service)
        if code != 0:
            print_error(t("msg.service_start_failed", service=service))
            return False
        print_success(t("msg.service_started", service=service))
        return True
    else:  # enable
        if service_is_enabled(service):
            print_info(t("msg.service_already_enabled", service=service))
            return True
        print_info(t("msg.service_enabling", service=service))
        code, _ = service_enable(service)
        if code != 0:
            print_error(t("msg.service_enable_failed", service=service))
            return False
        print_success(t("msg.service_enabled", service=service))
        return True


def _step_set_password() -> bool:
    """Set user password if not already set."""
    if IS_WINDOWS:
        print_warning(t("msg.win_password_note"))
        user = getpass.getuser()
        print_info(t("msg.win_password_hint", user=user))
        return True
    user = getpass.getuser()
    if _has_password(user):
        print_info(t("msg.password_already_set", user=user))
        return True
    print_warning(t("msg.password_not_set", user=user))
    _set_password(user)
    return True


def _step_config_sshd() -> bool:
    """Configure sshd — Linux: PasswordAuthentication, Windows: default shell."""
    if IS_WINDOWS:
        print_info(t("msg.win_config_sshd_shell"))
        ps_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        _, current = run_ps(
            "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\OpenSSH' "
            "-Name DefaultShell -ErrorAction SilentlyContinue "
            "| Select-Object -ExpandProperty DefaultShell"
        )
        if current == ps_path:
            print_info(t("msg.win_shell_already_set"))
            return True
        code, _ = run_ps(
            f'New-ItemProperty -Path "HKLM:\\SOFTWARE\\OpenSSH" '
            f'-Name DefaultShell -Value "{ps_path}" '
            f'-PropertyType String -Force'
        )
        if code != 0:
            print_error(t("msg.win_shell_set_failed"))
            return False
        print_success(t("msg.win_shell_set_success"))
        return True
    _configure_sshd()
    return True


def _step_open_firewall() -> bool:
    """Open firewall for SSH access."""
    if IS_WINDOWS:
        print_info(t("msg.win_checking_firewall"))
        _, exists = run_ps(
            "Get-NetFirewallRule -Name 'sshd' -ErrorAction SilentlyContinue "
            "| Select-Object -ExpandProperty Enabled"
        )
        if "True" in exists:
            print_info(t("msg.win_firewall_exists"))
            return True
        code, _ = run_ps(
            "New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' "
            "-Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22"
        )
        if code != 0:
            print_error(t("msg.win_firewall_failed"))
            return False
        print_success(t("msg.win_firewall_success"))
        return True
    _open_firewall_ssh_linux()
    return True


def _step_python_alias() -> bool:
    """Create python -> python3 symlink (Linux only)."""
    if IS_WINDOWS:
        print_info(t("msg.win_python_alias_skip"))
        return True
    _setup_python_alias_linux()
    return True


def _step_connection_info() -> bool:
    """Print SSH connection information."""
    user = getpass.getuser()
    hostname = socket.gethostname()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
    except Exception:
        ip_address = socket.gethostbyname(hostname)

    print()
    console.print("=" * 55)
    console.print(f"  {t('msg.conn_info_header')}")
    console.print("=" * 55)
    console.print(f"  {t('msg.conn_info_os', version=os_version_string())}")
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

def _generate_preview() -> str:
    lines = [t("msg.init_preview_header"), ""]
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
    group = "system"
    requires_network = True
    requires_sudo = True

    def run(self) -> bool | None:
        distro = detect_distro()
        choice = prompt_selection(t("msg.init_select"), INIT_OPTIONS)
        if choice is None or choice == BACK_ACTION:
            return None
        console.print()
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
        print_error(t("ui.invalid_selection"))
        return False
