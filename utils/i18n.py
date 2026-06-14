"""Internationalization (i18n) module for LinuxScriptToolbox.

This module provides translation support for English and Chinese.

Translation Key Conventions:
- UI elements: "ui.<element>"
- Tool display names: "tool.<tool-name>.display_name"
- Tool descriptions: "tool.<tool-name>.description"
- Messages: "msg.<category>_<message>"
- Group names: "ui.group_<group>"

Sections:
- UI: General interface elements
- Tools: Tool display names and descriptions
- Messages: Tool-specific messages (grouped by tool)
"""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

SUPPORTED_LANGS = {"en": "English", "zh": "中文"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # ============================================================
        # UI Elements
        # ============================================================
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
        "ui.group_fedora": "Fedora",
        "ui.group_suse": "openSUSE",
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
        "tool.ai-cli-setup.display_name": "AI CLI Setup",
        "tool.ai-cli-setup.description": "One-click install AI coding assistant CLIs (Claude Code, Codex, Gemini, OpenCode, MiMo)",
        "tool.system-cleanup.display_name": "System Cleanup",
        "tool.system-cleanup.description": "Clean package caches, journal logs, and temporary files",
        "tool.system-info.display_name": "System Info",
        "tool.system-info.description": "Display hardware overview, disk usage, network status, and services",
        "tool.backup-restore.display_name": "Backup/Restore",
        "tool.backup-restore.description": "Backup and restore critical system configuration files",

        # ============================================================
        # Messages — Common (shared across tools)
        # ============================================================
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

        # ============================================================
        # Messages — Dev Tools
        # ============================================================
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

        # ============================================================
        # Messages — Quick Fixes
        # ============================================================
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
        # Git Proxy Fix
        "msg.qfix_git_proxy": "Git Proxy Configuration",
        "msg.qfix_git_proxy_desc": "Configure Git HTTP/HTTPS proxy settings",
        "msg.qfix_git_proxy_configuring": "Configuring Git proxy...",
        "msg.qfix_git_proxy_current": "Current proxy settings: HTTP={http}, HTTPS={https}",
        "msg.qfix_git_proxy_overwrite": "Overwrite existing proxy settings?",
        "msg.qfix_git_proxy_enter": "Enter proxy URL (e.g., http://proxy:8080): ",
        "msg.qfix_git_proxy_empty": "No proxy URL entered, cancelled.",
        "msg.qfix_git_proxy_set": "Git proxy set to: {proxy}",
        # npm Permissions Fix
        "msg.qfix_npm_permissions": "npm Global Permissions Fix",
        "msg.qfix_npm_permissions_desc": "Fix npm global directory permissions for current user",
        "msg.qfix_npm_configuring": "Configuring npm global directory...",
        "msg.qfix_npm_not_found": "npm is not installed.",
        "msg.qfix_npm_prefix_failed": "Failed to get npm prefix.",
        "msg.qfix_npm_already_ok": "npm global directory is already user-owned.",
        "msg.qfix_npm_creating": "Creating user npm directory: {dir}",
        "msg.qfix_npm_create_failed": "Failed to create npm directory: {error}",
        "msg.qfix_npm_updating_profile": "Updating shell profile: {profile}",
        "msg.qfix_npm_success": "npm global directory configured: {dir}",
        "msg.qfix_npm_reload_hint": "Run 'source ~/.bashrc' or restart your shell to apply changes.",
        # Docker Group Fix
        "msg.qfix_docker_group": "Docker Group Fix",
        "msg.qfix_docker_group_desc": "Add current user to docker group",
        "msg.qfix_docker_configuring": "Configuring Docker group...",
        "msg.qfix_docker_not_found": "Docker is not installed.",
        "msg.qfix_docker_already_in_group": "User '{user}' is already in docker group.",
        "msg.qfix_docker_creating_group": "Creating docker group...",
        "msg.qfix_docker_adding_user": "Adding user '{user}' to docker group...",
        "msg.qfix_docker_add_failed": "Failed to add user to docker group.",
        "msg.qfix_docker_success": "User '{user}' added to docker group.",
        "msg.qfix_docker_logout_hint": "Please log out and log back in for changes to take effect.",

        # ============================================================
        # Messages — Shorin Setup
        # ============================================================
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
        "msg.shorin_fedora_mode": "Fedora mode: using adapted setup...",
        "msg.shorin_suse_mode": "openSUSE mode: using adapted setup...",
        "msg.shorin_dms_download": "Downloading DMS...",
        "msg.shorin_dms_manual": "DMS not available for this distro, install manually.",
        "msg.shorin_build_quickshell": "Building quickshell from source...",
        "msg.shorin_niri_not_available": "Niri is not available for this distro.",
        "msg.selected_desktop": "Selected: {de}",

        # ============================================================
        # Messages — AI CLI Setup
        # ============================================================
        "msg.ai_cli_select": "Select AI CLI to install:",
        "msg.ai_cli_claude": "Claude Code",
        "msg.ai_cli_claude_desc": "Anthropic's AI coding assistant (claude-code)",
        "msg.ai_cli_codex": "Codex CLI",
        "msg.ai_cli_codex_desc": "OpenAI's coding agent CLI (codex)",
        "msg.ai_cli_gemini": "Gemini CLI",
        "msg.ai_cli_gemini_desc": "Google's Gemini AI CLI (gemini-cli)",
        "msg.ai_cli_opencode": "OpenCode",
        "msg.ai_cli_opencode_desc": "SST's terminal AI coding agent (opencode-ai)",
        "msg.ai_cli_mimo": "MiMo Code",
        "msg.ai_cli_mimo_desc": "Xiaomi's AI coding assistant (mimo)",
        "msg.ai_cli_all": "All AI CLIs",
        "msg.ai_cli_all_desc": "Install all available AI CLI tools",
        "msg.ai_cli_installing": "Installing {package}...",
        "msg.ai_cli_install_success": "{name} installed successfully.",
        "msg.ai_cli_install_failed": "Failed to install {name}.",
        "msg.ai_cli_already_installed": "{name} is already installed.",
        "msg.ai_cli_nodejs_not_found": "Node.js not found, installing...",
        "msg.ai_cli_nodejs_detected": "Node.js detected: {version}",
        "msg.ai_cli_nodejs_installing": "Installing Node.js and npm...",
        "msg.ai_cli_nodejs_installed": "Node.js and npm installed successfully.",
        "msg.ai_cli_nodejs_install_failed": "Failed to install Node.js.",
        "msg.ai_cli_nodejs_unknown": "Cannot auto-install Node.js for this distro. Please install manually.",
        "msg.ai_cli_npm_not_found": "npm not found. Please install Node.js manually.",
        "msg.ai_cli_menu": "Select action:",
        "msg.ai_cli_menu_install": "Install",
        "msg.ai_cli_menu_install_desc": "Install new AI CLI tools",
        "msg.ai_cli_menu_update": "Update",
        "msg.ai_cli_menu_update_desc": "Update installed AI CLI tools to latest version",
        "msg.ai_cli_update_select": "Select AI CLI to update:",
        "msg.ai_cli_updating": "Updating {package}...",
        "msg.ai_cli_update_success": "{name} updated successfully.",
        "msg.ai_cli_update_failed": "Failed to update {name}.",
        "msg.ai_cli_not_installed": "{name} is not installed, skipping.",
        "msg.ai_cli_none_installed": "No AI CLI tools are currently installed.",
        "msg.ai_cli_update_all": "Update All Installed",
        "msg.ai_cli_update_all_desc": "Update all installed AI CLI tools",

        # ============================================================
        # Messages — System Cleanup
        # ============================================================
        "msg.cleanup_select": "Select cleanup option:",
        "msg.cleanup_pkg_cache": "Package Cache",
        "msg.cleanup_pkg_cache_desc": "Clean package manager cache",
        "msg.cleanup_journal": "Journal Logs",
        "msg.cleanup_journal_desc": "Clean systemd journal logs older than 7 days",
        "msg.cleanup_temp": "Temporary Files",
        "msg.cleanup_temp_desc": "Clean temporary files and user cache",
        "msg.cleanup_all": "All Cleanup",
        "msg.cleanup_all_desc": "Run all cleanup operations",
        "msg.cleanup_pkg_cache_running": "Cleaning package cache...",
        "msg.cleanup_pkg_cache_success": "Package cache cleaned successfully.",
        "msg.cleanup_pkg_cache_failed": "Failed to clean package cache.",
        "msg.cleanup_journal_running": "Cleaning journal logs...",
        "msg.cleanup_journal_size": "Current journal size: {size}",
        "msg.cleanup_journal_not_found": "journalctl not found, skipping.",
        "msg.cleanup_journal_success": "Journal logs cleaned successfully.",
        "msg.cleanup_journal_failed": "Failed to clean journal logs.",
        "msg.cleanup_temp_running": "Cleaning temporary files...",
        "msg.cleanup_temp_partial": "Some temporary files could not be deleted.",
        "msg.cleanup_temp_cache_size": "User cache size: {size}",
        "msg.cleanup_temp_success": "Temporary files cleaned successfully.",
        "msg.cleanup_temp_error": "Error cleaning cache: {error}",
        "msg.cleanup_temp_no_cache": "No user cache directory found.",

        # ============================================================
        # Messages — System Info
        # ============================================================
        "msg.info_select": "Select information to display:",
        "msg.info_hardware": "Hardware Overview",
        "msg.info_hardware_desc": "Display CPU, memory, and GPU information",
        "msg.info_disk": "Disk Usage",
        "msg.info_disk_desc": "Display disk usage and largest directories",
        "msg.info_network": "Network Status",
        "msg.info_network_desc": "Display IP addresses, DNS, and connections",
        "msg.info_services": "Services Status",
        "msg.info_services_desc": "Display running services and recent errors",
        "msg.info_all": "All Information",
        "msg.info_all_desc": "Display all system information",
        "msg.info_hardware_running": "Hardware Information:",
        "msg.info_disk_running": "Disk Usage:",
        "msg.info_disk_home": "Largest directories in home:",
        "msg.info_network_running": "Network Status:",
        "msg.info_network_connections": "Active connections:",
        "msg.info_services_running": "Services Status:",
        "msg.info_services_failed": "Failed services:",
        "msg.info_services_count": "Running services: {count}",
        "msg.info_services_recent_errors": "Recent errors:",

        # ============================================================
        # Messages — Backup/Restore
        # ============================================================
        "msg.backup_select": "Select operation:",
        "msg.backup_create": "Create Backup",
        "msg.backup_create_desc": "Backup critical system configuration files",
        "msg.backup_restore": "Restore Backup",
        "msg.backup_restore_desc": "Restore configuration files from backup",
        "msg.backup_list": "List Backups",
        "msg.backup_list_desc": "List all available backups",
        "msg.backup_creating": "Creating backup...",
        "msg.backup_file_backed": "Backed up: {file}",
        "msg.backup_file_failed": "Failed to backup {file}: {error}",
        "msg.backup_file_not_found": "Not found: {file}",
        "msg.backup_no_files": "No files to backup.",
        "msg.backup_created": "Backup created: {path} ({count} files)",
        "msg.backup_no_backups": "No backups available.",
        "msg.backup_select_restore": "Select backup to restore:",
        "msg.backup_not_found": "Backup not found: {path}",
        "msg.backup_files_in_backup": "Files in backup: {count}",
        "msg.backup_confirm_restore": "Restore selected backup?",
        "msg.backup_file_restored": "Restored: {file}",
        "msg.backup_restore_failed": "Failed to restore {file}: {error}",
        "msg.backup_restored": "Restored {count} files successfully.",
        "msg.backup_available": "Available backups:",
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
        "ui.group_fedora": "Fedora",
        "ui.group_suse": "openSUSE",
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
        "tool.ai-cli-setup.display_name": "AI CLI 安装",
        "tool.ai-cli-setup.description": "一键安装 AI 编程助手 CLI（Claude Code、Codex、Gemini、OpenCode、MiMo）",
        "tool.system-cleanup.display_name": "系统清理",
        "tool.system-cleanup.description": "清理包缓存、日志和临时文件",
        "tool.system-info.display_name": "系统信息",
        "tool.system-info.description": "显示硬件概览、磁盘使用、网络状态和服务状态",
        "tool.backup-restore.display_name": "备份/恢复",
        "tool.backup-restore.description": "备份和恢复关键系统配置文件",

        # ============================================================
        # Messages — 通用（跨工具共享）
        # ============================================================
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

        # ============================================================
        # Messages — 开发工具
        # ============================================================
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

        # ============================================================
        # Messages — 快捷修复
        # ============================================================
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
        # Git 代理修复
        "msg.qfix_git_proxy": "Git 代理配置",
        "msg.qfix_git_proxy_desc": "配置 Git HTTP/HTTPS 代理设置",
        "msg.qfix_git_proxy_configuring": "正在配置 Git 代理...",
        "msg.qfix_git_proxy_current": "当前代理设置：HTTP={http}，HTTPS={https}",
        "msg.qfix_git_proxy_overwrite": "是否覆盖现有代理设置？",
        "msg.qfix_git_proxy_enter": "输入代理 URL（例如 http://proxy:8080）：",
        "msg.qfix_git_proxy_empty": "未输入代理 URL，已取消。",
        "msg.qfix_git_proxy_set": "Git 代理已设置为：{proxy}",
        # npm 权限修复
        "msg.qfix_npm_permissions": "npm 全局权限修复",
        "msg.qfix_npm_permissions_desc": "修复 npm 全局目录权限，使当前用户可写",
        "msg.qfix_npm_configuring": "正在配置 npm 全局目录...",
        "msg.qfix_npm_not_found": "npm 未安装。",
        "msg.qfix_npm_prefix_failed": "获取 npm 前缀失败。",
        "msg.qfix_npm_already_ok": "npm 全局目录已经是用户可写的。",
        "msg.qfix_npm_creating": "正在创建用户 npm 目录：{dir}",
        "msg.qfix_npm_create_failed": "创建 npm 目录失败：{error}",
        "msg.qfix_npm_updating_profile": "正在更新 shell 配置文件：{profile}",
        "msg.qfix_npm_success": "npm 全局目录已配置：{dir}",
        "msg.qfix_npm_reload_hint": "运行 'source ~/.bashrc' 或重启 shell 以应用更改。",
        # Docker 组修复
        "msg.qfix_docker_group": "Docker 组修复",
        "msg.qfix_docker_group_desc": "将当前用户添加到 docker 组",
        "msg.qfix_docker_configuring": "正在配置 Docker 组...",
        "msg.qfix_docker_not_found": "Docker 未安装。",
        "msg.qfix_docker_already_in_group": "用户 '{user}' 已在 docker 组中。",
        "msg.qfix_docker_creating_group": "正在创建 docker 组...",
        "msg.qfix_docker_adding_user": "正在将用户 '{user}' 添加到 docker 组...",
        "msg.qfix_docker_add_failed": "将用户添加到 docker 组失败。",
        "msg.qfix_docker_success": "用户 '{user}' 已添加到 docker 组。",
        "msg.qfix_docker_logout_hint": "请注销并重新登录以使更改生效。",

        # ============================================================
        # Messages — Shorin 环境配置
        # ============================================================
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
        "msg.shorin_fedora_mode": "Fedora 模式：使用适配的安装方式...",
        "msg.shorin_suse_mode": "openSUSE 模式：使用适配的安装方式...",
        "msg.shorin_dms_download": "正在下载 DMS...",
        "msg.shorin_dms_manual": "当前发行版不支持 DMS，请手动安装。",
        "msg.shorin_build_quickshell": "正在从源码编译 quickshell...",
        "msg.shorin_niri_not_available": "当前发行版不支持 Niri。",
        "msg.selected_desktop": "已选择：{de}",

        # ============================================================
        # Messages — AI CLI 安装
        # ============================================================
        "msg.ai_cli_select": "选择要安装的 AI CLI：",
        "msg.ai_cli_claude": "Claude Code",
        "msg.ai_cli_claude_desc": "Anthropic 的 AI 编程助手（claude-code）",
        "msg.ai_cli_codex": "Codex CLI",
        "msg.ai_cli_codex_desc": "OpenAI 的编程代理 CLI（codex）",
        "msg.ai_cli_gemini": "Gemini CLI",
        "msg.ai_cli_gemini_desc": "Google 的 Gemini AI CLI（gemini-cli）",
        "msg.ai_cli_opencode": "OpenCode",
        "msg.ai_cli_opencode_desc": "SST 的终端 AI 编程代理（opencode-ai）",
        "msg.ai_cli_mimo": "MiMo Code",
        "msg.ai_cli_mimo_desc": "小米的 AI 编程助手（mimo）",
        "msg.ai_cli_all": "全部 AI CLI",
        "msg.ai_cli_all_desc": "安装所有可用的 AI CLI 工具",
        "msg.ai_cli_installing": "正在安装 {package}...",
        "msg.ai_cli_install_success": "{name} 安装成功。",
        "msg.ai_cli_install_failed": "{name} 安装失败。",
        "msg.ai_cli_already_installed": "{name} 已安装。",
        "msg.ai_cli_nodejs_not_found": "未检测到 Node.js，正在安装...",
        "msg.ai_cli_nodejs_detected": "已检测到 Node.js：{version}",
        "msg.ai_cli_nodejs_installing": "正在安装 Node.js 和 npm...",
        "msg.ai_cli_nodejs_installed": "Node.js 和 npm 安装成功。",
        "msg.ai_cli_nodejs_install_failed": "Node.js 安装失败。",
        "msg.ai_cli_nodejs_unknown": "无法为此发行版自动安装 Node.js，请手动安装。",
        "msg.ai_cli_npm_not_found": "npm 未找到，请手动安装 Node.js。",
        "msg.ai_cli_menu": "选择操作：",
        "msg.ai_cli_menu_install": "安装",
        "msg.ai_cli_menu_install_desc": "安装新的 AI CLI 工具",
        "msg.ai_cli_menu_update": "更新",
        "msg.ai_cli_menu_update_desc": "将已安装的 AI CLI 工具更新到最新版本",
        "msg.ai_cli_update_select": "选择要更新的 AI CLI：",
        "msg.ai_cli_updating": "正在更新 {package}...",
        "msg.ai_cli_update_success": "{name} 更新成功。",
        "msg.ai_cli_update_failed": "{name} 更新失败。",
        "msg.ai_cli_not_installed": "{name} 未安装，跳过。",
        "msg.ai_cli_none_installed": "当前没有已安装的 AI CLI 工具。",
        "msg.ai_cli_update_all": "更新全部已安装",
        "msg.ai_cli_update_all_desc": "更新所有已安装的 AI CLI 工具",

        # ============================================================
        # Messages — 系统清理
        # ============================================================
        "msg.cleanup_select": "选择清理选项：",
        "msg.cleanup_pkg_cache": "包缓存",
        "msg.cleanup_pkg_cache_desc": "清理包管理器缓存",
        "msg.cleanup_journal": "日志",
        "msg.cleanup_journal_desc": "清理 7 天前的 systemd 日志",
        "msg.cleanup_temp": "临时文件",
        "msg.cleanup_temp_desc": "清理临时文件和用户缓存",
        "msg.cleanup_all": "全部清理",
        "msg.cleanup_all_desc": "执行所有清理操作",
        "msg.cleanup_pkg_cache_running": "正在清理包缓存...",
        "msg.cleanup_pkg_cache_success": "包缓存清理成功。",
        "msg.cleanup_pkg_cache_failed": "包缓存清理失败。",
        "msg.cleanup_journal_running": "正在清理日志...",
        "msg.cleanup_journal_size": "当前日志大小：{size}",
        "msg.cleanup_journal_not_found": "journalctl 未找到，跳过。",
        "msg.cleanup_journal_success": "日志清理成功。",
        "msg.cleanup_journal_failed": "日志清理失败。",
        "msg.cleanup_temp_running": "正在清理临时文件...",
        "msg.cleanup_temp_partial": "部分临时文件无法删除。",
        "msg.cleanup_temp_cache_size": "用户缓存大小：{size}",
        "msg.cleanup_temp_success": "临时文件清理成功。",
        "msg.cleanup_temp_error": "清理缓存时出错：{error}",
        "msg.cleanup_temp_no_cache": "未找到用户缓存目录。",

        # ============================================================
        # Messages — 系统信息
        # ============================================================
        "msg.info_select": "选择要显示的信息：",
        "msg.info_hardware": "硬件概览",
        "msg.info_hardware_desc": "显示 CPU、内存和 GPU 信息",
        "msg.info_disk": "磁盘使用",
        "msg.info_disk_desc": "显示磁盘使用情况和最大目录",
        "msg.info_network": "网络状态",
        "msg.info_network_desc": "显示 IP 地址、DNS 和连接",
        "msg.info_services": "服务状态",
        "msg.info_services_desc": "显示运行中的服务和最近错误",
        "msg.info_all": "全部信息",
        "msg.info_all_desc": "显示所有系统信息",
        "msg.info_hardware_running": "硬件信息：",
        "msg.info_disk_running": "磁盘使用：",
        "msg.info_disk_home": "主目录中最大的目录：",
        "msg.info_network_running": "网络状态：",
        "msg.info_network_connections": "活动连接：",
        "msg.info_services_running": "服务状态：",
        "msg.info_services_failed": "失败的服务：",
        "msg.info_services_count": "运行中的服务：{count}",
        "msg.info_services_recent_errors": "最近错误：",

        # ============================================================
        # Messages — 备份/恢复
        # ============================================================
        "msg.backup_select": "选择操作：",
        "msg.backup_create": "创建备份",
        "msg.backup_create_desc": "备份关键系统配置文件",
        "msg.backup_restore": "恢复备份",
        "msg.backup_restore_desc": "从备份恢复配置文件",
        "msg.backup_list": "列出备份",
        "msg.backup_list_desc": "列出所有可用备份",
        "msg.backup_creating": "正在创建备份...",
        "msg.backup_file_backed": "已备份：{file}",
        "msg.backup_file_failed": "备份 {file} 失败：{error}",
        "msg.backup_file_not_found": "未找到：{file}",
        "msg.backup_no_files": "没有文件可备份。",
        "msg.backup_created": "备份已创建：{path}（{count} 个文件）",
        "msg.backup_no_backups": "没有可用备份。",
        "msg.backup_select_restore": "选择要恢复的备份：",
        "msg.backup_not_found": "备份未找到：{path}",
        "msg.backup_files_in_backup": "备份中的文件：{count}",
        "msg.backup_confirm_restore": "是否恢复所选备份？",
        "msg.backup_file_restored": "已恢复：{file}",
        "msg.backup_restore_failed": "恢复 {file} 失败：{error}",
        "msg.backup_restored": "已成功恢复 {count} 个文件。",
        "msg.backup_available": "可用备份：",
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
