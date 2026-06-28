"""Tailscale client quick deployment tool with custom DERP relay.

Tailscale 客户端快捷部署工具，配合自定义 DERP 中继使用。

Generates DERPMap configuration, pushes to Tailscale ACL,
and provides client-side setup instructions for connecting
home and office machines through the DERP relay.

生成 DERPMap 配置，推送到 Tailscale ACL，并提供客户端安装指南，
用于通过 DERP 中继连接家里和公司的设备。
"""

from tools.base import Tool
from . import tailscale_client_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_cmd, run_verbose
from utils.i18n import t
from utils.platform import IS_WINDOWS, command_exists
from utils.ui import (
    ask,
    print_success,
    print_error,
    print_info,
    print_warning,
    confirm,
    console,
)

# ── Menu options ─────────────────────────────────────────────────

CLIENT_MENU_OPTIONS = [
    {
        "id": "generate-derpmap",
        "name_key": "msg.tc_menu_generate",
        "desc_key": "msg.tc_menu_generate_desc",
    },
    {
        "id": "push-acl",
        "name_key": "msg.tc_menu_push",
        "desc_key": "msg.tc_menu_push_desc",
    },
    {
        "id": "install-tailscale",
        "name_key": "msg.tc_menu_install",
        "desc_key": "msg.tc_menu_install_desc",
    },
    {
        "id": "verify-derp",
        "name_key": "msg.tc_menu_verify",
        "desc_key": "msg.tc_menu_verify_desc",
    },
    {
        "id": "show-guide",
        "name_key": "msg.tc_menu_guide",
        "desc_key": "msg.tc_menu_guide_desc",
    },
]


# ── Helper functions ─────────────────────────────────────────────


# Get DERP server info from user input.
#
# 从用户输入获取 DERP 服务器信息。
#
# Returns:
#     Dict with 'host', 'cert_name', 'stun_port', 'derp_port',
#     or None if cancelled. / 返回配置字典，取消返回 None。
def _get_derp_info() -> dict | None:
    host = ask(t("msg.tc_ask_derp_host"), default="8.137.164.32")
    if not host:
        return None

    # Try to auto-detect cert fingerprint from server /
    # 尝试从服务器自动检测证书指纹
    cert_name = ""
    if confirm(t("msg.tc_ask_auto_detect_cert"), default=True):
        print_info(t("msg.tc_detecting_cert"))
        code, out = run_cmd([
            "openssl", "s_client", "-connect", f"{host.strip()}:443",
            "-servername", host.strip(),
        ], timeout=10)
        if code == 0:
            # Extract SHA256 fingerprint / 提取 SHA256 指纹
            code2, fp_out = run_cmd([
                "bash", "-c",
                f"echo '{out}' | openssl x509 -fingerprint -sha256 -noout 2>/dev/null",
            ])
            if code2 == 0 and "SHA256 Fingerprint" in fp_out:
                # Convert colon-separated hex to raw format /
                # 将冒号分隔的十六进制转换为 raw 格式
                hex_val = fp_out.split("=")[1].strip().replace(":", "").lower()
                cert_name = f"sha256-raw:{hex_val}"
                print_success(t("msg.tc_cert_detected", cert=cert_name))

    if not cert_name:
        cert_name = ask(t("msg.tc_ask_cert_name"), default="")
        if not cert_name:
            print_warning(t("msg.tc_no_cert_warning"))
            cert_name = ""

    derp_port = ask(t("msg.tc_ask_derp_port"), default="443")
    stun_port = ask(t("msg.tc_ask_stun_port"), default="3478")

    return {
        "host": host.strip(),
        "cert_name": cert_name.strip(),
        "derp_port": int(derp_port.strip()),
        "stun_port": int(stun_port.strip()),
    }


# Generate DERPMap JSON configuration.
#
# 生成 DERPMap JSON 配置。
#
# Args:
#     derp_info: DERP server info dict. / DERP 服务器信息字典。
#
# Returns:
#     DERPMap JSON string. / DERPMap JSON 字符串。
def _generate_derpmap_json(derp_info: dict) -> str:
    node = {
        "Name": "1",
        "RegionID": 900,
        "HostName": derp_info["host"],
        "DERPPort": derp_info["derp_port"],
        "STUNPort": derp_info["stun_port"],
        "InsecureForTests": True,
    }
    if derp_info["cert_name"]:
        node["CertName"] = derp_info["cert_name"]

    derpmap = {
        "Regions": {
            "900": {
                "RegionID": 900,
                "RegionCode": "custom",
                "RegionName": "Custom DERP Relay",
                "Nodes": [node],
            }
        }
    }

    import json
    return json.dumps(derpmap, indent=2)


# Generate the full ACL JSON snippet with DERPMap.
#
# 生成包含 DERPMap 的完整 ACL JSON 片段。
#
# Args:
#     derp_info: DERP server info dict. / DERP 服务器信息字典。
#
# Returns:
#     ACL JSON string with derpMap field. / 包含 derpMap 字段的 ACL JSON 字符串。
def _generate_acl_snippet(derp_info: dict) -> str:
    derpmap_json = _generate_derpmap_json(derp_info)
    return f'''
// === Add this to your Tailscale ACL (https://login.tailscale.com/admin/acls/file) ===
// === 将以下内容添加到 Tailscale ACL 配置中 ===

"derpMap": {derpmap_json}
'''


# ── Action handlers ──────────────────────────────────────────────


# Generate DERPMap configuration and display it.
#
# 生成 DERPMap 配置并显示。
#
# Returns:
#     True if generation succeeded. / 生成成功返回 True。
def _generate_derpmap() -> bool:
    derp_info = _get_derp_info()
    if derp_info is None:
        return None

    console.print()
    print_info(t("msg.tc_generated_derpmap"))
    console.print()

    acl_snippet = _generate_acl_snippet(derp_info)
    console.print(acl_snippet)

    console.print()
    print_info(t("msg.tc_derpmap_instructions"))
    print_info(t("msg.tc_derpmap_url"))

    return True


# Push DERPMap configuration to Tailscale ACL via API.
#
# 通过 API 将 DERPMap 配置推送到 Tailscale ACL。
#
# Returns:
#     True if push succeeded, False otherwise. / 推送成功返回 True，否则返回 False。
def _push_acl() -> bool:
    if not command_exists("tailscale"):
        print_error(t("msg.tc_tailscale_not_installed"))
        return False

    # Check if tailscale is connected / 检查 tailscale 是否已连接
    code, out = run_cmd(["tailscale", "status", "--json"])
    if code != 0:
        print_error(t("msg.tc_not_connected"))
        return False

    import json
    try:
        status = json.loads(out)
        if not status.get("Self"):
            print_error(t("msg.tc_not_logged_in"))
            return False
    except (json.JSONDecodeError, KeyError):
        print_error(t("msg.tc_status_parse_error"))
        return False

    # Get DERP info / 获取 DERP 信息
    derp_info = _get_derp_info()
    if derp_info is None:
        return None

    console.print()
    print_info(t("msg.tc_pushing_acl"))

    # Get current ACL / 获取当前 ACL
    code, current_acl = run_cmd(["tailscale", "debug", "acl", "get"])
    if code != 0:
        print_warning(t("msg.tc_acl_get_failed"))
        print_info(t("msg.tc_manual_acl_instructions"))
        acl_snippet = _generate_acl_snippet(derp_info)
        console.print(acl_snippet)
        return False

    # Merge DERPMap into current ACL / 将 DERPMap 合并到当前 ACL
    try:
        acl = json.loads(current_acl) if current_acl else {}
    except json.JSONDecodeError:
        acl = {}

    derpmap_json = _generate_derpmap_json(derp_info)
    derpmap = json.loads(derpmap_json)
    acl["derpMap"] = derpmap

    # Write to temp file and push / 写入临时文件并推送
    import tempfile
    import os
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="tailscale-acl-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(acl, f, indent=2)
        code = run_verbose(["tailscale", "debug", "acl", "set", tmp_path])
        if code == 0:
            print_success(t("msg.tc_acl_pushed"))
            return True
        else:
            print_error(t("msg.tc_acl_push_failed"))
            print_info(t("msg.tc_manual_acl_instructions"))
            acl_snippet = _generate_acl_snippet(derp_info)
            console.print(acl_snippet)
            return False
    finally:
        os.unlink(tmp_path)


# Install Tailscale on the current machine.
#
# 在当前机器上安装 Tailscale。
#
# Returns:
#     True if installation succeeded, False otherwise. / 安装成功返回 True，否则返回 False。
def _install_tailscale() -> bool:
    if command_exists("tailscale"):
        print_info(t("msg.tc_already_installed"))
        code, out = run_cmd(["tailscale", "version"])
        if code == 0:
            print_info(t("msg.tc_version", version=out.strip()))
        return True

    if not confirm(t("msg.tc_install_confirm")):
        return None

    print_info(t("msg.tc_installing"))

    if IS_WINDOWS:
        return _install_tailscale_windows()

    return _install_tailscale_linux()


# Install Tailscale on Linux.
#
# 在 Linux 上安装 Tailscale。
#
# Returns:
#     True if installation succeeded, False otherwise. / 安装成功返回 True，否则返回 False。
def _install_tailscale_linux() -> bool:
    # Use official install script / 使用官方安装脚本
    code = run_verbose([
        "curl", "-fsSL", "https://tailscale.com/install.sh", "-o", "/tmp/tailscale-install.sh",
    ])
    if code != 0:
        print_error(t("msg.tc_download_failed"))
        return False

    code = run_verbose(["sudo", "bash", "/tmp/tailscale-install.sh"])
    if code != 0:
        print_error(t("msg.tc_install_failed"))
        return False

    print_success(t("msg.tc_install_success"))
    _prompt_start_tailscale()
    return True


# Install Tailscale on Windows.
#
# 在 Windows 上安装 Tailscale。
#
# Returns:
#     True if installation succeeded, False otherwise. / 安装成功返回 True，否则返回 False。
def _install_tailscale_windows() -> bool:
    # Try winget first, fall back to downloading installer /
    # 先尝试 winget，回退到下载安装包
    if command_exists("winget"):
        print_info(t("msg.tc_installing_winget"))
        code = run_verbose([
            "winget", "install", "--id", "Tailscale.Tailscale", "-e",
            "--accept-source-agreements", "--accept-package-agreements",
        ])
        if code == 0:
            print_success(t("msg.tc_install_success"))
            _prompt_start_tailscale()
            return True
        print_warning(t("msg.tc_winget_failed"))

    # Download MSI installer / 下载 MSI 安装包
    print_info(t("msg.tc_downloading_msi"))
    msi_url = "https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi"
    msi_path = "$env:TEMP\\tailscale-setup.msi"
    code = run_verbose([
        "powershell", "-NoProfile", "-Command",
        f"Invoke-WebRequest -Uri '{msi_url}' -OutFile '{msi_path}'",
    ], timeout=120)
    if code != 0:
        print_error(t("msg.tc_download_failed"))
        return False

    print_info(t("msg.tc_installing_msi"))
    code = run_verbose([
        "msiexec", "/i", msi_path, "/quiet", "/norestart",
    ])
    if code != 0:
        print_error(t("msg.tc_install_failed"))
        return False

    print_success(t("msg.tc_install_success"))
    _prompt_start_tailscale()
    return True


# Prompt user to start Tailscale and log in.
#
# 提示用户启动 Tailscale 并登录。
def _prompt_start_tailscale() -> None:
    if not confirm(t("msg.tc_start_confirm"), default=True):
        return

    print_info(t("msg.tc_starting"))
    if IS_WINDOWS:
        # On Windows, start the Tailscale GUI / 在 Windows 上启动 Tailscale 图形界面
        run_verbose(["powershell", "-NoProfile", "-Command", "Start-Process tailscale-ipn"])
        print_success(t("msg.tc_started_windows"))
    else:
        code = run_verbose(["sudo", "tailscale", "up"])
        if code == 0:
            print_success(t("msg.tc_started"))
        else:
            print_warning(t("msg.tc_start_failed"))
            return

    print_info(t("msg.tc_login_hint"))


# Verify DERP relay connectivity.
#
# 验证 DERP 中继连通性。
#
# Returns:
#     True if DERP is reachable. / DERP 可达返回 True。
def _verify_derp() -> bool:
    if not command_exists("tailscale"):
        print_error(t("msg.tc_tailscale_not_installed"))
        return False

    console.print()
    print_info(t("msg.tc_running_netcheck"))

    code, out = run_cmd(["tailscale", "netcheck"])
    if code != 0:
        print_error(t("msg.tc_netcheck_failed"))
        return False

    console.print(out)
    console.print()

    # Check if custom DERP (region 900) is in the output /
    # 检查自定义 DERP（region 900）是否在输出中
    if "900" in out or "custom" in out.lower():
        if "reachable" in out.lower():
            print_success(t("msg.tc_derp_reachable"))
        else:
            print_warning(t("msg.tc_derp_may_not_reachable"))
    else:
        print_warning(t("msg.tc_derp_not_found"))

    # Show Tailscale status / 显示 Tailscale 状态
    console.print()
    print_info(t("msg.tc_status_header"))
    run_verbose(["tailscale", "status"])

    return True


# Show complete setup guide for connecting home and office machines.
#
# 显示连接家里和公司设备的完整设置指南。
#
# Returns:
#     True always. / 始终返回 True。
def _show_guide() -> bool:
    console.print()
    console.print(t("msg.tc_guide_title"))
    console.print()
    console.print(t("msg.tc_guide_step1"))
    console.print(t("msg.tc_guide_step1_detail"))
    console.print()
    console.print(t("msg.tc_guide_step2"))
    console.print(t("msg.tc_guide_step2_detail"))
    console.print()
    console.print(t("msg.tc_guide_step3"))
    console.print(t("msg.tc_guide_step3_detail"))
    console.print()
    console.print(t("msg.tc_guide_step4"))
    console.print(t("msg.tc_guide_step4_detail"))
    console.print()
    console.print(t("msg.tc_guide_step5"))
    console.print(t("msg.tc_guide_step5_detail"))
    console.print()
    console.print(t("msg.tc_guide_ssh"))
    console.print()
    return True


# ── Tool class ───────────────────────────────────────────────────


class TailscaleClient(Tool):
    """Quick deployment tool for Tailscale clients with custom DERP relay.

    Tailscale 客户端快捷部署工具，配合自定义 DERP 中继使用。

    Generates DERPMap configuration for Tailscale ACL, installs Tailscale
    on client machines, and verifies DERP relay connectivity.

    生成 Tailscale ACL 的 DERPMap 配置，在客户端机器上安装 Tailscale，
    并验证 DERP 中继连通性。

    Attributes:
        name: Unique tool identifier. / 工具唯一标识符。
        display_name: Human-readable tool name. / 人类可读的工具名称。
        description: Brief description of the tool. / 工具的简要描述。
        distros: Supported Linux distributions. / 支持的 Linux 发行版列表。
        requires_network: Whether the tool needs network access. / 工具是否需要网络访问。
    """

    name = "tailscale-client"
    display_name = "Tailscale Client Setup"
    description = "Quick deploy Tailscale client with custom DERP relay"
    distros = ["arch", "debian", "fedora", "suse", "unknown", "windows"]
    platforms = ["linux", "windows"]
    requires_network = True
    requires_sudo = True

    def run(self) -> bool | None:
        dispatch = {
            "generate-derpmap": _generate_derpmap,
            "push-acl": _push_acl,
            "install-tailscale": _install_tailscale,
            "verify-derp": _verify_derp,
            "show-guide": _show_guide,
        }

        return self.run_submenu(
            CLIENT_MENU_OPTIONS,
            t("msg.tc_select_action"),
            dispatch,
        )
