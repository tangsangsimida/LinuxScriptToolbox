import getpass
import subprocess
from pathlib import Path

from tools.base import Tool
from utils.cmd_utils import run_cmd, run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.sudo_utils import write_file, copy_file
from utils.ui import print_success, print_error, print_info, print_warning, confirm

DISTRO_CONFIG = {
    "arch": {"service": "sshd", "package": "openssh"},
    "debian": {"service": "ssh", "package": "openssh-server"},
    "fedora": {"service": "sshd", "package": "openssh-server"},
    "suse": {"service": "sshd", "package": "openssh"},
}

PYTHON_SYMLINK = Path("/usr/local/bin/python")
SSHD_CONFIG = Path("/etc/ssh/sshd_config")


def _has_password(user: str) -> bool:
    """Check if user has a password set by reading shadow file."""
    code, out = run_cmd(["sudo", "grep", f"^{user}:", "/etc/shadow"])
    if code != 0:
        return False
    fields = out.split(":")
    if len(fields) < 2:
        return False
    pw_hash = fields[1]
    return pw_hash not in ("!", "!!", "", "*")


def _set_password(user: str) -> None:
    """Prompt for and set user password."""
    try:
        pw1 = getpass.getpass(t("msg.enter_password"))
        pw2 = getpass.getpass(t("msg.confirm_password"))
    except (KeyboardInterrupt, EOFError):
        print()
        return
    if pw1 != pw2:
        print_warning(t("msg.password_mismatch"))
        return
    proc = subprocess.run(
        ["sudo", "chpasswd"],
        input=f"{user}:{pw1}",
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        print_error(t("msg.password_set_failed"))
        return
    print_success(t("msg.password_set_success", user=user))


def _configure_sshd() -> None:
    """Ensure PasswordAuthentication yes in sshd_config."""
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


def _open_firewall_ssh() -> None:
    """Allow SSH through the active firewall."""
    print_info(t("msg.step_firewall"))

    fw = None
    if run_cmd(["which", "ufw"])[0] == 0:
        fw = "ufw"
    elif run_cmd(["which", "firewall-cmd"])[0] == 0:
        fw = "firewalld"
    elif run_cmd(["which", "iptables"])[0] == 0:
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


class DeviceInitializer(Tool):
    name = "device-init"
    display_name = "Initialize Device"
    description = "Set up SSH access (install, password, config, firewall) and python alias"
    distros = list(DISTRO_CONFIG.keys())

    def _get_config(self, distro: str) -> dict:
        return DISTRO_CONFIG.get(distro, DISTRO_CONFIG["debian"])

    def _is_installed(self, package: str) -> bool:
        if run_cmd(["which", "pacman"])[0] == 0:
            code, _ = run_cmd(["pacman", "-Qi", package])
        elif run_cmd(["which", "rpm"])[0] == 0:
            code, _ = run_cmd(["rpm", "-q", package])
        else:
            code, _ = run_cmd(["dpkg", "-s", package])
        return code == 0

    def _install(self, package: str, distro: str) -> bool:
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

    def _is_active(self, service: str) -> bool:
        code, _ = run_cmd(["systemctl", "is-active", service])
        return code == 0

    def _is_enabled(self, service: str) -> bool:
        code, _ = run_cmd(["systemctl", "is-enabled", service])
        return code == 0

    def _setup_python_alias(self) -> None:
        """Create persistent 'python' symlink if python3 exists but python doesn't."""
        has_python3 = run_cmd(["which", "python3"])[0] == 0
        has_python = run_cmd(["which", "python"])[0] == 0

        if not has_python3:
            print_warning(t("msg.python3_not_found"))
            return

        if has_python:
            print_info(t("msg.python_already_exists"))
            return

        _, python3_path = run_cmd(["which", "python3"])
        run_cmd(["sudo", "ln", "-sf", python3_path, str(PYTHON_SYMLINK)])
        print_success(t("msg.python_alias_created", path=str(PYTHON_SYMLINK)))

    def run(self) -> bool | None:
        distro = detect_distro()
        cfg = self._get_config(distro)
        service = cfg["service"]
        package = cfg["package"]

        # Step 1: Install if needed
        if not self._is_installed(package):
            if not self._install(package, distro):
                print_error(t("msg.install_failed", package=package))
                return False
            print_success(t("msg.install_success", package=package))
        else:
            print_info(t("msg.already_installed", package=package))

        # Step 2: Start service
        if self._is_active(service):
            print_info(t("msg.service_already_running", service=service))
        else:
            code, out = run_cmd(["sudo", "systemctl", "start", service])
            if code != 0:
                print_error(t("msg.service_start_failed", service=service))
                return False
            print_success(t("msg.service_started", service=service))

        # Step 3: Enable on boot
        if self._is_enabled(service):
            print_info(t("msg.service_already_enabled", service=service))
        else:
            code, _ = run_cmd(["sudo", "systemctl", "enable", service])
            if code != 0:
                print_error(t("msg.service_enable_failed", service=service))
                return False
            print_success(t("msg.service_enabled", service=service))

        # Step 4: Set user password if not set
        print_info(t("msg.step_password"))
        user = getpass.getuser()
        if _has_password(user):
            print_info(t("msg.password_already_set", user=user))
        else:
            print_warning(t("msg.password_not_set", user=user))
            _set_password(user)

        # Step 5: Configure sshd for password auth
        print_info(t("msg.step_sshd_config"))
        _configure_sshd()

        # Step 6: Open firewall
        _open_firewall_ssh()

        # Step 7: Setup python alias
        self._setup_python_alias()

        return True
