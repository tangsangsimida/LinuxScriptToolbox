import getpass
import subprocess
import sys
from pathlib import Path

from tools.base import Tool
from utils.i18n import t
from utils.sudo_utils import write_file, copy_file

DISTRO_CONFIG = {
    "arch": {"service": "sshd", "package": "openssh"},
    "debian": {"service": "ssh", "package": "openssh-server"},
}

PYTHON_SYMLINK = Path("/usr/local/bin/python")
SSHD_CONFIG = Path("/etc/ssh/sshd_config")


def _run_cmd(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def _run_verbose(cmd: list[str]) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()
    return proc.returncode


def _has_password(user: str) -> bool:
    """Check if user has a password set by reading shadow file."""
    code, out = _run_cmd(["sudo", "grep", f"^{user}:", "/etc/shadow"])
    if code != 0:
        return False
    # Field 2 is the password hash; '!' or '!!' or empty means no password
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
        print(t("msg.password_mismatch"))
        return
    code, _ = _run_cmd(["sudo", "chpasswd"])
    # chpasswd reads from stdin
    proc = subprocess.run(
        ["sudo", "chpasswd"],
        input=f"{user}:{pw1}",
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(t("msg.password_set_failed"))
        return
    print(t("msg.password_set_success", user=user))


def _configure_sshd() -> None:
    """Ensure PasswordAuthentication yes in sshd_config."""
    print(t("msg.checking_sshd_config"))

    code, content = _run_cmd(["sudo", "cat", str(SSHD_CONFIG)])
    if code != 0:
        return

    if "PasswordAuthentication no" in content:
        backup = str(SSHD_CONFIG) + ".bak"
        copy_file(str(SSHD_CONFIG), backup)
        print(t("msg.sshd_config_backup", path=backup))

        new_content = content.replace("PasswordAuthentication no", "PasswordAuthentication yes")
        write_file(str(SSHD_CONFIG), new_content)

        _run_cmd(["sudo", "systemctl", "restart", "sshd"])
        print(t("msg.password_auth_enabled"))
        print(t("msg.sshd_restarted"))
    else:
        print(t("msg.password_auth_already"))


def _open_firewall_ssh() -> None:
    """Allow SSH through the active firewall."""
    print(t("msg.step_firewall"))

    # Detect firewall backend
    fw = None
    if _run_cmd(["which", "ufw"])[0] == 0:
        fw = "ufw"
    elif _run_cmd(["which", "firewall-cmd"])[0] == 0:
        fw = "firewalld"
    elif _run_cmd(["which", "iptables"])[0] == 0:
        fw = "iptables"

    if fw is None:
        print(t("msg.firewall_no_active"))
        return

    print(t("msg.firewall_detected", fw=fw))
    confirm = input(t("msg.firewall_allow_ssh") + " (y/N) ").strip().lower()
    if confirm != "y":
        return

    if fw == "ufw":
        _run_cmd(["sudo", "ufw", "allow", "ssh"])
    elif fw == "firewalld":
        _run_cmd(["sudo", "firewall-cmd", "--permanent", "--add-service=ssh"])
        _run_cmd(["sudo", "firewall-cmd", "--reload"])
    elif fw == "iptables":
        _run_cmd(["sudo", "iptables", "-I", "INPUT", "-p", "tcp", "--dport", "22", "-j", "ACCEPT"])

    print(t("msg.firewall_rule_added"))


class DeviceInitializer(Tool):
    name = "device-init"
    display_name = "Initialize Device"
    description = "Set up SSH access (install, password, config, firewall) and python alias"
    distros = list(DISTRO_CONFIG.keys())

    def _get_config(self, distro: str) -> dict:
        return DISTRO_CONFIG.get(distro, DISTRO_CONFIG["debian"])

    def _is_installed(self, package: str) -> bool:
        return _run_cmd(["pacman", "-Qi", package])[0] == 0 if _run_cmd(["which", "pacman"])[0] == 0 else _run_cmd(["dpkg", "-s", package])[0] == 0

    def _install(self, package: str, distro: str) -> bool:
        print(t("msg.installing", package=package))
        if distro == "arch":
            code = _run_verbose(["sudo", "pacman", "-S", "--noconfirm", package])
        else:
            code = _run_verbose(["sudo", "apt-get", "install", "-y", package])
        return code == 0

    def _is_active(self, service: str) -> bool:
        code, _ = _run_cmd(["systemctl", "is-active", service])
        return code == 0

    def _is_enabled(self, service: str) -> bool:
        code, _ = _run_cmd(["systemctl", "is-enabled", service])
        return code == 0

    def _setup_python_alias(self) -> None:
        """Create persistent 'python' symlink if python3 exists but python doesn't."""
        has_python3 = _run_cmd(["which", "python3"])[0] == 0
        has_python = _run_cmd(["which", "python"])[0] == 0

        if not has_python3:
            print(t("msg.python3_not_found"))
            return

        if has_python:
            print(t("msg.python_already_exists"))
            return

        python3_path = _run_cmd(["which", "python3"])[1]
        _run_cmd(["sudo", "ln", "-sf", python3_path, str(PYTHON_SYMLINK)])
        print(t("msg.python_alias_created", path=str(PYTHON_SYMLINK)))

    def run(self) -> bool:
        from utils.distro import detect_distro
        distro = detect_distro()
        cfg = self._get_config(distro)
        service = cfg["service"]
        package = cfg["package"]

        # Step 1: Install if needed
        if not self._is_installed(package):
            if not self._install(package, distro):
                print(t("msg.install_failed", package=package))
                return False
            print(t("msg.install_success", package=package))
        else:
            print(t("msg.already_installed", package=package))

        # Step 2: Start service
        if self._is_active(service):
            print(t("msg.service_already_running", service=service))
        else:
            code, out = _run_cmd(["sudo", "systemctl", "start", service])
            if code != 0:
                print(t("msg.service_start_failed", service=service))
                return False
            print(t("msg.service_started", service=service))

        # Step 3: Enable on boot
        if self._is_enabled(service):
            print(t("msg.service_already_enabled", service=service))
        else:
            code, _ = _run_cmd(["sudo", "systemctl", "enable", service])
            if code != 0:
                print(t("msg.service_enable_failed", service=service))
                return False
            print(t("msg.service_enabled", service=service))

        # Step 4: Set user password if not set
        print(t("msg.step_password"))
        user = getpass.getuser()
        if _has_password(user):
            print(t("msg.password_already_set", user=user))
        else:
            print(t("msg.password_not_set", user=user))
            _set_password(user)

        # Step 5: Configure sshd for password auth
        print(t("msg.step_sshd_config"))
        _configure_sshd()

        # Step 6: Open firewall
        _open_firewall_ssh()

        # Step 7: Setup python alias
        self._setup_python_alias()

        return True
