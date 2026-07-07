"""Tailscale client setup translations / Tailscale 客户端部署翻译."""

from utils.i18n import register_translations

register_translations("en", {
    # Tool metadata
    "tool.tailscale-client.display_name": "Tailscale Client Setup",
    "tool.tailscale-client.description": "Quick deploy Tailscale client with custom DERP relay",

    # Main menu
    "msg.tc_select_action": "Select action:",
    "msg.tc_menu_generate": "Generate DERPMap Config",
    "msg.tc_menu_generate_desc": "Generate DERPMap JSON for Tailscale ACL",
    "msg.tc_menu_push": "Push DERPMap to Tailscale",
    "msg.tc_menu_push_desc": "Push DERPMap config to current Tailscale ACL (local machine)",
    "msg.tc_menu_install": "Install Tailscale",
    "msg.tc_menu_install_desc": "Install Tailscale on this machine",
    "msg.tc_menu_verify": "Verify DERP Connection",
    "msg.tc_menu_verify_desc": "Run tailscale netcheck to verify DERP relay",
    "msg.tc_menu_guide": "Show Setup Guide",
    "msg.tc_menu_guide_desc": "Step-by-step guide for connecting home and office machines",

    # DERP info input
    "msg.tc_ask_derp_host": "DERP server IP or domain",
    "msg.tc_ask_auto_detect_cert": "Auto-detect certificate fingerprint from server?",
    "msg.tc_detecting_cert": "Connecting to DERP server to detect certificate...",
    "msg.tc_cert_detected": "Certificate fingerprint detected: {cert}",
    "msg.tc_ask_cert_name": "Certificate fingerprint (sha256-raw:xxx, leave empty to skip)",
    "msg.tc_no_cert_warning": "No certificate fingerprint. Clients may need InsecureForTests flag.",
    "msg.tc_ask_derp_port": "DERP port (HTTPS)",
    "msg.tc_ask_stun_port": "STUN port (UDP)",
    "msg.tc_invalid_port": "Invalid port \"{value}\"; using default {default}.",

    # Generate DERPMap
    "msg.tc_generated_derpmap": "Generated DERPMap configuration:",
    "msg.tc_derpmap_instructions": "Copy the 'derpMap' section and add it to your Tailscale ACL file.",
    "msg.tc_derpmap_url": "ACL editor: https://login.tailscale.com/admin/acls/file",

    # Push ACL
    "msg.tc_tailscale_not_installed": "Tailscale is not installed. Run 'Install Tailscale' first.",
    "msg.tc_not_connected": "Tailscale is not connected. Run 'sudo tailscale up' first.",
    "msg.tc_not_logged_in": "Tailscale is not logged in. Run 'sudo tailscale up' to log in.",
    "msg.tc_status_parse_error": "Failed to parse Tailscale status.",
    "msg.tc_pushing_acl": "Pushing DERPMap configuration to Tailscale ACL...",
    "msg.tc_acl_get_failed": "Could not get current ACL via API. Showing manual instructions instead.",
    "msg.tc_manual_acl_instructions": "Please add the following to your Tailscale ACL manually:",
    "msg.tc_acl_pushed": "DERPMap configuration pushed successfully!",
    "msg.tc_acl_push_failed": "Failed to push ACL. You may need to edit it manually.",

    # Install Tailscale
    "msg.tc_already_installed": "Tailscale is already installed.",
    "msg.tc_version": "Version: {version}",
    "msg.tc_install_confirm": "Install Tailscale on this machine?",
    "msg.tc_installing": "Installing Tailscale...",
    "msg.tc_detected_distro": "Detected distribution: {distro}",
    "msg.tc_install_arch": "Installing Tailscale from Arch official repos...",
    "msg.tc_install_debian": "Installing Tailscale via apt (Tailscale official repo)...",
    "msg.tc_install_fedora": "Installing Tailscale via dnf (Tailscale official repo)...",
    "msg.tc_install_suse": "Installing Tailscale via zypper...",
    "msg.tc_install_generic": "Installing Tailscale via official install script...",
    "msg.tc_zypper_failed_fallback": "zypper installation failed, falling back to official script...",
    "msg.tc_adding_repo": "Adding Tailscale package repository...",
    "msg.tc_download_failed": "Failed to download Tailscale install script.",
    "msg.tc_install_failed": "Tailscale installation failed.",
    "msg.tc_install_success": "Tailscale installed successfully!",
    "msg.tc_start_confirm": "Start and connect Tailscale now?",
    "msg.tc_starting": "Starting Tailscale...",
    "msg.tc_started": "Tailscale started. A browser window will open for login.",
    "msg.tc_login_hint": "Log in with the same account on all your machines.",
    "msg.tc_start_failed": "Failed to start Tailscale. Try 'sudo tailscale up' manually.",
    "msg.tc_installing_winget": "Installing Tailscale via winget...",
    "msg.tc_winget_failed": "winget installation failed. Falling back to MSI installer.",
    "msg.tc_downloading_msi": "Downloading Tailscale MSI installer...",
    "msg.tc_installing_msi": "Installing Tailscale MSI...",
    "msg.tc_started_windows": "Tailscale started. The Tailscale window will open for login.",

    # Verify DERP
    "msg.tc_running_netcheck": "Running tailscale netcheck...",
    "msg.tc_netcheck_failed": "Failed to run netcheck. Is Tailscale connected?",
    "msg.tc_derp_reachable": "Custom DERP relay is reachable!",
    "msg.tc_derp_may_not_reachable": "Custom DERP may not be reachable. Check firewall rules.",
    "msg.tc_derp_not_found": "Custom DERP not found in netcheck. Did you configure DERPMap in ACL?",
    "msg.tc_status_header": "Tailscale status:",

    # Setup guide
    "msg.tc_guide_title": "=== Tailscale + Custom DERP Relay Setup Guide ===",
    "msg.tc_guide_step1": "Step 1: Deploy DERP relay server (on your public server)",
    "msg.tc_guide_step1_detail": "  Run 'tailscale-derp' tool on your server to deploy DERP relay.",
    "msg.tc_guide_step2": "Step 2: Configure DERPMap in Tailscale ACL",
    "msg.tc_guide_step2_detail": "  Use 'Generate DERPMap Config' to get the JSON, then add it to\n  https://login.tailscale.com/admin/acls/file",
    "msg.tc_guide_step3": "Step 3: Install Tailscale on all machines",
    "msg.tc_guide_step3_detail": "  Run 'Install Tailscale' on each machine, or use:\n  curl -fsSL https://tailscale.com/install.sh | sh",
    "msg.tc_guide_step4": "Step 4: Connect all machines to the same Tailscale account",
    "msg.tc_guide_step4_detail": "  On each machine: sudo tailscale up\n  Log in with the SAME account (Google/GitHub/Microsoft).",
    "msg.tc_guide_step5": "Step 5: Verify DERP connectivity",
    "msg.tc_guide_step5_detail": "  Run 'Verify DERP Connection' or: tailscale netcheck\n  Look for 'Region custom (900)' in the output.",
    "msg.tc_guide_ssh": "  Then SSH between machines: ssh user@100.x.x.x\n  (Get IPs from: tailscale status)",
})

register_translations("zh", {
    # Tool metadata
    "tool.tailscale-client.display_name": "Tailscale 客户端部署",
    "tool.tailscale-client.description": "快捷部署 Tailscale 客户端并配置自定义 DERP 中继",

    # Main menu
    "msg.tc_select_action": "选择操作：",
    "msg.tc_menu_generate": "生成 DERPMap 配置",
    "msg.tc_menu_generate_desc": "生成用于 Tailscale ACL 的 DERPMap JSON",
    "msg.tc_menu_push": "推送 DERPMap 到 Tailscale",
    "msg.tc_menu_push_desc": "将 DERPMap 配置推送到当前 Tailscale ACL（本机）",
    "msg.tc_menu_install": "安装 Tailscale",
    "msg.tc_menu_install_desc": "在本机安装 Tailscale",
    "msg.tc_menu_verify": "验证 DERP 连接",
    "msg.tc_menu_verify_desc": "运行 tailscale netcheck 验证 DERP 中继",
    "msg.tc_menu_guide": "查看设置指南",
    "msg.tc_menu_guide_desc": "连接家里和公司设备的分步指南",

    # DERP info input
    "msg.tc_ask_derp_host": "DERP 服务器 IP 或域名",
    "msg.tc_ask_auto_detect_cert": "是否从服务器自动检测证书指纹？",
    "msg.tc_detecting_cert": "正在连接 DERP 服务器检测证书...",
    "msg.tc_cert_detected": "检测到证书指纹：{cert}",
    "msg.tc_ask_cert_name": "证书指纹（sha256-raw:xxx，留空跳过）",
    "msg.tc_no_cert_warning": "未设置证书指纹，客户端可能需要 InsecureForTests 标志。",
    "msg.tc_ask_derp_port": "DERP 端口（HTTPS）",
    "msg.tc_ask_stun_port": "STUN 端口（UDP）",
    "msg.tc_invalid_port": "无效端口 \"{value}\"；使用默认值 {default}。",

    # Generate DERPMap
    "msg.tc_generated_derpmap": "生成的 DERPMap 配置：",
    "msg.tc_derpmap_instructions": "复制 derpMap 部分，添加到 Tailscale ACL 配置文件中。",
    "msg.tc_derpmap_url": "ACL 编辑器：https://login.tailscale.com/admin/acls/file",

    # Push ACL
    "msg.tc_tailscale_not_installed": "Tailscale 未安装，请先运行「安装 Tailscale」。",
    "msg.tc_not_connected": "Tailscale 未连接，请先运行 sudo tailscale up。",
    "msg.tc_not_logged_in": "Tailscale 未登录，请运行 sudo tailscale up 登录。",
    "msg.tc_status_parse_error": "解析 Tailscale 状态失败。",
    "msg.tc_pushing_acl": "正在推送 DERPMap 配置到 Tailscale ACL...",
    "msg.tc_acl_get_failed": "无法通过 API 获取当前 ACL，改为显示手动配置说明。",
    "msg.tc_manual_acl_instructions": "请手动将以下内容添加到 Tailscale ACL：",
    "msg.tc_acl_pushed": "DERPMap 配置推送成功！",
    "msg.tc_acl_push_failed": "ACL 推送失败，可能需要手动编辑。",

    # Install Tailscale
    "msg.tc_already_installed": "Tailscale 已安装。",
    "msg.tc_version": "版本：{version}",
    "msg.tc_install_confirm": "是否在本机安装 Tailscale？",
    "msg.tc_installing": "正在安装 Tailscale...",
    "msg.tc_detected_distro": "检测到发行版：{distro}",
    "msg.tc_install_arch": "正在从 Arch 官方仓库安装 Tailscale...",
    "msg.tc_install_debian": "正在通过 apt 安装 Tailscale（Tailscale 官方仓库）...",
    "msg.tc_install_fedora": "正在通过 dnf 安装 Tailscale（Tailscale 官方仓库）...",
    "msg.tc_install_suse": "正在通过 zypper 安装 Tailscale...",
    "msg.tc_install_generic": "正在通过官方安装脚本安装 Tailscale...",
    "msg.tc_zypper_failed_fallback": "zypper 安装失败，回退到官方安装脚本...",
    "msg.tc_adding_repo": "正在添加 Tailscale 软件包仓库...",
    "msg.tc_download_failed": "Tailscale 安装脚本下载失败。",
    "msg.tc_install_failed": "Tailscale 安装失败。",
    "msg.tc_install_success": "Tailscale 安装成功！",
    "msg.tc_start_confirm": "是否立即启动并连接 Tailscale？",
    "msg.tc_starting": "正在启动 Tailscale...",
    "msg.tc_started": "Tailscale 已启动，浏览器将打开登录页面。",
    "msg.tc_login_hint": "请在所有设备上使用同一个账号登录。",
    "msg.tc_start_failed": "Tailscale 启动失败，请手动运行 sudo tailscale up。",
    "msg.tc_installing_winget": "正在通过 winget 安装 Tailscale...",
    "msg.tc_winget_failed": "winget 安装失败，回退到 MSI 安装包。",
    "msg.tc_downloading_msi": "正在下载 Tailscale MSI 安装包...",
    "msg.tc_installing_msi": "正在安装 Tailscale MSI...",
    "msg.tc_started_windows": "Tailscale 已启动，将打开 Tailscale 窗口进行登录。",

    # Verify DERP
    "msg.tc_running_netcheck": "正在运行 tailscale netcheck...",
    "msg.tc_netcheck_failed": "netcheck 运行失败，Tailscale 是否已连接？",
    "msg.tc_derp_reachable": "自定义 DERP 中继可达！",
    "msg.tc_derp_may_not_reachable": "自定义 DERP 可能不可达，请检查防火墙规则。",
    "msg.tc_derp_not_found": "未在 netcheck 中发现自定义 DERP，是否已在 ACL 中配置 DERPMap？",
    "msg.tc_status_header": "Tailscale 状态：",

    # Setup guide
    "msg.tc_guide_title": "=== Tailscale + 自定义 DERP 中继设置指南 ===",
    "msg.tc_guide_step1": "第一步：部署 DERP 中继服务器（在公网服务器上）",
    "msg.tc_guide_step1_detail": "  在服务器上运行 tailscale-derp 工具部署 DERP 中继。",
    "msg.tc_guide_step2": "第二步：在 Tailscale ACL 中配置 DERPMap",
    "msg.tc_guide_step2_detail": "  使用「生成 DERPMap 配置」获取 JSON，然后添加到\n  https://login.tailscale.com/admin/acls/file",
    "msg.tc_guide_step3": "第三步：在所有设备上安装 Tailscale",
    "msg.tc_guide_step3_detail": "  在每台设备上运行「安装 Tailscale」，或手动执行：\n  curl -fsSL https://tailscale.com/install.sh | sh",
    "msg.tc_guide_step4": "第四步：所有设备登录同一个 Tailscale 账号",
    "msg.tc_guide_step4_detail": "  每台设备执行：sudo tailscale up\n  使用同一个账号登录（Google/GitHub/Microsoft）。",
    "msg.tc_guide_step5": "第五步：验证 DERP 连通性",
    "msg.tc_guide_step5_detail": "  运行「验证 DERP 连接」或执行：tailscale netcheck\n  检查输出中是否有 Region custom (900)。",
    "msg.tc_guide_ssh": "  然后通过 SSH 互联：ssh user@100.x.x.x\n  （IP 地址通过 tailscale status 查看）",
})
