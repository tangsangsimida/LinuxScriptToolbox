"""Device initialization tool translations / 设备初始化工具翻译."""

from utils.i18n import register_translations

register_translations("en", {
    # ── Submenu options ──────────────────────────────────────────
    "msg.init_select": "Select an initialization operation:",
    "msg.sep_ssh_service": "SSH Service",
    "msg.sep_other": "Other",
    "msg.init_all": "Full SSH setup (recommended)",
    "msg.init_all_desc": "Install, configure, enable sshd, firewall and print connection info",
    "msg.init_preview": "Preview setup steps",
    "msg.init_preview_desc": "Show what the full setup would do without making changes",
    "msg.init_preview_header": "[DRY-RUN] Full SSH setup would:",
    "msg.init_preview_files": "Modified files: /etc/ssh/sshd_config, firewall rules",
    "msg.init_connection_info": "Print connection info only",
    "msg.init_connection_info_desc": "Display SSH connection details (user, IP, port)",
    "msg.init_install_ssh": "Install SSH server",
    "msg.init_install_ssh_desc": "Install OpenSSH Server package",
    "msg.init_start_ssh": "Start SSH service",
    "msg.init_start_ssh_desc": "Start the sshd service now",
    "msg.init_enable_ssh": "Enable SSH on boot",
    "msg.init_enable_ssh_desc": "Enable sshd service to start automatically",
    "msg.init_set_password": "Set user password",
    "msg.init_set_password_desc": "Set or update the current user's password",
    "msg.init_config_sshd": "Configure sshd",
    "msg.init_config_sshd_desc": "Linux: enable PasswordAuthentication | Windows: set default shell to PowerShell",
    "msg.init_open_firewall": "Open firewall for SSH",
    "msg.init_open_firewall_desc": "Allow SSH port 22 through the firewall",
    "msg.init_python_alias": "Create python alias",
    "msg.init_python_alias_desc": "Create python -> python3 symlink (Linux only)",
    # ── Step messages (shared) ───────────────────────────────────
    "msg.checking_sshd_config": "Checking sshd configuration...",
    "msg.confirm_password": "Confirm password: ",
    "msg.enter_password": "Enter new password: ",
    "msg.firewall_allow_ssh": "Allow SSH through firewall?",
    "msg.firewall_detected": "Detected firewall: {fw}",
    "msg.firewall_no_active": "No active firewall detected, skipped.",
    "msg.firewall_rule_added": "Firewall rule added: allow SSH (port 22).",
    "msg.password_already_set": "User '{user}' already has a password.",
    "msg.password_auth_already": "PasswordAuthentication is already enabled.",
    "msg.password_auth_enabled": "PasswordAuthentication enabled in sshd_config.",
    "msg.password_mismatch": "Passwords do not match, skipping.",
    "msg.password_not_set": "No password set for user '{user}'.",
    "msg.password_set_failed": "Failed to set password.",
    "msg.password_set_success": "Password set for user '{user}'.",
    "msg.python3_not_found": "python3 not found, skipping alias setup.",
    "msg.python_alias_created": "Created alias python=python3 in {path}",
    "msg.python_already_exists": "'python' command already exists, skipped.",
    "msg.service_already_enabled": "Service {service} is already enabled on boot.",
    "msg.service_already_running": "Service {service} is already running.",
    "msg.service_enable_failed": "Failed to enable service {service}.",
    "msg.service_enabled": "Service {service} enabled on boot.",
    "msg.service_start_failed": "Failed to start service {service}.",
    "msg.service_started": "Service {service} started.",
    "msg.sshd_config_backup": "Backup saved to {path}",
    "msg.sshd_restarted": "sshd service restarted.",
    "msg.step_firewall": "Checking firewall...",
    # ── Windows-specific messages ────────────────────────────────
    "msg.win_checking_openssh": "Checking OpenSSH Server installation status...",
    "msg.win_openssh_installed": "OpenSSH Server is already installed.",
    "msg.win_installing_openssh": "Installing OpenSSH Server (this may take a few minutes)...",
    "msg.win_openssh_install_success": "OpenSSH Server installed successfully.",
    "msg.win_starting_sshd": "Starting sshd service...",
    "msg.win_sshd_status": "sshd service status: {status}",
    "msg.win_enabling_sshd": "Setting sshd to automatic startup...",
    "msg.win_sshd_auto_enabled": "sshd service set to automatic startup.",
    "msg.win_password_note": "Password is managed by Windows. Use 'net user <name> <password>' to reset.",
    "msg.win_password_hint": "Current user: {user}. SSH login password is your Windows login password.",
    "msg.win_config_sshd_shell": "Setting default SSH shell to PowerShell...",
    "msg.win_shell_already_set": "Default shell is already set to PowerShell.",
    "msg.win_shell_set_success": "Default SSH shell switched to PowerShell.",
    "msg.win_shell_set_failed": "Failed to set default shell in registry.",
    "msg.win_checking_firewall": "Checking firewall rules...",
    "msg.win_firewall_exists": "Firewall rule for sshd already exists.",
    "msg.win_firewall_success": "Firewall inbound rule created: TCP/22.",
    "msg.win_firewall_failed": "Failed to create firewall rule.",
    "msg.win_python_alias_skip": "python alias is not needed on Windows, skipped.",
    "msg.win_ps_failed": "PowerShell command failed: {cmd}... | {err}",
    "msg.win_conn_info_notes": (
        "Notes:\n"
        "  - Password: Use your current Windows login password.\n"
        "  - Microsoft Account: username may be the email prefix; run 'whoami' to confirm.\n"
        "  - Reset password: net user <username> <new_password>\n"
        "  - Admin authorized_keys: C:\\ProgramData\\ssh\\administrators_authorized_keys\n"
        "  - Config file: C:\\ProgramData\\ssh\\sshd_config"
    ),
    # ── Connection info ──────────────────────────────────────────
    "msg.conn_info_header": "SSH Connection Information",
    "msg.conn_info_os": "OS Version : {version}",
    "msg.conn_info_user": "Username   : {user}",
    "msg.conn_info_host": "Hostname   : {host}",
    "msg.conn_info_ip": "IP Address : {ip}",
    "msg.conn_info_port": "Port       : {port}",
    "msg.conn_info_cmd": "SSH Command: {cmd}",
    "msg.conn_info_notes": (
        "Notes:\n"
        "  - Password: Use your current system login password.\n"
        "  - Config file: /etc/ssh/sshd_config"
    ),
    # ── Tool metadata ────────────────────────────────────────────
    "tool.device-init.description": "Set up SSH access, password, config, firewall and python alias",
    "tool.device-init.display_name": "Initialize Device",
})

register_translations("zh", {
    # ── 子菜单选项 ───────────────────────────────────────────────
    "msg.init_select": "选择初始化操作：",
    "msg.sep_ssh_service": "SSH 服务",
    "msg.sep_other": "其他",
    "msg.init_all": "完整 SSH 配置（推荐）",
    "msg.init_all_desc": "安装、配置、启用 sshd、防火墙并打印连接信息",
    "msg.init_preview": "预览配置步骤",
    "msg.init_preview_desc": "查看完整配置将执行的操作（不做任何更改）",
    "msg.init_preview_header": "[预览] 完整 SSH 配置将执行：",
    "msg.init_preview_files": "涉及文件：/etc/ssh/sshd_config、防火墙规则",
    "msg.init_connection_info": "仅打印连接信息",
    "msg.init_connection_info_desc": "显示 SSH 连接详情（用户、IP、端口）",
    "msg.init_install_ssh": "安装 SSH 服务器",
    "msg.init_install_ssh_desc": "安装 OpenSSH Server 软件包",
    "msg.init_start_ssh": "启动 SSH 服务",
    "msg.init_start_ssh_desc": "立即启动 sshd 服务",
    "msg.init_enable_ssh": "设置 SSH 开机自启",
    "msg.init_enable_ssh_desc": "将 sshd 服务设为开机自动启动",
    "msg.init_set_password": "设置用户密码",
    "msg.init_set_password_desc": "设置或更新当前用户的密码",
    "msg.init_config_sshd": "配置 sshd",
    "msg.init_config_sshd_desc": "Linux：启用密码认证 | Windows：设置默认 Shell 为 PowerShell",
    "msg.init_open_firewall": "开放防火墙 SSH 端口",
    "msg.init_open_firewall_desc": "允许 SSH 端口 22 通过防火墙",
    "msg.init_python_alias": "创建 Python 别名",
    "msg.init_python_alias_desc": "创建 python -> python3 符号链接（仅 Linux）",
    # ── 步骤消息（共享）────────────────────────────────────────
    "msg.checking_sshd_config": "正在检查 sshd 配置...",
    "msg.confirm_password": "确认密码：",
    "msg.enter_password": "输入新密码：",
    "msg.firewall_allow_ssh": "是否允许 SSH 通过防火墙？",
    "msg.firewall_detected": "检测到防火墙：{fw}",
    "msg.firewall_no_active": "未检测到活动的防火墙，跳过。",
    "msg.firewall_rule_added": "防火墙规则已添加：允许 SSH（端口 22）。",
    "msg.password_already_set": "用户 '{user}' 已设置密码。",
    "msg.password_auth_already": "PasswordAuthentication 已经启用。",
    "msg.password_auth_enabled": "已在 sshd_config 中启用 PasswordAuthentication。",
    "msg.password_mismatch": "密码不匹配，跳过。",
    "msg.password_not_set": "用户 '{user}' 未设置密码。",
    "msg.password_set_failed": "密码设置失败。",
    "msg.password_set_success": "用户 '{user}' 的密码已设置。",
    "msg.python3_not_found": "未找到 python3，跳过别名设置。",
    "msg.python_alias_created": "已在 {path} 中创建别名 python=python3",
    "msg.python_already_exists": "\"python\" 命令已存在，跳过。",
    "msg.service_already_enabled": "服务 {service} 已是开机自启状态。",
    "msg.service_already_running": "服务 {service} 已在运行。",
    "msg.service_enable_failed": "启用服务 {service} 开机自启失败。",
    "msg.service_enabled": "服务 {service} 已设为开机自启。",
    "msg.service_start_failed": "启动服务 {service} 失败。",
    "msg.service_started": "服务 {service} 已启动。",
    "msg.sshd_config_backup": "备份已保存至 {path}",
    "msg.sshd_restarted": "sshd 服务已重启。",
    "msg.step_firewall": "正在检查防火墙...",
    # ── Windows 专用消息 ─────────────────────────────────────────
    "msg.win_checking_openssh": "正在检查 OpenSSH Server 安装状态...",
    "msg.win_openssh_installed": "OpenSSH Server 已安装。",
    "msg.win_installing_openssh": "正在安装 OpenSSH Server（可能需要几分钟）...",
    "msg.win_openssh_install_success": "OpenSSH Server 安装成功。",
    "msg.win_starting_sshd": "正在启动 sshd 服务...",
    "msg.win_sshd_status": "sshd 服务状态：{status}",
    "msg.win_enabling_sshd": "正在设置 sshd 开机自启...",
    "msg.win_sshd_auto_enabled": "sshd 服务已设为自动启动。",
    "msg.win_password_note": "密码由 Windows 管理。使用 'net user <用户名> <新密码>' 重置。",
    "msg.win_password_hint": "当前用户：{user}。SSH 登录密码即 Windows 登录密码。",
    "msg.win_config_sshd_shell": "正在设置 SSH 默认 Shell 为 PowerShell...",
    "msg.win_shell_already_set": "默认 Shell 已经是 PowerShell。",
    "msg.win_shell_set_success": "SSH 默认 Shell 已切换为 PowerShell。",
    "msg.win_shell_set_failed": "注册表设置默认 Shell 失败。",
    "msg.win_checking_firewall": "正在检查防火墙规则...",
    "msg.win_firewall_exists": "sshd 防火墙规则已存在。",
    "msg.win_firewall_success": "已创建防火墙入站规则：TCP/22。",
    "msg.win_firewall_failed": "创建防火墙规则失败。",
    "msg.win_python_alias_skip": "Windows 上不需要 python 别名，跳过。",
    "msg.win_ps_failed": "PowerShell 命令失败：{cmd}... | {err}",
    "msg.win_conn_info_notes": (
        "说明：\n"
        "  - 密码：使用当前 Windows 登录密码。\n"
        "  - 微软账户：用户名可能是邮箱前缀，运行 'whoami' 确认。\n"
        "  - 重置密码：net user <用户名> <新密码>\n"
        "  - 管理员密钥路径：C:\\ProgramData\\ssh\\administrators_authorized_keys\n"
        "  - 配置文件：C:\\ProgramData\\ssh\\sshd_config"
    ),
    # ── 连接信息 ─────────────────────────────────────────────────
    "msg.conn_info_header": "SSH 连接信息",
    "msg.conn_info_os": "系统版本 : {version}",
    "msg.conn_info_user": "用户名   : {user}",
    "msg.conn_info_host": "主机名   : {host}",
    "msg.conn_info_ip": "IP 地址  : {ip}",
    "msg.conn_info_port": "端口     : {port}",
    "msg.conn_info_cmd": "SSH 命令 : {cmd}",
    "msg.conn_info_notes": (
        "说明：\n"
        "  - 密码：使用当前系统登录密码。\n"
        "  - 配置文件：/etc/ssh/sshd_config"
    ),
    # ── 工具元数据 ───────────────────────────────────────────────
    "tool.device-init.description": "配置 SSH 访问、密码、配置、防火墙和 Python 别名",
    "tool.device-init.display_name": "初始化设备",
})
