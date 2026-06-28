# Tailscale DERP 中继部署与使用指南

**用途**: 在公网服务器上部署 DERP 中继服务，实现家里和公司设备通过 Tailscale P2P/中继互联  
**适用平台**: 服务器端 (Linux) / 客户端 (Linux + Windows)

---

## 目录

1. [架构概览](#1-架构概览)
2. [服务端部署 — DERP 中继服务器](#2-服务端部署--derp-中继服务器)
3. [客户端部署 — Linux](#3-客户端部署--linux)
4. [客户端部署 — Windows](#4-客户端部署--windows)
5. [配置 DERPMap](#5-配置-derpmap)
6. [验证连接与 SSH 互联](#6-验证连接与-ssh-互联)
7. [常见问题](#7-常见问题)

---

## 1. 架构概览

```
┌──────────────┐        ┌─────────────────────┐        ┌──────────────┐
│  家里笔记本    │        │   阿里云 DERP 中继    │        │  公司笔记本    │
│  100.x.x.1   │◄──────►│   8.137.164.32       │◄──────►│  100.x.x.2   │
│              │  STUN   │   443/tcp (HTTPS)    │  STUN   │              │
│              │◄───────►│   3478/udp (STUN)    │◄───────►│              │
└──────────────┘        └─────────────────────┘        └──────────────┘
        │                        │                        │
        └────── P2P 直连成功 ─────┘                        │
        （不走中继，零流量消耗）                              │
                                                           │
        └──────────── P2P 失败时走 DERP 中继 ───────────────┘
                     （加密转发，低流量）
```

**工作原理**:
- Tailscale 优先尝试 **P2P 直连**（通过 STUN 打洞），成功则不走中继
- P2P 失败时通过 **DERP 中继** 转发加密的 WireGuard 流量
- DERP 服务器只做加密转发，**看不到任何明文数据**
- 所有设备使用 **同一个 Tailscale 账号**，自动获得 `100.x.x.x` 内网 IP

---

## 2. 服务端部署 — DERP 中继服务器

### 2.1 前提条件

- 一台公网 Linux 服务器（阿里云/腾讯云/AWS 等）
- 开放端口: **443/tcp** (HTTPS) + **3478/udp** (STUN)
- Python 3.10+

### 2.2 一键部署

```bash
# SSH 登录服务器
ssh user@your-server-ip

# 克隆项目
git clone <repo-url> ~/LinuxScriptToolbox
cd ~/LinuxScriptToolbox

# 运行 DERP 部署工具
python main.py --tool tailscale-derp
```

### 2.3 部署流程

选择菜单 **[1] Deploy DERP Relay** 后，按提示操作：

```
1. 输入 DERP 服务器地址:
   - 域名 (如 derp.example.com) → 自动申请 Let's Encrypt 证书
   - IP 地址 (如 8.137.164.32)  → 自动生成自签名证书

2. 输入 STUN 端口: 直接回车使用默认 3478

3. 输入 Tailscale auth key: 留空回车跳过（个人使用不需要）

4. 确认部署: 输入 y
```

### 2.4 证书模式说明

| 输入类型 | 证书模式 | 需要域名 | 需要端口 80 | 说明 |
|---------|---------|---------|-----------|------|
| 域名 + 端口 80 空闲 | Let's Encrypt | ✅ | ✅ | 自动申请免费证书 |
| 域名 + 端口 80 被占 | Certbot | ✅ | ❌ | 通过 nginx webroot 申请 |
| IP 地址 | 自签名 | ❌ | ❌ | 10 年有效期，客户端需配置 |

### 2.5 验证部署

```bash
# 检查服务状态
sudo systemctl status tailscale-derp

# 检查端口监听
sudo ss -tlnp | grep 443
sudo ss -ulnp | grep 3478

# 查看服务日志（会输出 DERPMap 配置 JSON）
sudo journalctl -u tailscale-derp -n 20
```

日志中会输出类似这样的 DERPMap 配置：

```json
{"Name":"custom","RegionID":900,"HostName":"8.137.164.32","CertName":"sha256-raw:xxxxx"}
```

### 2.6 服务管理

```bash
python main.py --tool tailscale-derp
# [3] Manage Service → Start / Stop / Restart / Update
```

### 2.7 卸载清理

```bash
python main.py --tool tailscale-derp
# [5] Cleanup / Remove → 确认后自动停止服务、删除所有文件
```

---

## 3. 客户端部署 — Linux

### 3.1 一键部署

```bash
cd ~/LinuxScriptToolbox
python main.py --tool tailscale-client
```

### 3.2 安装 Tailscale

选择 **[3] Install Tailscale**：

```
工具会自动:
1. 下载 Tailscale 官方安装脚本
2. 安装 Tailscale
3. 提示启动并登录
```

登录时浏览器会弹出 Tailscale 页面，使用 **Google/GitHub/Microsoft** 账号登录。

> **重要**: 家里和公司的笔记本必须用 **同一个账号** 登录！

### 3.3 手动安装（如果不使用工具）

```bash
# Debian/Ubuntu
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Arch Linux
sudo pacman -S tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up

# Fedora
sudo dnf install tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up
```

### 3.4 生成 DERPMap 配置

选择 **[1] Generate DERPMap Config**：

```
DERP 服务器 IP 或域名 [8.137.164.32]:    ← 直接回车使用默认
是否从服务器自动检测证书指纹？ [Y/n]: Y   ← 自动检测
DERP 端口（HTTPS） [443]:                ← 直接回车
STUN 端口（UDP） [3478]:                 ← 直接回车
```

工具会自动连接 DERP 服务器检测证书指纹，然后输出 DERPMap JSON。

### 3.5 查看本机 Tailscale IP

```bash
tailscale ip -4
# 输出: 100.x.x.x
```

---

## 4. 客户端部署 — Windows

### 4.1 一键部署

打开 PowerShell，运行：

```powershell
cd ~/LinuxScriptToolbox
python main.py --tool tailscale-client
```

### 4.2 安装 Tailscale

选择 **[3] Install Tailscale**：

```
工具会自动:
1. 优先尝试 winget install Tailscale.Tailscale
2. 如果 winget 不可用，自动下载 MSI 安装包安装
3. 安装完成后打开 Tailscale 图形界面
```

### 4.3 手动安装（如果不使用工具）

**方式一: winget（推荐）**
```powershell
winget install Tailscale.Tailscale
```

**方式二: 下载安装包**
1. 访问 https://tailscale.com/download
2. 下载 Windows 安装包
3. 双击安装

### 4.4 登录 Tailscale

安装完成后：
1. 系统托盘出现 Tailscale 图标
2. 右键点击 → **Log in...**
3. 浏览器弹出登录页面
4. 使用 **Google/GitHub/Microsoft** 账号登录

> **重要**: 家里和公司的笔记本必须用 **同一个账号** 登录！

### 4.5 生成 DERPMap 配置

选择 **[1] Generate DERPMap Config**，操作同 Linux。

### 4.6 查看本机 Tailscale IP

```powershell
tailscale ip -4
# 输出: 100.x.x.x
```

### 4.7 Windows 防火墙

如果连接有问题，需要允许 Tailscale 通过防火墙：

```powershell
# 以管理员身份运行 PowerShell
New-NetFirewallRule -DisplayName "Tailscale" -Direction Inbound -Action Allow -Program "C:\Program Files\Tailscale\tailscale-ipn.exe"
New-NetFirewallRule -DisplayName "Tailscale DERP" -Direction Outbound -Action Allow -RemotePort 443,3478 -Protocol TCP,UDP
```

---

## 5. 配置 DERPMap

### 5.1 获取 DERPMap 配置

在任意一台已安装 Tailscale 的设备上运行：

```bash
python main.py --tool tailscale-client
# 选择 [1] Generate DERPMap Config
```

或者从 DERP 服务器日志中获取：

```bash
ssh user@your-server "sudo journalctl -u tailscale-derp -n 20 | grep RegionID"
```

### 5.2 推送到 Tailscale ACL

**方式一: 工具自动推送**

```bash
python main.py --tool tailscale-client
# 选择 [2] Push DERPMap to Tailscale
```

**方式二: 手动配置**

1. 打开 Tailscale ACL 编辑器: https://login.tailscale.com/admin/acls/file

2. 在 JSON 配置末尾添加 `derpMap` 字段：

```json
{
  // ... 你原有的 ACL 规则 ...

  "derpMap": {
    "Regions": {
      "900": {
        "RegionID": 900,
        "RegionCode": "custom",
        "RegionName": "My DERP Relay",
        "Nodes": [
          {
            "Name": "1",
            "RegionID": 900,
            "HostName": "8.137.164.32",
            "CertName": "sha256-raw:你的证书指纹",
            "DERPPort": 443,
            "STUNPort": 3478,
            "InsecureForTests": true
          }
        ]
      }
    }
  }
}
```

3. 点击 **Save** 保存

> **注意**: `InsecureForTests: true` 仅在使用自签名证书时需要。如果使用 Let's Encrypt 证书，可以去掉这行。

---

## 6. 验证连接与 SSH 互联

### 6.1 验证 DERP 连通性

在每台设备上运行：

```bash
python main.py --tool tailscale-client
# 选择 [4] Verify DERP Connection
```

或者手动运行：

```bash
tailscale netcheck
```

正常输出应包含：

```
Region  custom (900)
  8.137.164.32   reachable, latency XXms (DERP)
```

### 6.2 查看组网状态

```bash
tailscale status
```

输出示例：

```
100.x.x.1    home-laptop      user@  linux   -
100.x.x.2    work-laptop      user@  windows -
```

### 6.3 SSH 互联

**从 Linux 连接 Windows**:
```bash
# Windows 需要先启用 OpenSSH Server
# Windows 设置 → 应用 → 可选功能 → 添加 OpenSSH Server

ssh windows-user@100.x.x.2
```

**从 Windows 连接 Linux**:
```powershell
ssh linux-user@100.x.x.1
```

**从 Linux 连接 Linux**:
```bash
ssh user@100.x.x.1
```

### 6.4 文件传输

```bash
# 从本地复制到远程
scp file.txt user@100.x.x.1:~/Desktop/

# 从远程复制到本地
scp user@100.x.x.1:~/file.txt ./

# 同步目录
rsync -avz ./folder/ user@100.x.x.1:~/folder/
```

---

## 7. 常见问题

### Q: tailscale netcheck 显示 DERP 不可达？

**检查项**:
1. 服务器防火墙是否开放 443/tcp 和 3478/udp
2. 阿里云/腾讯云安全组是否放行这两个端口
3. DERP 服务是否正在运行: `sudo systemctl status tailscale-derp`

```bash
# 在服务器上检查端口监听
sudo ss -tlnp | grep 443
sudo ss -ulnp | grep 3478

# 在客户端测试连通性
curl -k https://8.137.164.32/derp/latency-check
```

### Q: 使用自签名证书时连接失败？

确保 DERPMap 配置中包含:
```json
"InsecureForTests": true
```

### Q: 两台设备显示在线但 ping 不通？

1. 确认两台设备登录的是 **同一个 Tailscale 账号**
2. 检查 Tailscale 状态: `tailscale status`
3. 检查是否被对方的防火墙拦截

### Q: Windows SSH 连接被拒绝？

Windows 默认未启用 OpenSSH Server:

```powershell
# 以管理员身份运行
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

### Q: DERP 中继流量消耗大吗？

- DERP 只在 P2P 直连失败时使用
- 流量为加密的 WireGuard 封装，额外开销约 5-10%
- SSH 会话本身流量极小（几 KB/s），DERP 中继几乎无感知

### Q: 如何查看 DERP 服务器日志？

```bash
# 实时日志
sudo journalctl -u tailscale-derp -f

# 最近 50 行
sudo journalctl -u tailscale-derp -n 50
```

### Q: 如何更新 DERP 服务器？

```bash
python main.py --tool tailscale-derp
# [3] Manage Service → [4] Update
```

### Q: 客户端 DERPMap 配置修改后需要重启 Tailscale 吗？

不需要。Tailscale 会自动从协调服务器拉取 DERPMap 更新，通常在几分钟内生效。如果想立即生效：

```bash
# Linux
sudo tailscale up

# Windows
# 右键托盘图标 → Disconnect → 再次 Log in
```
