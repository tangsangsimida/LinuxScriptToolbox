"""AI CLI Setup — one-click install of AI coding assistant CLI tools."""

from tools.base import Tool
from utils.cmd_utils import run_cmd, run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.ui import print_success, print_error, print_info, console, prompt_selection, BACK_ACTION

AI_CLI_OPTIONS = [
    {
        "id": "claude-code",
        "name_key": "msg.ai_cli_claude",
        "desc_key": "msg.ai_cli_claude_desc",
        "package": "@anthropic-ai/claude-code",
    },
    {
        "id": "codex",
        "name_key": "msg.ai_cli_codex",
        "desc_key": "msg.ai_cli_codex_desc",
        "package": "@openai/codex",
    },
    {
        "id": "gemini",
        "name_key": "msg.ai_cli_gemini",
        "desc_key": "msg.ai_cli_gemini_desc",
        "package": "@google/gemini-cli",
    },
    {
        "id": "opencode",
        "name_key": "msg.ai_cli_opencode",
        "desc_key": "msg.ai_cli_opencode_desc",
        "package": "opencode-ai",
    },
    {
        "id": "all",
        "name_key": "msg.ai_cli_all",
        "desc_key": "msg.ai_cli_all_desc",
    },
]

DISTRO_NODEJS_PKGS = {
    "arch": ["nodejs", "npm"],
    "debian": ["nodejs", "npm"],
    "fedora": ["nodejs", "npm"],
    "suse": ["nodejs", "npm"],
}


def _has_nodejs() -> bool:
    """Check if Node.js is installed."""
    return run_cmd(["which", "node"])[0] == 0


def _has_npm() -> bool:
    """Check if npm is installed."""
    return run_cmd(["which", "npm"])[0] == 0


def _get_node_version() -> str | None:
    """Get installed Node.js version string."""
    code, out = run_cmd(["node", "--version"])
    if code == 0:
        return out
    return None


def _install_nodejs(distro: str) -> bool:
    """Install Node.js and npm via the distro package manager."""
    pkgs = DISTRO_NODEJS_PKGS.get(distro)
    if pkgs is None:
        print_error(t("msg.ai_cli_nodejs_unknown"))
        return False

    print_info(t("msg.ai_cli_nodejs_installing"))

    if distro == "arch":
        code = run_verbose(["sudo", "pacman", "-S", "--noconfirm"] + pkgs)
    elif distro in ("debian",):
        if run_verbose(["sudo", "apt-get", "update", "-qq"]) != 0:
            print_error(t("msg.ai_cli_nodejs_install_failed"))
            return False
        code = run_verbose(["sudo", "apt-get", "install", "-y"] + pkgs)
    elif distro == "fedora":
        code = run_verbose(["sudo", "dnf", "install", "-y"] + pkgs)
    elif distro == "suse":
        code = run_verbose(["sudo", "zypper", "install", "-y"] + pkgs)
    else:
        return False

    if code != 0:
        print_error(t("msg.ai_cli_nodejs_install_failed"))
        return False

    print_success(t("msg.ai_cli_nodejs_installed"))
    return True


def _is_npm_package_installed(package: str) -> bool:
    """Check if an npm package is globally installed."""
    code, out = run_cmd(["npm", "list", "-g", package])
    return code == 0 and package in out


def _install_npm_package(package: str, display_name: str) -> bool:
    """Install an npm package globally."""
    if _is_npm_package_installed(package):
        print_info(t("msg.ai_cli_already_installed", name=display_name))
        return True

    print_info(t("msg.ai_cli_installing", package=package))
    code = run_verbose(["npm", "install", "-g", package])
    if code != 0:
        print_error(t("msg.ai_cli_install_failed", name=display_name))
        return False

    print_success(t("msg.ai_cli_install_success", name=display_name))
    return True


def _update_npm_package(package: str, display_name: str) -> bool:
    """Update a globally installed npm package to latest version."""
    if not _is_npm_package_installed(package):
        print_info(t("msg.ai_cli_not_installed", name=display_name))
        return False

    print_info(t("msg.ai_cli_updating", package=package))
    code = run_verbose(["npm", "install", "-g", f"{package}@latest"])
    if code != 0:
        print_error(t("msg.ai_cli_update_failed", name=display_name))
        return False

    print_success(t("msg.ai_cli_update_success", name=display_name))
    return True


def _get_installed_clis() -> list[dict]:
    """Return list of AI CLI options that are currently installed."""
    installed = []
    for opt in AI_CLI_OPTIONS:
        if opt["id"] == "all":
            continue
        if _is_npm_package_installed(opt["package"]):
            installed.append(opt)
    return installed


MAIN_MENU = [
    {
        "id": "install",
        "name_key": "msg.ai_cli_menu_install",
        "desc_key": "msg.ai_cli_menu_install_desc",
    },
    {
        "id": "update",
        "name_key": "msg.ai_cli_menu_update",
        "desc_key": "msg.ai_cli_menu_update_desc",
    },
]


class AiCliSetup(Tool):
    name = "ai-cli-setup"
    display_name = "AI CLI Setup"
    description = "One-click install AI coding assistant CLIs (Claude Code, Codex, Gemini, OpenCode)"
    distros = ["arch", "debian", "fedora", "suse", "unknown"]

    def _ensure_nodejs(self, distro: str) -> bool:
        """Ensure Node.js and npm are available. Returns False on failure."""
        if not _has_nodejs():
            print_info(t("msg.ai_cli_nodejs_not_found"))
            if not _install_nodejs(distro):
                return False
        else:
            version = _get_node_version()
            print_info(t("msg.ai_cli_nodejs_detected", version=version or "unknown"))

        if not _has_npm():
            print_error(t("msg.ai_cli_npm_not_found"))
            return False

        return True

    def _run_install(self) -> bool | None:
        """Install flow: let user pick a CLI to install."""
        choice = prompt_selection(t("msg.ai_cli_select"), AI_CLI_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        console.print()

        if choice == "all":
            ok = True
            for opt in AI_CLI_OPTIONS:
                if opt["id"] == "all":
                    continue
                display_name = t(opt["name_key"])
                if not _install_npm_package(opt["package"], display_name):
                    ok = False
            return ok

        selected = next((opt for opt in AI_CLI_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        display_name = t(selected["name_key"])
        return _install_npm_package(selected["package"], display_name)

    def _run_update(self) -> bool | None:
        """Update flow: let user pick an installed CLI to update."""
        installed = _get_installed_clis()
        if not installed:
            print_info(t("msg.ai_cli_none_installed"))
            return None

        # Build options: each installed CLI + "update all installed"
        update_options = [
            {
                "id": opt["id"],
                "name_key": opt["name_key"],
                "desc_key": opt["desc_key"],
            }
            for opt in installed
        ]
        update_options.append({
            "id": "all-installed",
            "name_key": "msg.ai_cli_update_all",
            "desc_key": "msg.ai_cli_update_all_desc",
        })

        choice = prompt_selection(t("msg.ai_cli_update_select"), update_options)

        if choice is None or choice == BACK_ACTION:
            return None

        console.print()

        if choice == "all-installed":
            ok = True
            for opt in installed:
                display_name = t(opt["name_key"])
                if not _update_npm_package(opt["package"], display_name):
                    ok = False
            return ok

        selected = next((opt for opt in installed if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        display_name = t(selected["name_key"])
        return _update_npm_package(selected["package"], display_name)

    def run(self) -> bool | None:
        distro = detect_distro()

        if not self._ensure_nodejs(distro):
            return False

        # Main menu: Install / Update
        choice = prompt_selection(t("msg.ai_cli_menu"), MAIN_MENU)

        if choice is None or choice == BACK_ACTION:
            return None

        if choice == "install":
            return self._run_install()
        elif choice == "update":
            return self._run_update()

        return None
