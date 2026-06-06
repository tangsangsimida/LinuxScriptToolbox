import os
import stat
import subprocess
from pathlib import Path

from tools.base import Tool
from utils.cmd_utils import run_cmd, run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.ui import print_success, print_error, print_info, print_warning, ask, confirm, console, prompt_selection, BACK_ACTION

FIX_OPTIONS = [
    {
        "id": "stm32cubemx-wayland",
        "name_key": "msg.qfix_stm32cubemx",
        "desc_key": "msg.qfix_stm32cubemx_desc",
    },
    {
        "id": "git-proxy",
        "name_key": "msg.qfix_git_proxy",
        "desc_key": "msg.qfix_git_proxy_desc",
    },
    {
        "id": "npm-permissions",
        "name_key": "msg.qfix_npm_permissions",
        "desc_key": "msg.qfix_npm_permissions_desc",
    },
    {
        "id": "docker-group",
        "name_key": "msg.qfix_docker_group",
        "desc_key": "msg.qfix_docker_group_desc",
    },
]

STM32_SEARCH_PATHS = [
    Path.home() / "software" / "stm32cubemx",
    Path("/opt/stm32cubemx"),
    Path("/usr/local/stm32cubemx"),
    Path.home() / "STM32CubeMX",
    Path.home() / "software" / "STM32CubeMX",
]

WRAPPER_TEMPLATE = """\
#!/bin/bash
# Auto-generated wrapper for STM32CubeMX on Wayland
# Fixes blank popup/dialog windows by forcing X11 backend

export GDK_BACKEND=x11
export SWT_GTK3=0
export _JAVA_AWT_WM_NONREPARENTING=1

exec java \\
  -Dsun.java2d.opengl=false \\
  -Dsun.java2d.xrender=false \\
  -Dawt.useSystemAAFontSettings=on \\
  -Dswing.aatext=true \\
  -Dswt.enable.autoScale=false \\
  -Dswt.autoScale=false \\
  -jar "{cubemx_path}" "$@"
"""

DESKTOP_TEMPLATE = """\
[Desktop Entry]
Name=STM32CubeMX (Wayland Fix)
Comment=STM32CubeMX with Wayland compatibility fix
Exec={wrapper_path}
Icon=stm32cubemx
Terminal=false
Type=Application
Categories=Development;Electronics;
"""


def _find_stm32cubemx() -> Path | None:
    for base in STM32_SEARCH_PATHS:
        if not base.is_dir():
            continue
        # Check for jar file
        jar = base / "STM32CubeMX"
        if jar.is_file():
            return jar
        # Check for alternative names
        for name in ["STM32CubeMX.exe", "stm32cubemx.jar"]:
            alt = base / name
            if alt.is_file():
                return alt
        # Search recursively (shallow)
        for f in base.glob("*STM32CubeMX*"):
            if f.is_file() and os.access(f, os.X_OK):
                return f
    return None


def _create_wrapper(cubemx_path: Path) -> Path | None:
    wrapper_dir = Path.home() / ".local" / "bin"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    content = WRAPPER_TEMPLATE.format(cubemx_path=cubemx_path)

    # Create as "STM32CubeMX" so it shadows the original in PATH
    wrapper_path = wrapper_dir / "STM32CubeMX"
    try:
        wrapper_path.write_text(content)
        wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError as e:
        print_error(t("msg.qfix_wrapper_failed", error=str(e)))
        return None

    # Also create lowercase variant (some distros install as stm32cubemx)
    lower_path = wrapper_dir / "stm32cubemx"
    try:
        if lower_path.exists() or lower_path.is_symlink():
            lower_path.unlink()
        lower_path.symlink_to(wrapper_path)
    except OSError:
        pass

    # Also create the -fixed.sh variant
    fixed_path = wrapper_dir / "STM32CubeMX-fixed.sh"
    try:
        if fixed_path.exists() or fixed_path.is_symlink():
            fixed_path.unlink()
        fixed_path.symlink_to(wrapper_path)
    except OSError:
        pass

    return wrapper_path


def _create_desktop_file(wrapper_path: Path) -> bool:
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "stm32cubemx.desktop"
    content = DESKTOP_TEMPLATE.format(wrapper_path=wrapper_path)
    try:
        desktop_file.write_text(content)
        desktop_file.chmod(desktop_file.stat().st_mode | stat.S_IXUSR)
        return True
    except OSError as e:
        print_error(t("msg.qfix_desktop_failed", error=str(e)))
        return False


class QuickFixes(Tool):
    name = "quick-fixes"
    display_name = "Quick Fixes"
    description = "One-click fixes for common Linux software issues"
    distros = ["arch", "debian", "fedora", "suse", "unknown"]

    def _fix_stm32cubemx_wayland(self) -> bool:
        # Step 1: Detect installation
        print_info(t("msg.qfix_detecting_path"))
        cubemx_path = _find_stm32cubemx()

        if cubemx_path is None:
            print_error(t("msg.qfix_not_found"))
            custom = ask(t("msg.qfix_enter_path")).strip()
            if not custom:
                return False
            cubemx_path = Path(custom).expanduser()
            if not cubemx_path.is_file():
                print_error(t("msg.qfix_path_invalid", path=str(cubemx_path)))
                return False

        print_success(t("msg.qfix_found", path=str(cubemx_path)))

        # Step 2: Create wrapper script
        print_info(t("msg.qfix_creating_wrapper"))
        wrapper_path = _create_wrapper(cubemx_path)
        if wrapper_path is None:
            return False
        print_success(t("msg.qfix_wrapper_created", path=str(wrapper_path)))

        # Step 3: Create .desktop file
        print_info(t("msg.qfix_creating_desktop"))
        if not _create_desktop_file(wrapper_path):
            return False
        desktop_path = Path.home() / ".local" / "share" / "applications" / "stm32cubemx.desktop"
        print_success(t("msg.qfix_desktop_created", path=str(desktop_path)))

        # Step 4: Summary
        console.print()
        print_success(t("msg.qfix_success"))
        print_info(t("msg.qfix_usage_hint", wrapper=str(wrapper_path)))
        return True

    def _fix_git_proxy(self) -> bool:
        """Configure Git proxy settings."""
        print_info(t("msg.qfix_git_proxy_configuring"))

        # Check current proxy settings
        code, current_http = run_cmd(["git", "config", "--global", "http.proxy"])
        code2, current_https = run_cmd(["git", "config", "--global", "https.proxy"])

        if current_http or current_https:
            print_info(t("msg.qfix_git_proxy_current", http=current_http or "none", https=current_https or "none"))
            if not confirm(t("msg.qfix_git_proxy_overwrite")):
                return False

        # Ask for proxy URL
        proxy_url = ask(t("msg.qfix_git_proxy_enter")).strip()
        if not proxy_url:
            print_warning(t("msg.qfix_git_proxy_empty"))
            return False

        # Validate proxy URL format
        if not proxy_url.startswith(("http://", "https://", "socks5://")):
            proxy_url = "http://" + proxy_url

        # Set proxy
        run_cmd(["git", "config", "--global", "http.proxy", proxy_url])
        run_cmd(["git", "config", "--global", "https.proxy", proxy_url])

        print_success(t("msg.qfix_git_proxy_set", proxy=proxy_url))
        return True

    def _fix_npm_permissions(self) -> bool:
        """Fix npm global directory permissions."""
        print_info(t("msg.qfix_npm_configuring"))

        # Check if npm is installed
        if run_cmd(["which", "npm"])[0] != 0:
            print_error(t("msg.qfix_npm_not_found"))
            return False

        # Get npm global prefix
        code, npm_prefix = run_cmd(["npm", "config", "get", "prefix"])
        if code != 0:
            print_error(t("msg.qfix_npm_prefix_failed"))
            return False

        # Check if it's already user-owned
        npm_dir = Path(npm_prefix)
        if npm_dir.exists() and os.access(npm_dir, os.W_OK):
            print_info(t("msg.qfix_npm_already_ok"))
            return True

        # Create user-owned npm directory
        user_npm_dir = Path.home() / ".npm-global"
        print_info(t("msg.qfix_npm_creating", dir=str(user_npm_dir)))

        try:
            user_npm_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print_error(t("msg.qfix_npm_create_failed", error=str(e)))
            return False

        # Set npm prefix
        run_cmd(["npm", "config", "set", "prefix", str(user_npm_dir)])

        # Update PATH in shell profile
        shell_profile = Path.home() / ".bashrc"
        if not shell_profile.exists():
            shell_profile = Path.home() / ".profile"

        path_export = f'export PATH="{user_npm_dir}/bin:$PATH"'
        if shell_profile.exists():
            content = shell_profile.read_text()
            if path_export not in content:
                print_info(t("msg.qfix_npm_updating_profile", profile=str(shell_profile)))
                with open(shell_profile, "a") as f:
                    f.write(f"\n# npm global directory\n{path_export}\n")

        print_success(t("msg.qfix_npm_success", dir=str(user_npm_dir)))
        print_info(t("msg.qfix_npm_reload_hint"))
        return True

    def _fix_docker_group(self) -> bool:
        """Add current user to docker group."""
        print_info(t("msg.qfix_docker_configuring"))

        # Check if docker is installed
        if run_cmd(["which", "docker"])[0] != 0:
            print_error(t("msg.qfix_docker_not_found"))
            return False

        # Get current user
        import getpass
        user = getpass.getuser()

        # Check if user is already in docker group
        code, groups = run_cmd(["groups", user])
        if "docker" in groups:
            print_info(t("msg.qfix_docker_already_in_group", user=user))
            return True

        # Check if docker group exists
        code, _ = run_cmd(["getent", "group", "docker"])
        if code != 0:
            print_info(t("msg.qfix_docker_creating_group"))
            run_cmd(["sudo", "groupadd", "docker"])

        # Add user to docker group
        print_info(t("msg.qfix_docker_adding_user", user=user))
        code = run_verbose(["sudo", "usermod", "-aG", "docker", user])
        if code != 0:
            print_error(t("msg.qfix_docker_add_failed"))
            return False

        print_success(t("msg.qfix_docker_success", user=user))
        print_warning(t("msg.qfix_docker_logout_hint"))
        return True

    def run(self) -> bool | None:
        choice = prompt_selection(t("msg.qfix_select"), FIX_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        selected = next((opt for opt in FIX_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        console.print()

        if selected["id"] == "stm32cubemx-wayland":
            return self._fix_stm32cubemx_wayland()
        elif selected["id"] == "git-proxy":
            return self._fix_git_proxy()
        elif selected["id"] == "npm-permissions":
            return self._fix_npm_permissions()
        elif selected["id"] == "docker-group":
            return self._fix_docker_group()

        print_error(t("msg.qfix_not_implemented"))
        return False
