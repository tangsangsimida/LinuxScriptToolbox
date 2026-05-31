import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

SUPPORTED_LANGS = {"en": "English", "zh": "中文"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # UI
        "ui.available_tools": "Available tools:",
        "ui.run_all": "Run all tools",
        "ui.language": "Language",
        "ui.quit": "Quit",
        "ui.select": "Select: ",
        "ui.detected": "Detected: {distro}",
        "ui.no_tools": "No tools available for this distro.",
        "ui.press_enter": "Press Enter to continue...",
        "ui.running": "--- Running: {name} ---",
        "ui.invalid_selection": "Invalid selection",
        "ui.invalid_input": "Invalid input",
        "ui.goodbye": "Goodbye!",
        "ui.back": "Back",
        "ui.select_language": "Select language:",
        "ui.arrow_hint": "Type a number/letter to select, or use ↑↓ to navigate",
        "ui.group_common": "Common",
        "ui.group_arch": "Arch Linux",
        "ui.group_debian": "Debian/Ubuntu",
        # Tools
        "tool.mirror-optimizer.display_name": "Optimize Mirrors",
        "tool.mirror-optimizer.description": "Replace package manager mirrors with China mirrors (supports any distro)",
        "tool.device-init.display_name": "Initialize Device",
        "tool.device-init.description": "Set up SSH access (install, password, config, firewall) and python alias",
        "tool.dev-tools.display_name": "Dev Tools Setup",
        "tool.dev-tools.description": "Quick install embedded toolchains (ARM GCC, RISC-V GCC)",
        "tool.quick-fixes.display_name": "Quick Fixes",
        "tool.quick-fixes.description": "One-click fixes for common Linux software issues",
        "tool.shorin-setup.display_name": "Shorin Setup",
        "tool.shorin-setup.description": "Clone and run shorin-arch-setup for desktop environment configuration",
        # Messages
        "msg.backup_saved": "Backup saved to {path}",
        "msg.backup_exists": "Backup already exists, skipped",
        "msg.mirrorlist_updated": "Mirrorlist updated with China mirrors at top",
        "msg.mirrorlist_not_found": "Error: /etc/pacman.d/mirrorlist not found",
        "msg.sources_list_not_found": "Error: No APT sources file found",
        "msg.sources_list_updated": "APT sources updated with China mirror",
        "msg.detected_format": "Detected {format} format: {path}",
        "msg.detected_pm": "Detected package manager: {pm}",
        "msg.root_required": "Root privileges required",
        "msg.command_timeout": "Command timed out after {seconds}s: {cmd}",
        "msg.no_pkg_manager": "No supported package manager found (pacman/apt/dnf/zypper)",
        "msg.repo_dir_not_found": "Repo directory not found: {path}",
        "msg.repo_files_not_found": "No repo files found",
        "msg.pm_pacman": "pacman (Arch Linux)",
        "msg.pm_apt": "apt (Debian/Ubuntu)",
        "msg.pm_dnf": "dnf (Fedora)",
        "msg.pm_zypper": "zypper (openSUSE)",
        "msg.installing": "Installing {package}...",
        "msg.install_success": "{package} installed successfully.",
        "msg.install_failed": "Failed to install {package}.",
        "msg.already_installed": "{package} is already installed.",
        "msg.service_started": "Service {service} started.",
        "msg.service_already_running": "Service {service} is already running.",
        "msg.service_start_failed": "Failed to start service {service}.",
        "msg.service_enabled": "Service {service} enabled on boot.",
        "msg.service_already_enabled": "Service {service} is already enabled on boot.",
        "msg.service_enable_failed": "Failed to enable service {service}.",
        "msg.python3_not_found": "python3 not found, skipping alias setup.",
        "msg.python_already_exists": "'python' command already exists, skipped.",
        "msg.python_alias_created": "Created alias python=python3 in {path}",
        "msg.step_password": "[4/6] Checking user password...",
        "msg.step_sshd_config": "[5/6] Configuring sshd...",
        "msg.step_firewall": "[6/6] Checking firewall...",
        "msg.password_not_set": "No password set for user '{user}'.",
        "msg.enter_password": "Enter new password: ",
        "msg.confirm_password": "Confirm password: ",
        "msg.password_set_success": "Password set for user '{user}'.",
        "msg.password_mismatch": "Passwords do not match, skipping.",
        "msg.password_set_failed": "Failed to set password.",
        "msg.password_already_set": "User '{user}' already has a password.",
        "msg.checking_sshd_config": "Checking sshd configuration...",
        "msg.sshd_config_backup": "Backup saved to {path}",
        "msg.password_auth_enabled": "PasswordAuthentication enabled in sshd_config.",
        "msg.password_auth_already": "PasswordAuthentication is already enabled.",
        "msg.sshd_restarted": "sshd service restarted.",
        "msg.firewall_detected": "Detected firewall: {fw}",
        "msg.firewall_no_active": "No active firewall detected, skipped.",
        "msg.firewall_allow_ssh": "Allow SSH through firewall?",
        "msg.firewall_rule_added": "Firewall rule added: allow SSH (port 22).",
        "msg.apt_update": "Updating package lists...",
        # Dev Tools
        "msg.devtool_select": "Select toolchain to install:",
        "msg.devtool_arm_gcc": "ARM GCC Toolchain",
        "msg.devtool_arm_gcc_desc": "Install arm-none-eabi-gcc for ARM Cortex-R/M embedded development",
        "msg.devtool_riscv_gcc": "RISC-V GCC Toolchain",
        "msg.devtool_riscv_gcc_desc": "Install riscv64-elf-gcc for RISC-V embedded development",
        "msg.devtool_all": "All Toolchains",
        "msg.devtool_all_desc": "Install all available toolchains",
        "msg.devtool_installing": "Installing: {packages}...",
        "msg.devtool_already_installed": "{toolchain} is already installed.",
        "msg.devtool_install_success": "{toolchain} installed successfully.",
        "msg.devtool_install_failed": "Failed to install toolchain.",
        # Quick Fixes
        "msg.qfix_select": "Select a fix to apply:",
        "msg.qfix_stm32cubemx": "STM32CubeMX Wayland Fix",
        "msg.qfix_stm32cubemx_desc": "Fix blank popup/dialog windows in STM32CubeMX on Wayland",
        "msg.qfix_detecting_path": "Detecting STM32CubeMX installation...",
        "msg.qfix_found": "Found: {path}",
        "msg.qfix_not_found": "STM32CubeMX not found in common paths.",
        "msg.qfix_enter_path": "Enter STM32CubeMX path: ",
        "msg.qfix_path_invalid": "Invalid path: {path}",
        "msg.qfix_creating_wrapper": "Creating wrapper script...",
        "msg.qfix_wrapper_created": "Wrapper script created: {path}",
        "msg.qfix_wrapper_failed": "Failed to create wrapper script: {error}",
        "msg.qfix_creating_desktop": "Creating .desktop file...",
        "msg.qfix_desktop_created": "Desktop file created: {path}",
        "msg.qfix_desktop_failed": "Failed to create .desktop file: {error}",
        "msg.qfix_success": "Fix applied successfully!",
        "msg.qfix_usage_hint": "You can run STM32CubeMX via: {wrapper}",
        "msg.qfix_not_implemented": "This fix is not yet implemented.",
        # Shorin
        "msg.cloning": "Cloning {repo}...",
        "msg.clone_failed": "Failed to clone {repo}.",
        "msg.shorin_select": "Select Shorin setup option:",
        "msg.shorin_niri": "Niri Desktop",
        "msg.shorin_niri_desc": "Install niri + DMS + quickshell via shorin-arch-setup",
        "msg.shorin_dms": "DMS (DankMaterialShell)",
        "msg.shorin_dms_desc": "Install DMS + quickshell for existing niri setup",
        "msg.shorin_kde": "KDE Plasma",
        "msg.shorin_kde_desc": "Install KDE Plasma via shorin-arch-setup",
        "msg.shorin_gnome": "GNOME",
        "msg.shorin_gnome_desc": "Install GNOME via shorin-arch-setup",
        "msg.script_not_found": "Script not found: {script}",
        "msg.running_script": "Running {script}...",
        "msg.shorin_ubuntu_mode": "Ubuntu mode: using adapted setup...",
        "msg.shorin_dms_download": "Downloading DMS...",
        "msg.shorin_dms_manual": "DMS not available via PPA, install manually.",
        "msg.shorin_build_quickshell": "Building quickshell from source...",
        "msg.selected_desktop": "Selected: {de}",
    },
    "zh": {
        # UI
        "ui.available_tools": "可用工具：",
        "ui.run_all": "运行全部工具",
        "ui.language": "语言",
        "ui.quit": "退出",
        "ui.select": "选择：",
        "ui.detected": "检测到：{distro}",
        "ui.no_tools": "当前发行版没有可用工具。",
        "ui.press_enter": "按回车键继续...",
        "ui.running": "--- 正在运行：{name} ---",
        "ui.invalid_selection": "无效选择",
        "ui.invalid_input": "无效输入",
        "ui.goodbye": "再见！",
        "ui.back": "返回",
        "ui.select_language": "选择语言：",
        "ui.arrow_hint": "输入编号/字母直接选择，或使用 ↑↓ 方向键导航",
        "ui.group_common": "通用",
        "ui.group_arch": "Arch Linux",
        "ui.group_debian": "Debian/Ubuntu",
        # Tools
        "tool.mirror-optimizer.display_name": "优化镜像源",
        "tool.mirror-optimizer.description": "将包管理器镜像源替换为中国镜像源（支持任意发行版）",
        "tool.device-init.display_name": "设备初始化",
        "tool.device-init.description": "配置 SSH 远程访问（安装、密码、配置、防火墙）及 python 别名",
        "tool.dev-tools.display_name": "开发工具配置",
        "tool.dev-tools.description": "快速安装嵌入式工具链（ARM GCC、RISC-V GCC）",
        "tool.quick-fixes.display_name": "快捷修复",
        "tool.quick-fixes.description": "一键修复常见 Linux 软件问题",
        "tool.shorin-setup.display_name": "Shorin 环境配置",
        "tool.shorin-setup.description": "克隆并运行 shorin-arch-setup 进行桌面环境配置",
        # Messages
        "msg.backup_saved": "备份已保存到 {path}",
        "msg.backup_exists": "备份已存在，已跳过",
        "msg.mirrorlist_updated": "镜像源列表已更新，中国镜像源已添加到顶部",
        "msg.mirrorlist_not_found": "错误：/etc/pacman.d/mirrorlist 不存在",
        "msg.sources_list_not_found": "错误：未找到 APT 源配置文件",
        "msg.sources_list_updated": "APT 源已更新为中国镜像源",
        "msg.detected_format": "检测到 {format} 格式：{path}",
        "msg.detected_pm": "检测到包管理器：{pm}",
        "msg.root_required": "需要 root 权限",
        "msg.command_timeout": "命令超时（{seconds}s）：{cmd}",
        "msg.no_pkg_manager": "未找到支持的包管理器（pacman/apt/dnf/zypper）",
        "msg.repo_dir_not_found": "仓库目录不存在：{path}",
        "msg.repo_files_not_found": "未找到仓库配置文件",
        "msg.pm_pacman": "pacman（Arch Linux）",
        "msg.pm_apt": "apt（Debian/Ubuntu）",
        "msg.pm_dnf": "dnf（Fedora）",
        "msg.pm_zypper": "zypper（openSUSE）",
        "msg.installing": "正在安装 {package}...",
        "msg.install_success": "{package} 安装成功。",
        "msg.install_failed": "{package} 安装失败。",
        "msg.already_installed": "{package} 已安装。",
        "msg.service_started": "服务 {service} 已启动。",
        "msg.service_already_running": "服务 {service} 已在运行。",
        "msg.service_start_failed": "服务 {service} 启动失败。",
        "msg.service_enabled": "服务 {service} 已设置开机自启动。",
        "msg.service_already_enabled": "服务 {service} 已设置开机自启动。",
        "msg.service_enable_failed": "服务 {service} 设置开机自启动失败。",
        "msg.python3_not_found": "未找到 python3，跳过别名配置。",
        "msg.python_already_exists": "'python' 命令已存在，跳过。",
        "msg.python_alias_created": "已创建别名 python=python3（{path}）",
        "msg.step_password": "[4/6] 检查用户密码...",
        "msg.step_sshd_config": "[5/6] 配置 sshd...",
        "msg.step_firewall": "[6/6] 检查防火墙...",
        "msg.password_not_set": "用户 '{user}' 尚未设置密码。",
        "msg.enter_password": "输入新密码：",
        "msg.confirm_password": "确认密码：",
        "msg.password_set_success": "用户 '{user}' 的密码已设置。",
        "msg.password_mismatch": "两次输入的密码不一致，跳过。",
        "msg.password_set_failed": "密码设置失败。",
        "msg.password_already_set": "用户 '{user}' 已有密码。",
        "msg.checking_sshd_config": "检查 sshd 配置...",
        "msg.sshd_config_backup": "备份已保存到 {path}",
        "msg.password_auth_enabled": "sshd_config 中已启用密码认证。",
        "msg.password_auth_already": "密码认证已处于启用状态。",
        "msg.sshd_restarted": "sshd 服务已重启。",
        "msg.firewall_detected": "检测到防火墙：{fw}",
        "msg.firewall_no_active": "未检测到活跃防火墙，跳过。",
        "msg.firewall_allow_ssh": "是否允许 SSH 通过防火墙？",
        "msg.firewall_rule_added": "防火墙规则已添加：允许 SSH（端口 22）。",
        "msg.apt_update": "正在更新软件包列表...",
        # Dev Tools
        "msg.devtool_select": "选择要安装的工具链：",
        "msg.devtool_arm_gcc": "ARM GCC 工具链",
        "msg.devtool_arm_gcc_desc": "安装 arm-none-eabi-gcc，用于 ARM Cortex-R/M 嵌入式开发",
        "msg.devtool_riscv_gcc": "RISC-V GCC 工具链",
        "msg.devtool_riscv_gcc_desc": "安装 riscv64-elf-gcc，用于 RISC-V 嵌入式开发",
        "msg.devtool_all": "全部工具链",
        "msg.devtool_all_desc": "安装所有可用工具链",
        "msg.devtool_installing": "正在安装：{packages}...",
        "msg.devtool_already_installed": "{toolchain} 已安装。",
        "msg.devtool_install_success": "{toolchain} 安装成功。",
        "msg.devtool_install_failed": "工具链安装失败。",
        # Quick Fixes
        "msg.qfix_select": "选择要应用的修复：",
        "msg.qfix_stm32cubemx": "STM32CubeMX Wayland 修复",
        "msg.qfix_stm32cubemx_desc": "修复 STM32CubeMX 在 Wayland 下弹窗/对话框空白问题",
        "msg.qfix_detecting_path": "正在检测 STM32CubeMX 安装路径...",
        "msg.qfix_found": "已找到：{path}",
        "msg.qfix_not_found": "未在常见路径中找到 STM32CubeMX。",
        "msg.qfix_enter_path": "请输入 STM32CubeMX 路径：",
        "msg.qfix_path_invalid": "路径无效：{path}",
        "msg.qfix_creating_wrapper": "正在创建启动脚本...",
        "msg.qfix_wrapper_created": "启动脚本已创建：{path}",
        "msg.qfix_wrapper_failed": "创建启动脚本失败：{error}",
        "msg.qfix_creating_desktop": "正在创建 .desktop 文件...",
        "msg.qfix_desktop_created": ".desktop 文件已创建：{path}",
        "msg.qfix_desktop_failed": "创建 .desktop 文件失败：{error}",
        "msg.qfix_success": "修复已成功应用！",
        "msg.qfix_usage_hint": "可通过以下方式运行 STM32CubeMX：{wrapper}",
        "msg.qfix_not_implemented": "该修复尚未实现。",
        # Shorin
        "msg.cloning": "正在克隆 {repo}...",
        "msg.clone_failed": "克隆 {repo} 失败。",
        "msg.shorin_select": "选择 Shorin 配置选项：",
        "msg.shorin_niri": "Niri 桌面",
        "msg.shorin_niri_desc": "通过 shorin-arch-setup 安装 niri + DMS + quickshell",
        "msg.shorin_dms": "DMS（DankMaterialShell）",
        "msg.shorin_dms_desc": "为现有 niri 安装 DMS + quickshell",
        "msg.shorin_kde": "KDE Plasma",
        "msg.shorin_kde_desc": "通过 shorin-arch-setup 安装 KDE Plasma",
        "msg.shorin_gnome": "GNOME",
        "msg.shorin_gnome_desc": "通过 shorin-arch-setup 安装 GNOME",
        "msg.script_not_found": "脚本未找到：{script}",
        "msg.running_script": "正在运行 {script}...",
        "msg.shorin_ubuntu_mode": "Ubuntu 模式：使用适配的安装方式...",
        "msg.shorin_dms_download": "正在下载 DMS...",
        "msg.shorin_dms_manual": "PPA 中没有 DMS，请手动安装。",
        "msg.shorin_build_quickshell": "正在从源码编译 quickshell...",
        "msg.selected_desktop": "已选择：{de}",
    },
}

_current_lang: str | None = None


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def _save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


def get_lang() -> str:
    global _current_lang
    if _current_lang is None:
        cfg = _load_config()
        _current_lang = cfg.get("lang", "en")
    return _current_lang


def set_lang(lang: str) -> None:
    global _current_lang
    _current_lang = lang
    cfg = _load_config()
    cfg["lang"] = lang
    _save_config(cfg)


def t(key: str, **kwargs) -> str:
    lang = get_lang()
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


def tool_display_name(tool) -> str:
    key = f"tool.{tool.name}.display_name"
    return t(key) if TRANSLATIONS["en"].get(key) else tool.display_name


def tool_description(tool) -> str:
    key = f"tool.{tool.name}.description"
    return t(key) if TRANSLATIONS["en"].get(key) else tool.description
