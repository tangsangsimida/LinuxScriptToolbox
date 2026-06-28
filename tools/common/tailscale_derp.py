"""Tailscale DERP relay service one-click deployment module.

Tailscale DERP 中继服务一键部署模块。

Deploys a DERP relay server on a public Linux server using Docker Compose
(primary) or systemd + official binary (fallback). Optionally deploys a
Headscale control server for fully self-hosted Tailscale networks.

在公网 Linux 服务器上部署 DERP 中继服务，优先使用 Docker Compose，
备选 systemd + 官方二进制文件。可选部署 Headscale 控制服务器，
实现完全自托管的 Tailscale 网络。
"""

from pathlib import Path

from tools.base import Tool
from . import tailscale_derp_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_cmd, run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.platform import command_exists
from utils.sudo_utils import write_file as sudo_write_file
from utils.ui import (
    ask,
    print_success,
    print_error,
    print_info,
    print_warning,
    confirm,
    prompt_selection,
    console,
    BACK_ACTION,
)

# ── Constants ────────────────────────────────────────────────────

# Base directory for DERP deployment files / DERP 部署文件的基础目录
DERP_BASE_DIR = Path("/opt/tailscale-derp")

# DERP configuration file path / DERP 配置文件路径
DERP_CONFIG_DIR = DERP_BASE_DIR / "config"
DERP_YAML_PATH = DERP_CONFIG_DIR / "derp.yaml"

# Docker Compose file path / Docker Compose 文件路径
COMPOSE_FILE_PATH = DERP_BASE_DIR / "docker-compose.yml"

# Headscale data directory / Headscale 数据目录
HEADSCALE_DATA_DIR = DERP_BASE_DIR / "headscale"

# Systemd service name for binary fallback / 二进制回退方案的 systemd 服务名
DERP_SERVICE_NAME = "tailscale-derp"
HEADSCALE_SERVICE_NAME = "headscale"

# Required ports / 所需端口
DERP_PORTS = [
    ("80", "tcp", "HTTP / ACME challenge"),
    ("443", "tcp", "HTTPS / DERP"),
    ("3478", "udp", "STUN"),
]

# DERP is now part of the tailscale package — install via package manager
# DERP 现在是 tailscale 包的一部分 — 通过包管理器安装
# The derper binary is at /usr/sbin/derper after installing tailscale
# 安装 tailscale 后 derper 二进制文件位于 /usr/sbin/derper
DERP_SYSTEM_BINARY = "/usr/sbin/derper"

# Headscale latest release URL / Headscale 最新版本 URL
HEADSCALE_BINARY_URL = "https://github.com/juanfont/headscale/releases/latest/download/headscale_linux_amd64"

# ── Menu options ─────────────────────────────────────────────────

# Submenu options for the DERP tool / DERP 工具的子菜单选项
DERP_MENU_OPTIONS = [
    {
        "id": "deploy-derp",
        "name_key": "msg.derp_menu_deploy",
        "desc_key": "msg.derp_menu_deploy_desc",
    },
    {
        "id": "deploy-headscale",
        "name_key": "msg.derp_menu_headscale",
        "desc_key": "msg.derp_menu_headscale_desc",
    },
    {
        "id": "manage",
        "name_key": "msg.derp_menu_manage",
        "desc_key": "msg.derp_menu_manage_desc",
    },
    {
        "id": "status",
        "name_key": "msg.derp_menu_status",
        "desc_key": "msg.derp_menu_status_desc",
    },
    {
        "id": "cleanup",
        "name_key": "msg.derp_menu_cleanup",
        "desc_key": "msg.derp_menu_cleanup_desc",
    },
]


# ── Helper functions ─────────────────────────────────────────────


# Create a directory using sudo (needed for /opt/ paths).
#
# 使用 sudo 创建目录（/opt/ 路径需要 root 权限）。
#
# Args:
#     path: Directory path to create. / 要创建的目录路径。
#
# Returns:
#     True if directory was created or already exists. / 目录创建成功或已存在返回 True。
def _sudo_mkdir(path: Path) -> bool:
    code = run_verbose(["sudo", "mkdir", "-p", str(path)])
    return code == 0


# Check if a file exists using sudo (needed for /opt/ paths).
#
# 使用 sudo 检查文件是否存在（/opt/ 路径需要 root 权限）。
#
# Args:
#     path: File path to check. / 要检查的文件路径。
#
# Returns:
#     True if file exists. / 文件存在返回 True。
def _sudo_exists(path: Path) -> bool:
    code, _ = run_cmd(["sudo", "test", "-e", str(path)])
    return code == 0


# Write a file using sudo, avoiding stdin password leak with sudo tee.
#
# 使用 sudo 写入文件，避免 sudo tee 的 stdin 密码泄漏问题。
#
# Writes to a temp file first, then moves to the target path with sudo.
# This avoids the issue where LST_SUDO_PASSWORD gets written into the file
# when using sudo tee with stdin.
#
# 先写入临时文件，再用 sudo 移动到目标路径。
# 避免使用 sudo tee 时 LST_SUDO_PASSWORD 被写入文件的问题。

# Check if a string is an IP address (IPv4 or IPv6).
#
# 检查字符串是否为 IP 地址（IPv4 或 IPv6）。
#
# Args:
#     value: String to check. / 要检查的字符串。
#
# Returns:
#     True if the string is an IP address. / 是 IP 地址返回 True。
def _is_ip_address(value: str) -> bool:
    import ipaddress
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


# Generate a self-signed TLS certificate for an IP address.
#
# 为 IP 地址生成自签名 TLS 证书。
#
# Args:
#     ip_address: The IP address to generate the cert for. / 要生成证书的 IP 地址。
#
# Returns:
#     Tuple of (certfile_path, keyfile_path) or None on failure.
#     返回 (证书路径, 密钥路径) 元组，失败返回 None。
def _generate_self_signed_cert(hostname: str) -> tuple[str, str] | None:
    certdir = DERP_BASE_DIR / "certs"
    # derper expects {certdir}/{hostname}.crt and {hostname}.key /
    # derper 期望 {certdir}/{hostname}.crt 和 {hostname}.key
    certfile = certdir / f"{hostname}.crt"
    keyfile = certdir / f"{hostname}.key"

    # Check if certs already exist (idempotent) / 检查证书是否已存在（幂等）
    if _sudo_exists(certfile) and _sudo_exists(keyfile):
        print_info(t("msg.derp_selfsigned_exists"))
        return str(certfile), str(keyfile)

    _sudo_mkdir(certdir)

    print_info(t("msg.derp_selfsigned_generating", ip=hostname))

    # Generate self-signed cert with SAN for the IP /
    # 生成包含 IP SAN 的自签名证书
    code = run_verbose([
        "sudo", "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-nodes",
        "-keyout", str(keyfile),
        "-out", str(certfile),
        "-days", "3650",
        "-subj", f"/CN={hostname}",
        "-addext", f"subjectAltName=IP:{hostname}",
    ])
    if code != 0:
        print_error(t("msg.derp_selfsigned_failed"))
        return None

    # Set permissions / 设置权限
    run_verbose(["sudo", "chmod", "600", str(keyfile)])
    run_verbose(["sudo", "chmod", "644", str(certfile)])

    print_success(t("msg.derp_selfsigned_generated"))
    return str(certfile), str(keyfile)


# Check if a network port is currently in use.
#
# 检查网络端口是否被占用。
#
# Args:
#     port: Port number to check. / 要检查的端口号。
#     proto: Protocol ("tcp" or "udp"). / 协议（"tcp" 或 "udp"）。
#
# Returns:
#     True if the port is in use, False otherwise. / 端口被占用返回 True，否则返回 False。
def _is_port_in_use(port: str, proto: str = "tcp") -> bool:
    cmd = ["ss", "-tlnp"] if proto == "tcp" else ["ss", "-ulnp"]
    code, out = run_cmd(cmd)
    return code == 0 and f":{port} " in out


# Check if Docker and Docker Compose are available.
#
# 检查 Docker 和 Docker Compose 是否可用。
#
# Returns:
#     Tuple of (docker_available, compose_available). / 返回 (docker 可用, compose 可用) 元组。
_docker_check_cache: tuple[bool, bool] | None = None


def _check_docker() -> tuple[bool, bool]:
    """Check Docker and Docker Compose availability (cached per run).

    检查 Docker 和 Docker Compose 可用性（每次运行缓存）。
    """
    global _docker_check_cache
    if _docker_check_cache is not None:
        return _docker_check_cache
    docker_ok = command_exists("docker")
    compose_ok = False
    if docker_ok:
        # Docker Compose v2 plugin / Docker Compose v2 插件
        code, _ = run_cmd(["docker", "compose", "version"])
        compose_ok = code == 0
        if not compose_ok:
            # Standalone docker-compose / 独立的 docker-compose
            compose_ok = command_exists("docker-compose")
    _docker_check_cache = (docker_ok, compose_ok)
    return _docker_check_cache


# Collect DERP configuration from user input.
#
# 从用户输入收集 DERP 配置信息。
#
# Returns:
#     Dict with 'hostname', 'stun_port', and optional 'tailscale_authkey',
#     or None if user cancelled. / 返回包含配置的字典，用户取消返回 None。
def _collect_derp_config() -> dict | None:
    print_info(t("msg.derp_config_intro"))
    console.print()

    # Get hostname (domain or IP) / 获取主机名（域名或 IP）
    hostname_input = ask(t("msg.derp_ask_hostname"))
    if not hostname_input:
        print_error(t("msg.derp_hostname_required"))
        return None

    hostname_input = hostname_input.strip()

    # Get STUN port (default 3478) / 获取 STUN 端口（默认 3478）
    stun_port = ask(t("msg.derp_ask_stun_port"), default="3478")

    # Optional Tailscale auth key for mesh / 可选的 Tailscale 认证密钥用于 mesh
    console.print()
    print_info(t("msg.derp_authkey_hint"))
    authkey = ask(t("msg.derp_ask_authkey"), default="")

    # Auto-detect cert mode based on hostname type and port 80 availability /
    # 根据主机名类型和端口 80 可用性自动检测证书模式
    is_ip = _is_ip_address(hostname_input)
    if is_ip:
        # IP address → use self-signed certificates / IP 地址 → 使用自签名证书
        print_info(t("msg.derp_ip_selfsigned"))
        certmode = "selfsigned"
    elif _is_port_in_use("80", "tcp"):
        # Domain + port 80 occupied → certbot with nginx webroot /
        # 域名 + 端口 80 被占用 → certbot nginx webroot 模式
        print_info(t("msg.derp_port80_used_certbot"))
        certmode = "certbot"
    else:
        # Domain + port 80 free → built-in Let's Encrypt /
        # 域名 + 端口 80 空闲 → 内置 Let's Encrypt
        certmode = "letsencrypt"

    return {
        "hostname": hostname_input,
        "stun_port": stun_port.strip(),
        "tailscale_authkey": authkey.strip() if authkey.strip() else None,
        "certmode": certmode,
    }


# Generate DERP configuration YAML content.
#
# 生成 DERP 配置 YAML 内容。
#
# Args:
#     config: Configuration dict from _collect_derp_config(). / 配置字典。
#
# Returns:
#     YAML configuration string. / YAML 配置字符串。
def _generate_derp_yaml(config: dict) -> str:
    lines = [
        "# DERP relay configuration — auto-generated by LinuxScriptToolbox",
        "# DERP 中继配置 — 由 LinuxScriptToolbox 自动生成",
        "",
        'addr: ":443"',
        'letsencrypt: true',
        f'hostname: "{config["hostname"]}"',
        "",
        "stun:",
        f'  - addr: ":{config["stun_port"]}"',
        "",
    ]

    # If Tailscale auth key is provided, enable mesh mode /
    # 如果提供了 Tailscale 认证密钥，启用 mesh 模式
    if config.get("tailscale_authkey"):
        lines.extend([
            "tailscale_mode: \"login\"",
            f'tailscale_authkey: "{config["tailscale_authkey"]}"',
            "",
        ])

    return "\n".join(lines)


# Generate Docker Compose YAML for DERP relay.
#
# 生成 DERP 中继的 Docker Compose YAML。
#
# Args:
#     config: Configuration dict. / 配置字典。
#
# Returns:
#     Docker Compose YAML string. / Docker Compose YAML 字符串。
def _generate_compose_yaml(config: dict) -> str:
    authkey_env = ""
    if config.get("tailscale_authkey"):
        authkey_env = f'      - TS_AUTHKEY={config["tailscale_authkey"]}'
    else:
        authkey_env = "      # Uncomment and set to enable mesh: TS_AUTHKEY=tskey-auth-..."

    return f"""# Docker Compose for DERP relay — auto-generated by LinuxScriptToolbox
# DERP 中继的 Docker Compose 配置 — 由 LinuxScriptToolbox 自动生成

services:
  derp:
    image: tailscale/derp:latest
    container_name: tailscale-derp
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config/derp.yaml:/etc/derper/derp.yaml:ro
      - derp-state:/var/lib/tailscale
    environment:
{authkey_env}
      - DERP_CONFIG=/etc/derper/derp.yaml
    cap_add:
      - NET_ADMIN
      - SYS_MODULE

volumes:
  derp-state:
"""


# Generate systemd unit file for standalone DERP binary.
#
# 为独立 DERP 二进制文件生成 systemd 服务单元文件。
#
# Args:
#     config: Configuration dict. / 配置字典。
#     binary_path: Path to the derper binary. / derper 二进制文件路径。
#
# Returns:
#     Systemd unit file content string. / systemd 服务单元文件内容。
def _generate_systemd_unit(config: dict, binary_path: str) -> str:
    mesh_flag = ""
    if config.get("tailscale_authkey"):
        mesh_flag = " --mesh-with-logs"

    certmode = config.get("certmode", "letsencrypt")
    certdir = config.get("certdir", "/opt/tailscale-derp/certs")

    if certmode == "manual":
        # Use pre-existing certificates — derper looks for {certdir}/{hostname}.crt and .key /
        # 使用已有证书 — derper 在 certdir 中查找 {hostname}.crt 和 .key
        # -http-port -1 disables HTTP listener (not needed for manual certs) /
        # -http-port -1 禁用 HTTP 监听（manual 证书模式不需要）
        cert_flags = f"-certmode manual -certdir {certdir} -http-port -1"
    else:
        # Let's Encrypt with built-in ACME client / 使用内置 ACME 客户端的 Let's Encrypt
        cert_flags = f"-certmode letsencrypt -certdir {certdir}"

    return f"""[Unit]
Description=Tailscale DERP Relay Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={binary_path} -hostname {config["hostname"]} -a :443 -stun-port {config["stun_port"]} {cert_flags}{mesh_flag}
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""


# Generate systemd unit file for Headscale.
#
# 为 Headscale 生成 systemd 服务单元文件。
#
# Args:
#     binary_path: Path to the headscale binary. / headscale 二进制文件路径。
#
# Returns:
#     Systemd unit file content string. / systemd 服务单元文件内容。
def _generate_headscale_systemd_unit(binary_path: str) -> str:
    return f"""[Unit]
Description=Headscale Control Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={binary_path} serve
WorkingDirectory={HEADSCALE_DATA_DIR}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


# Check all prerequisites for DERP deployment.
#
# 检查 DERP 部署的所有先决条件。
#
# Returns:
#     True if all prerequisites are met, False otherwise. / 所有先决条件满足返回 True，否则返回 False。
def _check_prerequisites() -> bool:
    print_info(t("msg.derp_checking_prereqs"))
    console.print()

    all_ok = True

    # Check domain resolution / 检查域名解析
    print_info(t("msg.derp_check_dns"))

    # Check required ports / 检查所需端口
    for port, proto, desc in DERP_PORTS:
        if _is_port_in_use(port, proto):
            print_warning(t("msg.derp_port_in_use", port=port, proto=proto, desc=desc))
            all_ok = False
        else:
            print_success(t("msg.derp_port_free", port=port, proto=proto, desc=desc))

    # Check Docker / 检查 Docker
    docker_ok, compose_ok = _check_docker()
    if docker_ok and compose_ok:
        print_success(t("msg.derp_docker_ok"))
    elif docker_ok and not compose_ok:
        print_warning(t("msg.derp_compose_missing"))
    else:
        print_warning(t("msg.derp_docker_missing"))

    console.print()
    return all_ok


# Acquire TLS certificate using certbot with nginx webroot mode.
#
# 使用 certbot 的 nginx webroot 模式获取 TLS 证书。
#
# This is used when port 80 is already occupied by nginx — certbot
# places challenge files in nginx's webroot, and nginx serves them
# on port 80 for ACME validation.
#
# 当端口 80 已被 nginx 占用时使用此方式 — certbot 将验证文件放在
# nginx 的 webroot 目录中，nginx 在端口 80 上提供这些文件完成 ACME 验证。
#
# Args:
#     hostname: Domain name for the certificate. / 证书的域名。
#
# Returns:
#     Tuple of (certfile_path, keyfile_path) or None on failure.
#     返回 (证书路径, 密钥路径) 元组，失败返回 None。
def _acquire_certbot_cert(hostname: str) -> tuple[str, str] | None:
    # Check if certbot is available / 检查 certbot 是否可用
    if not command_exists("certbot"):
        print_info(t("msg.derp_installing_certbot"))
        from utils.platform_services import package_install
        distro = detect_distro()
        code = package_install("certbot", distro)
        if code != 0:
            print_error(t("msg.derp_certbot_install_failed"))
            return None

    # Detect nginx webroot / 检测 nginx webroot
    webroot = "/var/www/html"
    # Try to find the actual webroot from nginx config /
    # 尝试从 nginx 配置中找到实际的 webroot
    code, out = run_cmd(["sudo", "grep", "-r", "root", "/etc/nginx/sites-enabled/",
                         "/etc/nginx/conf.d/"])
    if code == 0 and out:
        for line in out.splitlines():
            if "root" in line and "#" not in line.split("root")[0]:
                parts = line.strip().split()
                for i, p in enumerate(parts):
                    if p == "root" and i + 1 < len(parts):
                        candidate = parts[i + 1].rstrip(";")
                        if candidate.startswith("/"):
                            webroot = candidate
                            break

    print_info(t("msg.derp_certbot_webroot", webroot=webroot))

    # Run certbot in webroot mode / 以 webroot 模式运行 certbot
    print_info(t("msg.derp_certbot_running", hostname=hostname))
    code = run_verbose([
        "sudo", "certbot", "certonly", "--webroot",
        "-w", webroot,
        "-d", hostname,
        "--non-interactive", "--agree-tos",
        "--register-unsafely-without-email",
    ])
    if code != 0:
        print_error(t("msg.derp_certbot_failed"))
        return None

    certfile = f"/etc/letsencrypt/live/{hostname}/fullchain.pem"
    keyfile = f"/etc/letsencrypt/live/{hostname}/privkey.pem"

    # Verify certificates exist / 验证证书存在
    code1, _ = run_cmd(["sudo", "test", "-f", certfile])
    code2, _ = run_cmd(["sudo", "test", "-f", keyfile])
    if code1 != 0 or code2 != 0:
        print_error(t("msg.derp_cert_not_found"))
        return None

    print_success(t("msg.derp_cert_acquired", hostname=hostname))
    return certfile, keyfile


# Install the tailscale package which includes the derper binary.
#
# 安装包含 derper 二进制文件的 tailscale 包。
#
# Args:
#     distro: Distribution identifier. / 发行版标识符。
#
# Returns:
#     True if installation succeeded, False otherwise. / 安装成功返回 True，否则返回 False。
def _install_tailscale(distro: str) -> bool:
    # Check if derper is already available / 检查 derper 是否已可用
    code, _ = run_cmd(["sudo", "test", "-x", DERP_SYSTEM_BINARY])
    if code == 0:
        print_info(t("msg.derp_tailscale_installed"))
        return True

    print_info(t("msg.derp_installing_tailscale"))

    # Debian/Ubuntu: need to add Tailscale apt repo first /
    # Debian/Ubuntu：需要先添加 Tailscale apt 仓库
    if distro in ("debian", "ubuntu"):
        from utils.sudo_utils import write_file as sudo_write_file
        run_verbose(["curl", "-fsSL", "https://pkgs.tailscale.com/stable/debian/bookworm.noarmor.gpg",
                     "-o", "/tmp/tailscale-key.gpg"])
        run_verbose(["sudo", "mv", "/tmp/tailscale-key.gpg",
                     "/usr/share/keyrings/tailscale-archive-keyring.gpg"])
        sudo_write_file(
            "/etc/apt/sources.list.d/tailscale.list",
            "deb [signed-by=/usr/share/keyrings/tailscale-archive-keyring.gpg] "
            "https://pkgs.tailscale.com/stable/debian bookworm main\n",
        )
        run_verbose(["sudo", "apt-get", "update", "-qq"])

    # Install via platform_services (handles arch/debian/fedora/suse)
    # 通过 platform_services 安装（处理 arch/debian/fedora/suse）
    from utils.platform_services import package_install
    code = package_install("tailscale", distro)
    if code != 0:
        print_error(t("msg.derp_tailscale_install_failed"))
        return False

    # Verify derper is now available / 验证 derper 现在可用
    code, _ = run_cmd(["sudo", "test", "-x", DERP_SYSTEM_BINARY])
    if code != 0:
        print_error(t("msg.derp_derper_not_found"))
        return False

    print_success(t("msg.derp_tailscale_install_success"))
    return True


# Download the Headscale binary from GitHub releases.
#
# 从 GitHub releases 下载 Headscale 二进制文件。
#
# Args:
#     target_path: Where to save the binary. / 二进制文件保存路径。
#
# Returns:
#     True if download succeeded, False otherwise. / 下载成功返回 True，否则返回 False。
def _download_headscale_binary(target_path: Path) -> bool:
    print_info(t("msg.derp_downloading_headscale", url=HEADSCALE_BINARY_URL))

    # Download to temp location first, then sudo move to /opt/ /
    # 先下载到临时位置，再用 sudo 移动到 /opt/
    tmp_path = Path("/tmp/headscale")
    code = run_verbose([
        "curl", "-fsSL", "-o", str(tmp_path), HEADSCALE_BINARY_URL,
    ])
    if code != 0:
        print_error(t("msg.derp_headscale_download_failed"))
        return False

    run_verbose(["sudo", "mv", str(tmp_path), str(target_path)])
    run_verbose(["sudo", "chmod", "755", str(target_path)])
    print_success(t("msg.derp_binary_saved", path=str(target_path)))
    return True


# ── DERP deployment (Docker Compose path) ────────────────────────


# Deploy DERP relay using Docker Compose.
#
# 使用 Docker Compose 部署 DERP 中继。
#
# Args:
#     config: Configuration dict from _collect_derp_config(). / 配置字典。
#
# Returns:
#     True if deployment succeeded, False otherwise. / 部署成功返回 True，否则返回 False。
def _deploy_derp_docker(config: dict) -> bool:
    print_info(t("msg.derp_deploy_docker"))
    console.print()

    # Create directory structure / 创建目录结构
    _sudo_mkdir(DERP_CONFIG_DIR)

    # Generate and write DERP config / 生成并写入 DERP 配置
    derp_yaml = _generate_derp_yaml(config)
    sudo_write_file(str(DERP_YAML_PATH), derp_yaml)
    print_success(t("msg.derp_config_written", path=str(DERP_YAML_PATH)))

    # Generate and write Docker Compose file / 生成并写入 Docker Compose 文件
    compose_yaml = _generate_compose_yaml(config)
    sudo_write_file(str(COMPOSE_FILE_PATH), compose_yaml)
    print_success(t("msg.derp_compose_written", path=str(COMPOSE_FILE_PATH)))

    # Pull latest image / 拉取最新镜像
    print_info(t("msg.derp_pull_image"))
    code = run_verbose(["docker", "compose", "-f", str(COMPOSE_FILE_PATH), "pull"])
    if code != 0:
        print_error(t("msg.derp_pull_failed"))
        return False

    # Start services / 启动服务
    print_info(t("msg.derp_starting"))
    code = run_verbose(["docker", "compose", "-f", str(COMPOSE_FILE_PATH), "up", "-d"])
    if code != 0:
        print_error(t("msg.derp_start_failed"))
        return False

    print_success(t("msg.derp_deploy_success"))
    console.print()
    print_info(t("msg.derp_verify_hint", hostname=config["hostname"]))
    return True


# ── DERP deployment (systemd binary fallback) ────────────────────


# Deploy DERP relay using systemd and the official binary.
#
# 使用 systemd 和官方二进制文件部署 DERP 中继。
#
# Args:
#     config: Configuration dict from _collect_derp_config(). / 配置字典。
#
# Returns:
#     True if deployment succeeded, False otherwise. / 部署成功返回 True，否则返回 False。
def _deploy_derp_systemd(config: dict) -> bool:
    print_info(t("msg.derp_deploy_systemd"))
    console.print()

    # Create directory structure / 创建目录结构
    _sudo_mkdir(DERP_CONFIG_DIR)
    _sudo_mkdir(DERP_BASE_DIR / "certs")

    # Install tailscale package (includes derper) /
    # 安装 tailscale 包（包含 derper）
    distro = detect_distro()
    if not _install_tailscale(distro):
        return False

    # Handle certificate acquisition based on certmode /
    # 根据证书模式获取证书
    if config.get("certmode") == "certbot":
        # Port 80 is occupied — use certbot with nginx webroot /
        # 端口 80 被占用 — 使用 certbot 的 nginx webroot 模式
        cert_result = _acquire_certbot_cert(config["hostname"])
        if cert_result is None:
            return False
        src_certfile, src_keyfile = cert_result
        # Copy certs to certdir with derper's expected naming ({hostname}.crt/.key) /
        # 将证书复制到 certdir 并使用 derper 期望的命名格式
        certdir = str(DERP_BASE_DIR / "certs")
        dst_certfile = f"{certdir}/{config['hostname']}.crt"
        dst_keyfile = f"{certdir}/{config['hostname']}.key"
        run_verbose(["sudo", "cp", src_certfile, dst_certfile])
        run_verbose(["sudo", "cp", src_keyfile, dst_keyfile])
        run_verbose(["sudo", "chmod", "600", dst_keyfile])
        config["certmode"] = "manual"
        config["certdir"] = certdir
    elif config.get("certmode") == "selfsigned":
        # IP address — generate self-signed certificate /
        # IP 地址 — 生成自签名证书
        cert_result = _generate_self_signed_cert(config["hostname"])
        if cert_result is None:
            return False
        config["certmode"] = "manual"
        config["certdir"] = str(DERP_BASE_DIR / "certs")

    # Generate systemd unit / 生成 systemd 服务单元
    unit_content = _generate_systemd_unit(config, DERP_SYSTEM_BINARY)
    unit_path = Path(f"/etc/systemd/system/{DERP_SERVICE_NAME}.service")
    sudo_write_file(str(unit_path), unit_content)
    print_success(t("msg.derp_systemd_written", path=str(unit_path)))

    # Reload and start / 重新加载并启动
    run_verbose(["sudo", "systemctl", "daemon-reload"])
    run_verbose(["sudo", "systemctl", "enable", DERP_SERVICE_NAME])
    code = run_verbose(["sudo", "systemctl", "start", DERP_SERVICE_NAME])
    if code != 0:
        print_error(t("msg.derp_start_failed"))
        return False

    print_success(t("msg.derp_deploy_success"))
    console.print()
    print_info(t("msg.derp_verify_hint", hostname=config["hostname"]))
    return True


# ── Headscale deployment ─────────────────────────────────────────


# Generate Headscale configuration YAML.
#
# 生成 Headscale 配置 YAML。
#
# Args:
#     server_url: The public URL for the Headscale server. / Headscale 服务器的公网 URL。
#
# Returns:
#     Headscale config YAML string. / Headscale 配置 YAML 字符串。
def _generate_headscale_config(server_url: str) -> str:
    return f"""# Headscale configuration — auto-generated by LinuxScriptToolbox
# Headscale 配置 — 由 LinuxScriptToolbox 自动生成

server_url: {server_url}
listen_addr: 0.0.0.0:8080
metrics_listen_addr: 127.0.0.1:9090

db_type: sqlite3
db_path: {HEADSCALE_DATA_DIR}/db.sqlite

log_level: info

private_key_path: {HEADSCALE_DATA_DIR}/private.key
noise:
  private_key_path: {HEADSCALE_DATA_DIR}/noise_private.key

derp:
  urls:
    - https://controlplane.tailscale.com/derpmap/default
  server:
    enabled: false
  auto_update_enabled: true
  update_frequency: 24h

dns_config:
  magic_dns: true
  base_domain: headscale.local
  nameservers:
    - 1.1.1.1
    - 8.8.8.8
"""


# Deploy Headscale control server using Docker Compose.
#
# 使用 Docker Compose 部署 Headscale 控制服务器。
#
# Returns:
#     True if deployment succeeded, False otherwise. / 部署成功返回 True，否则返回 False。
def _deploy_headscale_docker() -> bool:
    headscale_compose = HEADSCALE_DATA_DIR / "docker-compose.yml"

    compose_yaml = """# Headscale Docker Compose — auto-generated by LinuxScriptToolbox
# Headscale Docker Compose 配置 — 由 LinuxScriptToolbox 自动生成

services:
  headscale:
    image: headscale/headscale:latest
    container_name: headscale
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./config:/etc/headscale
      - ./data:/var/lib/headscale
    command: serve

volumes:
  headscale-data:
"""

    _sudo_mkdir(HEADSCALE_DATA_DIR)
    _sudo_mkdir(HEADSCALE_DATA_DIR / "config")
    _sudo_mkdir(HEADSCALE_DATA_DIR / "data")

    sudo_write_file(str(headscale_compose), compose_yaml)
    print_success(t("msg.derp_headscale_compose_written", path=str(headscale_compose)))

    # Generate headscale config / 生成 headscale 配置
    console.print()
    print_info(t("msg.derp_headscale_url_hint"))
    url_input = ask(t("msg.derp_headscale_ask_url"), default="http://localhost:8080")

    config_content = _generate_headscale_config(url_input.strip())
    config_path = HEADSCALE_DATA_DIR / "config" / "config.yaml"
    sudo_write_file(str(config_path), config_content)
    print_success(t("msg.derp_headscale_config_written", path=str(config_path)))

    # Pull and start / 拉取并启动
    print_info(t("msg.derp_pull_headscale"))
    code = run_verbose(["docker", "compose", "-f", str(headscale_compose), "pull"])
    if code != 0:
        print_error(t("msg.derp_pull_failed"))
        return False

    code = run_verbose(["docker", "compose", "-f", str(headscale_compose), "up", "-d"])
    if code != 0:
        print_error(t("msg.derp_start_failed"))
        return False

    print_success(t("msg.derp_headscale_deploy_success"))
    console.print()

    # Create initial API key / 创建初始 API 密钥
    print_info(t("msg.derp_headscale_creating_key"))
    run_verbose([
        "docker", "exec", "headscale",
        "headscale", "users", "create", "admin",
    ])

    print_info(t("msg.derp_headscale_key_hint"))
    return True


# Deploy Headscale using systemd and binary.
#
# 使用 systemd 和二进制文件部署 Headscale。
#
# Returns:
#     True if deployment succeeded, False otherwise. / 部署成功返回 True，否则返回 False。
def _deploy_headscale_systemd() -> bool:
    binary_path = DERP_BASE_DIR / "headscale"
    if not _sudo_exists(binary_path):
        if not _download_headscale_binary(binary_path):
            return False

    _sudo_mkdir(HEADSCALE_DATA_DIR)

    # Generate config / 生成配置
    console.print()
    print_info(t("msg.derp_headscale_url_hint"))
    url_input = ask(t("msg.derp_headscale_ask_url"), default="http://localhost:8080")

    config_content = _generate_headscale_config(url_input.strip())
    config_path = HEADSCALE_DATA_DIR / "config.yaml"
    _sudo_mkdir(HEADSCALE_DATA_DIR)
    sudo_write_file(str(config_path), config_content)
    print_success(t("msg.derp_headscale_config_written", path=str(config_path)))

    # Generate systemd unit / 生成 systemd 服务单元
    unit_content = _generate_headscale_systemd_unit(str(binary_path))
    unit_path = Path(f"/etc/systemd/system/{HEADSCALE_SERVICE_NAME}.service")
    sudo_write_file(str(unit_path), unit_content)
    print_success(t("msg.derp_systemd_written", path=str(unit_path)))

    # Start service / 启动服务
    run_verbose(["sudo", "systemctl", "daemon-reload"])
    run_verbose(["sudo", "systemctl", "enable", HEADSCALE_SERVICE_NAME])
    code = run_verbose(["sudo", "systemctl", "start", HEADSCALE_SERVICE_NAME])
    if code != 0:
        print_error(t("msg.derp_start_failed"))
        return False

    print_success(t("msg.derp_headscale_deploy_success"))
    return True


# ── Service management ───────────────────────────────────────────


# Service management submenu options / 服务管理子菜单选项
MANAGE_OPTIONS = [
    {
        "id": "start",
        "name_key": "msg.derp_manage_start",
        "desc_key": "msg.derp_manage_start_desc",
    },
    {
        "id": "stop",
        "name_key": "msg.derp_manage_stop",
        "desc_key": "msg.derp_manage_stop_desc",
    },
    {
        "id": "restart",
        "name_key": "msg.derp_manage_restart",
        "desc_key": "msg.derp_manage_restart_desc",
    },
    {
        "id": "update",
        "name_key": "msg.derp_manage_update",
        "desc_key": "msg.derp_manage_update_desc",
    },
]


# Detect the active deployment method (docker or systemd).
#
# 检测当前使用的部署方式（docker 或 systemd）。
#
# Returns:
#     "docker", "systemd", or None if not deployed. / 返回 "docker"、"systemd"，未部署返回 None。
def _detect_deployment_method() -> str | None:
    # Check Docker Compose / 检查 Docker Compose
    if _sudo_exists(COMPOSE_FILE_PATH):
        code, out = run_cmd([
            "docker", "compose", "-f", str(COMPOSE_FILE_PATH), "ps", "-q",
        ])
        if code == 0 and out:
            return "docker"

    # Check systemd service / 检查 systemd 服务
    code, _ = run_cmd(["systemctl", "is-active", DERP_SERVICE_NAME])
    if code == 0:
        return "systemd"

    return None


# Manage DERP service (start/stop/restart/update).
#
# 管理 DERP 服务（启动/停止/重启/更新）。
#
# Returns:
#     True if operation succeeded, False otherwise. / 操作成功返回 True，否则返回 False。
def _manage_service() -> bool | None:
    method = _detect_deployment_method()
    if method is None:
        print_warning(t("msg.derp_not_deployed"))
        return None

    choice = prompt_selection(t("msg.derp_manage_select"), MANAGE_OPTIONS)
    if choice is None or choice == BACK_ACTION:
        return None

    _dc = ["docker", "compose", "-f", str(COMPOSE_FILE_PATH)]
    _docker_dispatch = {
        "start": lambda: run_verbose([*_dc, "up", "-d"]),
        "stop": lambda: run_verbose([*_dc, "down"]),
        "restart": lambda: run_verbose([*_dc, "restart"]),
    }
    _systemctl = ["sudo", "systemctl"]
    _systemd_dispatch = {
        "start": lambda: run_verbose([*_systemctl, "start", DERP_SERVICE_NAME]),
        "stop": lambda: run_verbose([*_systemctl, "stop", DERP_SERVICE_NAME]),
        "restart": lambda: run_verbose([*_systemctl, "restart", DERP_SERVICE_NAME]),
    }

    if method == "docker":
        if choice == "update":
            print_info(t("msg.derp_updating"))
            run_verbose([*_dc, "pull"])
            code = run_verbose([*_dc, "up", "-d"])
        elif choice in _docker_dispatch:
            code = _docker_dispatch[choice]()
        else:
            return False
    else:
        if choice == "update":
            print_info(t("msg.derp_updating_binary"))
            from utils.platform_services import package_install
            package_install("tailscale", detect_distro())
            code = run_verbose([*_systemctl, "restart", DERP_SERVICE_NAME])
        elif choice in _systemd_dispatch:
            code = _systemd_dispatch[choice]()
        else:
            return False

    if code == 0:
        print_success(t("msg.derp_manage_success", action=t(f"msg.derp_manage_{choice}")))
        return True
    else:
        print_error(t("msg.derp_manage_failed"))
        return False


# ── Status display ───────────────────────────────────────────────


# Show status of DERP and optionally Headscale services.
#
# 显示 DERP 和可选 Headscale 服务的状态。
#
# Returns:
#     True always (informational). / 始终返回 True（信息展示）。
def _show_status() -> bool:
    console.print()
    print_info(t("msg.derp_status_header"))
    console.print()

    # Check DERP deployment method / 检查 DERP 部署方式
    method = _detect_deployment_method()
    if method is None:
        print_warning(t("msg.derp_not_deployed"))
    elif method == "docker":
        print_info(t("msg.derp_status_method", method="Docker Compose"))
        run_verbose(["docker", "compose", "-f", str(COMPOSE_FILE_PATH), "ps"])
    else:
        print_info(t("msg.derp_status_method", method="systemd"))
        run_verbose(["sudo", "systemctl", "status", DERP_SERVICE_NAME, "--no-pager"])

    console.print()

    # Check Headscale / 检查 Headscale
    hs_active = False
    hs_compose = HEADSCALE_DATA_DIR / "docker-compose.yml"
    if _sudo_exists(hs_compose):
        code, out = run_cmd(["docker", "compose", "-f", str(hs_compose), "ps", "-q"])
        hs_active = code == 0 and bool(out)
    else:
        code, _ = run_cmd(["systemctl", "is-active", HEADSCALE_SERVICE_NAME])
        hs_active = code == 0

    if hs_active:
        print_success(t("msg.derp_headscale_active"))
    else:
        print_info(t("msg.derp_headscale_inactive"))

    # Show port usage / 显示端口占用
    console.print()
    print_info(t("msg.derp_status_ports"))
    for port, proto, desc in DERP_PORTS:
        in_use = _is_port_in_use(port, proto)
        status = t("msg.derp_port_status_used") if in_use else t("msg.derp_port_status_free")
        console.print(f"    {port}/{proto} ({desc}): {status}")

    return True


# ── Cleanup ──────────────────────────────────────────────────────


# Remove DERP deployment and clean up all files.
#
# 移除 DERP 部署并清理所有文件。
#
# Returns:
#     True if cleanup succeeded, None if cancelled, False on error.
#     清理成功返回 True，取消返回 None，错误返回 False。
def _cleanup() -> bool | None:
    if not confirm(t("msg.derp_cleanup_confirm")):
        return None

    # Stop Docker services / 停止 Docker 服务
    hs_compose = HEADSCALE_DATA_DIR / "docker-compose.yml"
    if _sudo_exists(hs_compose):
        print_info(t("msg.derp_stopping_headscale"))
        run_verbose(["docker", "compose", "-f", str(hs_compose), "down", "-v"])

    if _sudo_exists(COMPOSE_FILE_PATH):
        print_info(t("msg.derp_stopping_docker"))
        run_verbose(["docker", "compose", "-f", str(COMPOSE_FILE_PATH), "down", "-v"])

    # Stop systemd services / 停止 systemd 服务
    for svc in [DERP_SERVICE_NAME, HEADSCALE_SERVICE_NAME]:
        code, _ = run_cmd(["systemctl", "is-active", svc])
        if code == 0:
            run_verbose(["sudo", "systemctl", "stop", svc])
            run_verbose(["sudo", "systemctl", "disable", svc])

    # Remove systemd unit files / 移除 systemd 服务单元文件
    for svc in [DERP_SERVICE_NAME, HEADSCALE_SERVICE_NAME]:
        unit_path = Path(f"/etc/systemd/system/{svc}.service")
        if _sudo_exists(unit_path):
            run_verbose(["sudo", "rm", str(unit_path)])
            print_info(t("msg.derp_removed_unit", path=str(unit_path)))

    run_verbose(["sudo", "systemctl", "daemon-reload"])

    # Remove deployment directory / 移除部署目录
    if _sudo_exists(DERP_BASE_DIR):
        run_verbose(["sudo", "rm", "-rf", str(DERP_BASE_DIR)])
        print_success(t("msg.derp_removed_dir", path=str(DERP_BASE_DIR)))

    print_success(t("msg.derp_cleanup_success"))
    return True


# ── Tool class ───────────────────────────────────────────────────


class TailscaleDerp(Tool):
    """One-click deployment of Tailscale DERP relay and optional Headscale server.

    Tailscale DERP 中继及可选 Headscale 服务器的一键部署工具。

    Supports Docker Compose (primary) and systemd + binary (fallback) deployment
    methods. Automatically provisions Let's Encrypt TLS certificates via domain
    validation. Idempotent — safe to re-run without breaking existing config.

    支持 Docker Compose（首选）和 systemd + 二进制文件（备选）两种部署方式。
    通过域名验证自动申请 Let's Encrypt TLS 证书。幂等执行——重复运行不会破坏已有配置。

    Attributes:
        name: Unique tool identifier. / 工具唯一标识符。
        display_name: Human-readable tool name. / 人类可读的工具名称。
        description: Brief description of the tool. / 工具的简要描述。
        distros: Supported Linux distributions. / 支持的 Linux 发行版列表。
        requires_network: Whether the tool needs network access. / 工具是否需要网络访问。
        requires_sudo: Whether the tool needs sudo privileges. / 工具是否需要 sudo 权限。
    """

    name = "tailscale-derp"
    display_name = "Tailscale DERP Relay"
    description = "One-click deploy DERP relay (Docker/systemd) with optional Headscale"
    distros = ["arch", "debian", "fedora", "suse"]
    group = "env"
    requires_network = True
    requires_sudo = True

    # Deploy DERP relay service.
    #
    # 部署 DERP 中继服务。
    #
    # Checks prerequisites, collects configuration from user, then deploys
    # using Docker Compose if available, falling back to systemd + binary.
    #
    # 检查先决条件，从用户收集配置，然后使用 Docker Compose 部署（如可用），
    # 回退到 systemd + 二进制文件。
    #
    # Returns:
    #     True if deployment succeeded, False on error, None if user cancelled.
    #     部署成功返回 True，出错返回 False，用户取消返回 None。

    def _deploy_derp(self) -> bool | None:
        # Check if already deployed / 检查是否已部署
        method = _detect_deployment_method()
        if method is not None:
            print_warning(t("msg.derp_already_deployed", method=method))
            if not confirm(t("msg.derp_redeploy_confirm")):
                return None

        # Check prerequisites / 检查先决条件
        if not _check_prerequisites():
            if not confirm(t("msg.derp_prereqs_warn_continue")):
                return None

        # Collect configuration / 收集配置
        config = _collect_derp_config()
        if config is None:
            return None

        # Confirm before deployment / 部署前确认
        console.print()
        print_info(t("msg.derp_deploy_summary", hostname=config["hostname"], port=config["stun_port"]))
        if not confirm(t("msg.derp_deploy_confirm")):
            return None

        # Choose deployment method / 选择部署方式
        docker_ok, compose_ok = _check_docker()
        if docker_ok and compose_ok:
            return _deploy_derp_docker(config)
        else:
            print_info(t("msg.derp_fallback_systemd"))
            return _deploy_derp_systemd(config)

    # Deploy Headscale control server.
    #
    # 部署 Headscale 控制服务器。
    #
    # Returns:
    #     True if deployment succeeded, False on error, None if user cancelled.
    #     部署成功返回 True，出错返回 False，用户取消返回 None。

    def _deploy_headscale(self) -> bool | None:
        # Check if already running / 检查是否已在运行
        already_running = False
        hs_compose = HEADSCALE_DATA_DIR / "docker-compose.yml"
        if _sudo_exists(hs_compose):
            code, out = run_cmd(["docker", "compose", "-f", str(hs_compose), "ps", "-q"])
            already_running = code == 0 and bool(out)
        else:
            code, _ = run_cmd(["systemctl", "is-active", HEADSCALE_SERVICE_NAME])
            already_running = code == 0

        if already_running:
            print_warning(t("msg.derp_headscale_already_deployed"))
            if not confirm(t("msg.derp_headscale_redeploy_confirm")):
                return None

        if not confirm(t("msg.derp_headscale_deploy_confirm")):
            return None

        docker_ok, compose_ok = _check_docker()
        if docker_ok and compose_ok:
            return _deploy_headscale_docker()
        else:
            print_info(t("msg.derp_fallback_systemd"))
            return _deploy_headscale_systemd()

    # Main entry point: present DERP tool submenu and dispatch.
    #
    # 主入口：显示 DERP 工具子菜单并分派。
    #
    # Returns:
    #     True/False from handler, None if user cancelled.
    #     处理函数返回的 True/False，用户取消返回 None。

    def run(self) -> bool | None:
        dispatch = {
            "deploy-derp": self._deploy_derp,
            "deploy-headscale": self._deploy_headscale,
            "manage": _manage_service,
            "status": _show_status,
            "cleanup": _cleanup,
        }

        return self.run_submenu(
            DERP_MENU_OPTIONS,
            t("msg.derp_select_action"),
            dispatch,
        )
