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
        "ui.select_language": "Select language:",
        # Tools
        "tool.arch-mirror-optimizer.display_name": "Optimize Pacman Mirrors",
        "tool.arch-mirror-optimizer.description": "Add China mirrors to the top of /etc/pacman.d/mirrorlist",
        "tool.debian-mirror-optimizer.display_name": "Optimize APT Mirrors",
        "tool.debian-mirror-optimizer.description": "Replace APT mirrors with China mirrors (supports deb822 and traditional formats)",
        "tool.device-init.display_name": "Initialize Device",
        "tool.device-init.description": "Set up SSH access (install, password, config, firewall) and python alias",
        "tool.locale-setup.display_name": "Locale & Input Method",
        "tool.locale-setup.description": "Set timezone, Chinese locale, and install Fcitx5 + Rime with rime-ice",
        "tool.gpu-driver.display_name": "GPU Driver Setup",
        "tool.gpu-driver.description": "Auto-detect GPU and install appropriate drivers",
        "tool.common-apps.display_name": "Common Apps Installer",
        "tool.common-apps.description": "Install commonly used applications by category",
        "tool.desktop-env.display_name": "Desktop Environment",
        "tool.desktop-env.description": "Install a desktop environment (KDE/GNOME/Sway)",
        "tool.btrfs-snapshot.display_name": "BTRFS Snapshots",
        "tool.btrfs-snapshot.description": "Create, list, and manage BTRFS snapshots via snapper",
        "tool.source-builder.display_name": "Build from Source",
        "tool.source-builder.description": "Compile and install software from source (quickshell, etc.)",
        # Messages
        "msg.backup_saved": "Backup saved to {path}",
        "msg.backup_exists": "Backup already exists, skipped",
        "msg.mirrorlist_updated": "Mirrorlist updated with China mirrors at top",
        "msg.mirrorlist_not_found": "Error: /etc/pacman.d/mirrorlist not found",
        "msg.sources_list_not_found": "Error: No APT sources file found",
        "msg.sources_list_updated": "APT sources updated with China mirror",
        "msg.detected_format": "Detected {format} format: {path}",
        "msg.root_required": "Root privileges required",
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
        "msg.step_timezone": "[1/4] Setting timezone...",
        "msg.step_locale": "[2/4] Configuring locale...",
        "msg.step_fcitx5": "[3/4] Installing Fcitx5 + Rime...",
        "msg.step_rime_ice": "[4/4] Setting up rime-ice...",
        "msg.timezone_set": "Timezone set to Asia/Shanghai.",
        "msg.timezone_already": "Timezone is already Asia/Shanghai.",
        "msg.timezone_failed": "Failed to set timezone.",
        "msg.locale_set": "Locale set to zh_CN.UTF-8.",
        "msg.pam_env_written": "User locale config written to {path}",
        "msg.locale_already": "Locale is already zh_CN.UTF-8.",
        "msg.locale_failed": "Failed to set locale.",
        "msg.locale_gen_not_found": "Error: /etc/locale.gen not found.",
        "msg.locale_not_found": "Error: zh_CN.UTF-8 not found in /etc/locale.gen.",
        "msg.fcitx5_installed": "Fcitx5 + Rime installed.",
        "msg.fcitx5_configured": "Fcitx5 configured: env vars, input sources, autostart.",
        "msg.cloning_rime_ice": "Cloning rime-ice...",
        "msg.rime_ice_ready": "rime-ice downloaded.",
        "msg.rime_ice_update": "rime-ice updated.",
        "msg.rime_ice_failed": "Failed to download rime-ice.",
        "msg.apt_update": "Updating package lists...",
        # GPU
        "msg.gpu_detected": "Detected GPU: {gpu}",
        "msg.no_gpu_detected": "No GPU detected.",
        "msg.installing_gpu_driver": "Installing {gpu} drivers...",
        "msg.no_driver_packages": "No driver packages for {gpu}.",
        # Common apps
        "msg.select_categories": "Select categories to install:",
        "msg.select_all": "Install all",
        "msg.no_categories": "No categories available.",
        "msg.nothing_selected": "Nothing selected.",
        "msg.installing_packages": "Installing {count} packages...",
        "msg.cat_dev": "Development Tools",
        "msg.cat_system": "System Utilities",
        "msg.cat_network": "Network Tools",
        "msg.cat_shell": "Shell (zsh/fish)",
        # Desktop
        "msg.select_desktop": "Select desktop environment:",
        "msg.de_kde": "KDE Plasma",
        "msg.de_gnome": "GNOME",
        "msg.de_niri": "Niri (scrollable tiling Wayland)",
        "msg.de_sway": "Sway (Wayland WM)",
        "msg.adding_ppa": "Adding PPA: {ppa}...",
        "msg.no_desktop_options": "No desktop options available.",
        "msg.selected_desktop": "Selected: {de}",
        "msg.enabling_service": "Enabling service {service}...",
        "msg.service_enabled_on_boot": "Service {service} enabled on boot.",
        "msg.desktop_installed": "Desktop environment installed. Reboot to use.",
        # BTRFS
        "msg.not_btrfs": "Root filesystem is not BTRFS.",
        "msg.snapshot_menu": "BTRFS Snapshot Manager:",
        "msg.snapshot_create": "Create snapshot",
        "msg.snapshot_list": "List snapshots",
        "msg.snapshot_delete": "Delete snapshot",
        "msg.snapshot_rollback": "Rollback to snapshot",
        "msg.snapshot_description": "Description: ",
        "msg.snapshot_created": "Snapshot created.",
        "msg.snapshot_create_failed": "Failed to create snapshot.",
        "msg.snapshot_id": "Snapshot ID: ",
        "msg.snapshot_deleted": "Snapshot deleted.",
        "msg.snapshot_delete_failed": "Failed to delete snapshot.",
        "msg.snapshot_rollback_warning": "WARNING: This will rollback the system to the selected snapshot.",
        "msg.confirm": "Confirm? (y/N): ",
        "msg.snapshot_rolled_back": "System rolled back. Reboot to apply.",
        "msg.snapshot_rollback_failed": "Failed to rollback.",
        # Source builder
        "msg.select_build": "Select software to build:",
        "msg.build_quickshell": "Quickshell (DMS QML runtime)",
        "msg.installing_build_deps": "Installing {count} build dependencies...",
        "msg.build_deps_installed": "Build dependencies already installed.",
        "msg.build_deps_failed": "Failed to install build dependencies.",
        "msg.cloning": "Cloning {repo}...",
        "msg.clone_failed": "Failed to clone {repo}.",
        "msg.configuring": "Configuring build...",
        "msg.configure_failed": "CMake configuration failed.",
        "msg.compiling": "Compiling...",
        "msg.binary_not_found": "Build succeeded but binary not found.",
        "msg.quickshell_installed": "Quickshell installed to {path}",
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
        "ui.select_language": "选择语言：",
        # Tools
        "tool.arch-mirror-optimizer.display_name": "优化 Pacman 镜像源",
        "tool.arch-mirror-optimizer.description": "将中国镜像源添加到 /etc/pacman.d/mirrorlist 顶部",
        "tool.debian-mirror-optimizer.display_name": "优化 APT 镜像源",
        "tool.debian-mirror-optimizer.description": "将 APT 镜像源替换为中国镜像源（支持 deb822 和传统格式）",
        "tool.device-init.display_name": "设备初始化",
        "tool.device-init.description": "配置 SSH 远程访问（安装、密码、配置、防火墙）及 python 别名",
        "tool.locale-setup.display_name": "语言与输入法配置",
        "tool.locale-setup.description": "设置时区、中文语言环境，安装 Fcitx5 + Rime 输入法和雾凇拼音",
        "tool.gpu-driver.display_name": "GPU 驱动安装",
        "tool.gpu-driver.description": "自动检测 GPU 并安装对应驱动",
        "tool.common-apps.display_name": "常用工具安装",
        "tool.common-apps.description": "按分类安装常用应用程序",
        "tool.desktop-env.display_name": "桌面环境安装",
        "tool.desktop-env.description": "安装桌面环境（KDE/GNOME/Sway）",
        "tool.btrfs-snapshot.display_name": "BTRFS 快照管理",
        "tool.btrfs-snapshot.description": "通过 snapper 创建、查看和管理 BTRFS 快照",
        "tool.source-builder.display_name": "源码编译安装",
        "tool.source-builder.description": "从源码编译安装软件（quickshell 等）",
        # Messages
        "msg.backup_saved": "备份已保存到 {path}",
        "msg.backup_exists": "备份已存在，已跳过",
        "msg.mirrorlist_updated": "镜像源列表已更新，中国镜像源已添加到顶部",
        "msg.mirrorlist_not_found": "错误：/etc/pacman.d/mirrorlist 不存在",
        "msg.sources_list_not_found": "错误：未找到 APT 源配置文件",
        "msg.sources_list_updated": "APT 源已更新为中国镜像源",
        "msg.detected_format": "检测到 {format} 格式：{path}",
        "msg.root_required": "需要 root 权限",
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
        "msg.step_timezone": "[1/4] 设置时区...",
        "msg.step_locale": "[2/4] 配置语言环境...",
        "msg.step_fcitx5": "[3/4] 安装 Fcitx5 + Rime...",
        "msg.step_rime_ice": "[4/4] 配置雾凇拼音...",
        "msg.timezone_set": "时区已设置为 Asia/Shanghai。",
        "msg.timezone_already": "时区已是 Asia/Shanghai。",
        "msg.timezone_failed": "时区设置失败。",
        "msg.locale_set": "语言环境已设置为 zh_CN.UTF-8。",
        "msg.pam_env_written": "用户语言配置已写入 {path}",
        "msg.locale_already": "语言环境已是 zh_CN.UTF-8。",
        "msg.locale_failed": "语言环境设置失败。",
        "msg.locale_gen_not_found": "错误：/etc/locale.gen 不存在。",
        "msg.locale_not_found": "错误：/etc/locale.gen 中未找到 zh_CN.UTF-8。",
        "msg.fcitx5_installed": "Fcitx5 + Rime 已安装。",
        "msg.fcitx5_configured": "Fcitx5 已配置：环境变量、输入源、自启动。",
        "msg.cloning_rime_ice": "正在下载雾凇拼音...",
        "msg.rime_ice_ready": "雾凇拼音已下载。",
        "msg.rime_ice_update": "雾凇拼音已更新。",
        "msg.rime_ice_failed": "雾凇拼音下载失败。",
        "msg.apt_update": "正在更新软件包列表...",
        # GPU
        "msg.gpu_detected": "检测到 GPU：{gpu}",
        "msg.no_gpu_detected": "未检测到 GPU。",
        "msg.installing_gpu_driver": "正在安装 {gpu} 驱动...",
        "msg.no_driver_packages": "没有 {gpu} 的驱动包。",
        # Common apps
        "msg.select_categories": "选择要安装的分类：",
        "msg.select_all": "全部安装",
        "msg.no_categories": "没有可用的分类。",
        "msg.nothing_selected": "未选择任何内容。",
        "msg.installing_packages": "正在安装 {count} 个软件包...",
        "msg.cat_dev": "开发工具",
        "msg.cat_system": "系统工具",
        "msg.cat_network": "网络工具",
        "msg.cat_shell": "Shell (zsh/fish)",
        # Desktop
        "msg.select_desktop": "选择桌面环境：",
        "msg.de_kde": "KDE Plasma",
        "msg.de_gnome": "GNOME",
        "msg.de_niri": "Niri（可滚动平铺 Wayland）",
        "msg.de_sway": "Sway (Wayland 窗口管理器)",
        "msg.adding_ppa": "正在添加 PPA：{ppa}...",
        "msg.no_desktop_options": "没有可用的桌面环境选项。",
        "msg.selected_desktop": "已选择：{de}",
        "msg.enabling_service": "正在启用服务 {service}...",
        "msg.service_enabled_on_boot": "服务 {service} 已设置开机自启。",
        "msg.desktop_installed": "桌面环境已安装。重启后生效。",
        # BTRFS
        "msg.not_btrfs": "根文件系统不是 BTRFS。",
        "msg.snapshot_menu": "BTRFS 快照管理器：",
        "msg.snapshot_create": "创建快照",
        "msg.snapshot_list": "查看快照",
        "msg.snapshot_delete": "删除快照",
        "msg.snapshot_rollback": "回滚到快照",
        "msg.snapshot_description": "描述：",
        "msg.snapshot_created": "快照已创建。",
        "msg.snapshot_create_failed": "快照创建失败。",
        "msg.snapshot_id": "快照 ID：",
        "msg.snapshot_deleted": "快照已删除。",
        "msg.snapshot_delete_failed": "快照删除失败。",
        "msg.snapshot_rollback_warning": "警告：这将把系统回滚到所选快照。",
        "msg.confirm": "确认？(y/N)：",
        "msg.snapshot_rolled_back": "系统已回滚。重启后生效。",
        "msg.snapshot_rollback_failed": "回滚失败。",
        # Source builder
        "msg.select_build": "选择要编译的软件：",
        "msg.build_quickshell": "Quickshell（DMS QML 运行时）",
        "msg.installing_build_deps": "正在安装 {count} 个编译依赖...",
        "msg.build_deps_installed": "编译依赖已安装。",
        "msg.build_deps_failed": "编译依赖安装失败。",
        "msg.cloning": "正在克隆 {repo}...",
        "msg.clone_failed": "克隆 {repo} 失败。",
        "msg.configuring": "正在配置...",
        "msg.configure_failed": "CMake 配置失败。",
        "msg.compiling": "正在编译...",
        "msg.binary_not_found": "编译成功但未找到二进制文件。",
        "msg.quickshell_installed": "Quickshell 已安装到 {path}",
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
