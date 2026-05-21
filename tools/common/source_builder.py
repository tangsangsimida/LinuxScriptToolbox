import subprocess
import sys
from pathlib import Path

from tools.base import Tool
from utils.i18n import t

QUICKSHELL_REPO = "https://git.outfoxxed.me/quickshell/quickshell.git"
QUICKSHELL_DIR = Path("/tmp/quickshell-build")
INSTALL_DIR = Path.home() / ".local" / "bin"


def _run(cmd: list[str], **kwargs) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    return result.returncode, result.stdout.strip()


def _run_verbose(cmd: list[str], **kwargs) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs)
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()
    return proc.returncode


def _package_installed(pkg: str) -> bool:
    code, _ = _run(["dpkg", "-s", pkg])
    return code == 0


def _get_distro() -> str:
    os_release = Path("/etc/os-release")
    if os_release.exists():
        data = os_release.read_text()
        if "ID=arch" in data or "ID_LIKE=arch" in data:
            return "arch"
    return "debian"


BUILD_DEPS = {
    "debian": [
        "cmake", "ninja-build", "g++", "pkg-config",
        "libjemalloc-dev", "libunwind-dev", "libdwarf-dev",
        "libpam0g-dev", "libpolkit-gobject-1-dev",
        "libvulkan-dev", "spirv-tools",
        "libcli11-dev", "libpipewire-0.3-dev",
        "libwayland-dev", "libxkbcommon-dev",
        "libegl1-mesa-dev", "libgl-dev", "libdrm-dev",
        "qt6-base-dev", "qt6-declarative-dev", "qt6-shadertools-dev",
        "qt6-wayland-dev", "qt6-wayland-private-dev",
        "qml6-module-qtquick", "qml6-module-qtquick-window",
        "qml6-module-qtquick-layouts", "qml6-module-qtquick-templates",
    ],
    "arch": [
        "cmake", "ninja", "gcc", "pkgconf",
        "jemalloc", "libunwind", "libdwarf",
        "pam", "polkit", "vulkan-headers",
        "spirv-tools", "cli11", "pipewire",
        "wayland", "libxkbcommon", "qt6-base", "qt6-declarative",
    ],
}


class SourceBuilder(Tool):
    name = "source-builder"
    display_name = "Build from Source"
    description = "Compile and install software from source (quickshell, etc.)"
    distros = ["arch", "debian"]

    def _install_build_deps(self, distro: str) -> bool:
        deps = BUILD_DEPS.get(distro, [])
        missing = []
        for dep in deps:
            if distro == "arch":
                code, _ = _run(["pacman", "-Qi", dep])
            else:
                code = 0 if _package_installed(dep) else 1
            if code != 0:
                missing.append(dep)

        if not missing:
            print(t("msg.build_deps_installed"))
            return True

        print(t("msg.installing_build_deps", count=len(missing)))
        if distro == "arch":
            ok = _run_verbose(["sudo", "pacman", "-S", "--noconfirm"] + missing)
        else:
            _run_verbose(["sudo", "apt-get", "update", "-qq"])
            ok = _run_verbose(["sudo", "apt-get", "install", "-y"] + missing)
        return ok == 0

    def _build_quickshell(self, distro: str) -> bool:
        # Install build dependencies
        if not self._install_build_deps(distro):
            print(t("msg.build_deps_failed"))
            return False

        # Clone source
        import shutil
        if QUICKSHELL_DIR.exists():
            shutil.rmtree(QUICKSHELL_DIR)
        QUICKSHELL_DIR.mkdir(parents=True)

        print(t("msg.cloning", repo="quickshell"))
        code = _run_verbose(["git", "clone", "--depth", "1", QUICKSHELL_REPO, str(QUICKSHELL_DIR)])
        if code != 0:
            print(t("msg.clone_failed", repo="quickshell"))
            return False

        # Configure
        build_dir = QUICKSHELL_DIR / "build"
        build_dir.mkdir()
        print(t("msg.configuring"))

        cmake_args = [
            "cmake", "-GNinja", "-B", str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCRASH_HANDLER=OFF",
            "-DUSE_JEMALLOC=OFF",
            "-DSERVICE_POLKIT=OFF",
        ]

        # Use Qt from custom install if available
        qt_dir = Path.home() / "software" / "QT" / "6.10.2" / "gcc_64"
        if qt_dir.exists():
            cmake_args.append(f"-DCMAKE_PREFIX_PATH={qt_dir}")

        code = _run_verbose(cmake_args, cwd=str(QUICKSHELL_DIR))
        if code != 0:
            print(t("msg.configure_failed"))
            return False

        # Build
        print(t("msg.compiling"))
        code = _run_verbose(["cmake", "--build", str(build_dir)])
        if code != 0:
            print(t("msg.build_failed"))
            return False

        # Install
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        binary = build_dir / "src" / "quickshell"
        if binary.exists():
            import shutil
            dst = INSTALL_DIR / "quickshell"
            shutil.copy2(str(binary), str(dst))
            dst.chmod(0o755)
            # Create symlink
            qs_link = INSTALL_DIR / "qs"
            if qs_link.exists() or qs_link.is_symlink():
                qs_link.unlink()
            qs_link.symlink_to(dst)
            print(t("msg.quickshell_installed", path=str(dst)))
            return True
        else:
            print(t("msg.binary_not_found"))
            return False

    def run(self) -> bool:
        distro = _get_distro()

        print(t("msg.select_build"))
        print("-" * 40)
        print(f"  [1] {t('msg.build_quickshell')}")
        print("-" * 40)

        choice = input(t("ui.select")).strip()

        if choice == "1":
            return self._build_quickshell(distro)
        else:
            print(t("ui.invalid_selection"))
            return False
