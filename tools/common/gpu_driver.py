import subprocess
import sys
from pathlib import Path

from tools.base import Tool
from utils.i18n import t

GPU_PACKAGES = {
    "arch": {
        "intel": ["xf86-video-intel", "vulkan-intel", "intel-media-driver"],
        "amd": ["xf86-video-amdgpu", "vulkan-radeon", "lib32-vulkan-radeon"],
        "nvidia": ["nvidia", "nvidia-utils", "nvidia-settings"],
    },
    "debian": {
        "intel": ["xserver-xorg-video-intel", "intel-media-va-driver", "vulkan-tools"],
        "amd": ["xserver-xorg-video-amdgpu", "mesa-vulkan-drivers", "vulkan-tools"],
        "nvidia": ["nvidia-driver", "nvidia-settings"],
    },
}


def _run(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def _run_verbose(cmd: list[str]) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()
    return proc.returncode


def _detect_gpu() -> list[str]:
    code, out = _run(["lspci"])
    if code != 0:
        return []
    gpus = []
    for line in out.splitlines():
        lower = line.lower()
        if any(k in lower for k in ["vga", "3d controller", "display controller"]):
            if "intel" in lower:
                gpus.append("intel")
            elif "amd" in lower or "radeon" in lower:
                gpus.append("amd")
            elif "nvidia" in lower:
                gpus.append("nvidia")
    return list(set(gpus))


def _get_distro() -> str:
    os_release = Path("/etc/os-release")
    if os_release.exists():
        data = os_release.read_text()
        if "ID=arch" in data or "ID_LIKE=arch" in data:
            return "arch"
    return "debian"


def _package_installed(pkg: str, distro: str) -> bool:
    if distro == "arch":
        code, _ = _run(["pacman", "-Qi", pkg])
    else:
        code, _ = _run(["dpkg", "-s", pkg])
    return code == 0


def _install_package(pkg: str, distro: str) -> bool:
    if _package_installed(pkg, distro):
        print(t("msg.already_installed", package=pkg))
        return True
    print(t("msg.installing", package=pkg))
    if distro == "arch":
        ok = _run_verbose(["sudo", "pacman", "-S", "--noconfirm", pkg])
    else:
        ok = _run_verbose(["sudo", "apt-get", "install", "-y", pkg])
    if ok != 0:
        print(t("msg.install_failed", package=pkg))
        return False
    print(t("msg.install_success", package=pkg))
    return True


class GPUDriverInstaller(Tool):
    name = "gpu-driver"
    display_name = "GPU Driver Setup"
    description = "Auto-detect GPU and install appropriate drivers"
    distros = ["arch", "debian"]

    def run(self) -> bool:
        gpus = _detect_gpu()
        if not gpus:
            print(t("msg.no_gpu_detected"))
            return False

        distro = _get_distro()
        print(t("msg.gpu_detected", gpu=", ".join(gpus)))

        if distro != "arch":
            print(t("msg.apt_update"))
            _run_verbose(["sudo", "apt-get", "update", "-qq"])

        success = True
        for gpu in gpus:
            pkgs = GPU_PACKAGES.get(distro, {}).get(gpu, [])
            if not pkgs:
                print(t("msg.no_driver_packages", gpu=gpu))
                continue
            print(t("msg.installing_gpu_driver", gpu=gpu))
            for pkg in pkgs:
                if not _install_package(pkg, distro):
                    success = False

        return success
