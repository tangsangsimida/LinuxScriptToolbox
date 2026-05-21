import subprocess
from pathlib import Path

from tools.base import Tool
from utils.i18n import t

DISTRO_CONFIG = {
    "arch": {"service": "sshd", "package": "openssh"},
    "debian": {"service": "ssh", "package": "openssh-server"},
}

PYTHON_SYMLINK = Path("/usr/local/bin/python")


def _run_cmd(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


class DeviceInitializer(Tool):
    name = "device-init"
    display_name = "Initialize Device (SSH)"
    description = "Enable and start SSH service, set to auto-start on boot"
    distros = list(DISTRO_CONFIG.keys())

    def _get_config(self, distro: str) -> dict:
        return DISTRO_CONFIG.get(distro, DISTRO_CONFIG["debian"])

    def _is_installed(self, package: str) -> bool:
        return _run_cmd(["pacman", "-Qi", package])[0] == 0 if _run_cmd(["which", "pacman"])[0] == 0 else _run_cmd(["dpkg", "-s", package])[0] == 0

    def _install(self, package: str, distro: str) -> bool:
        print(t("msg.installing", package=package))
        if distro == "arch":
            code, _ = _run_cmd(["sudo", "pacman", "-S", "--noconfirm", package])
        else:
            code, _ = _run_cmd(["sudo", "apt-get", "install", "-y", package])
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

        # Install if needed
        if not self._is_installed(package):
            if not self._install(package, distro):
                print(t("msg.install_failed", package=package))
                return False
            print(t("msg.install_success", package=package))
        else:
            print(t("msg.already_installed", package=package))

        # Start service
        if self._is_active(service):
            print(t("msg.service_already_running", service=service))
        else:
            code, out = _run_cmd(["sudo", "systemctl", "start", service])
            if code != 0:
                print(t("msg.service_start_failed", service=service))
                return False
            print(t("msg.service_started", service=service))

        # Enable on boot
        if self._is_enabled(service):
            print(t("msg.service_already_enabled", service=service))
        else:
            code, _ = _run_cmd(["sudo", "systemctl", "enable", service])
            if code != 0:
                print(t("msg.service_enable_failed", service=service))
                return False
            print(t("msg.service_enabled", service=service))

        # Setup python alias
        self._setup_python_alias()

        return True
