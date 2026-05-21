# niri + DMS 配置同步与问题修复记录

**日期**: 2026-05-10
**系统**: Ubuntu 24.04.4 LTS + Niri 26.04
**目标**: 将本地 Arch Linux 的 niri 配置同步到远程 Ubuntu 24.04 设备

---

## 1. SSH 免密登录配置

**问题**: 远程设备 `dennis@10.173.132.116` 无 SSH 密钥，无法免密登录。

**解决**:
```bash
# 生成 ED25519 密钥对
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -C "niri-sync"

# 使用密码认证拷贝公钥到远程
setsid -w ssh -o StrictHostKeyChecking=no dennis@10.173.132.116 \
  "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys" < ~/.ssh/id_ed25519.pub
```

---

## 2. niri 配置文件同步

**操作**: 将本地 `~/.config/niri/` 完整同步到远程设备。

```bash
tar -C ~/.config -czf - niri/ | ssh dennis@10.173.132.116 "tar -C ~/.config -xzf -"
```

**同步内容**:
- `config.kdl` — 主配置
- `layout.kdl`, `animations.kdl`, `blur.kdl`
- `shorin-windowrules.kdl`
- `dms/` — binds, colors, outputs, cursor, alttab, supertab, layout, windowrules, wpblur
- `scripts/` — niri-binds, niri-pick, niri-force-kill-window, screenshot-sound.sh

**备份**: 原远程配置备份至 `~/.config/niri.bak.*`

---

## 3. DMS (DankMaterialShell) 安装

### 3.1 dsearch (文件搜索服务)

**来源**: 本地 Arch 的 `dsearch-bin` 包，Go 编译，**静态链接**。

```bash
scp /usr/bin/dsearch dennis@10.173.132.116:~/.local/bin/dsearch
```

### 3.2 dgop (系统监控)

**来源**: 本地 Arch 的 `dgop` 二进制，Go 编译，动态链接但仅依赖 glibc。

```bash
scp /usr/bin/dgop dennis@10.173.132.116:~/.local/bin/dgop
```

### 3.3 dms CLI + Daemon

**来源**: 官方 GitHub Release `dms-full-amd64.tar.gz` v1.4.6，静态链接。

```bash
# 本地下载
curl -fsSL "https://github.com/AvengeMedia/DankMaterialShell/releases/download/v1.4.6/dms-full-amd64.tar.gz" \
  -o /tmp/dms-full-amd64.tar.gz

# 提取 dms 二进制并上传
scp /tmp/dms-full/bin/dms dennis@10.173.132.116:~/.local/bin/dms
```

### 3.4 quickshell (DMS 的 QML 运行时)

**问题**: quickshell 需要编译，依赖 Qt >= 6.6。Ubuntu 24.04 系统 Qt 为 6.4.2，但用户已安装 **Qt 6.10.2** 到 `~/software/QT/6.10.2/gcc_64/`。

**编译过程**:
```bash
# 克隆源码
git clone --depth 1 https://git.outfoxxed.me/quickshell/quickshell.git

# 安装编译依赖
sudo apt-get install -y libjemalloc-dev libunwind-dev libdwarf-dev \
  libpam0g-dev libpolkit-gobject-1-dev libvulkan-dev spirv-tools \
  libcli11-dev libpipewire-0.3-dev

# 配置 (使用 Qt 6.10.2)
cmake -GNinja -B build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH=$HOME/software/QT/6.10.2/gcc_64 \
  -DCRASH_HANDLER=OFF -DUSE_JEMALLOC=OFF -DSERVICE_POLKIT=OFF

# 编译
cmake --build build -j$(nproc)

# 安装到用户目录
cp build/src/quickshell ~/.local/bin/quickshell
ln -sf ~/.local/bin/quickshell ~/.local/bin/qs
```

### 3.5 DMS QML 配置文件

```bash
mkdir -p ~/.config/quickshell
ln -sf ~/.local/share/quickshell/dms ~/.config/quickshell/dms
```

---

## 4. 环境变量配置

**问题**: niri 通过 systemd 服务启动，子进程无法获取 fish shell 的 `LD_LIBRARY_PATH`。

**解决**: 在 systemd 用户环境中设置 Qt 库路径。

```bash
systemctl --user set-environment \
  LD_LIBRARY_PATH=/home/dennis/software/QT/6.10.2/gcc_64/lib:/home/dennis/.local/lib \
  QT_QPA_PLATFORM_PLUGIN_PATH=/home/dennis/software/QT/6.10.2/gcc_64/plugins \
  QT_ROOT_DIR=/home/dennis/software/QT/6.10.2/gcc_64
```

**持久化**: 创建 `~/.config/environment.d/qt.conf`:
```
LD_LIBRARY_PATH=/home/dennis/software/QT/6.10.2/gcc_64/lib:/home/dennis/.local/lib
QT_QPA_PLATFORM_PLUGIN_PATH=/home/dennis/software/QT/6.10.2/gcc_64/plugins
QT_ROOT_DIR=/home/dennis/software/QT/6.10.2/gcc_64
```

---

## 5. GPU 渲染错误修复

### 问题诊断

- **硬件**: Intel Arc B580 (独立) + AMD Radeon 780M (集成)
- **显示器**: 连接在 Intel Arc 的 DP-2 上
- **现象**: niri 使用 AMD 集显渲染 (renderD129)，再拷贝到 Intel 独显输出，导致卡顿

### 根因

AMD iGPU 的 PCI 配置中 VGA I/O 使能位 (bit 0) 为 1，Intel 为 0。内核据此将 AMD 标记为 `boot_vga=1`，niri 选择它为主渲染 GPU。

```
Intel (03:00.0): COMMAND=0x0006 (I/O- Mem+ BusMaster+)
AMD   (c8:00.0): COMMAND=0x0407 (I/O+ Mem+ BusMaster+)
```

### 运行修复

```bash
# 禁用 AMD 的 VGA I/O，启用 Intel 的 VGA I/O
sudo setpci -s c8:00.0 COMMAND=0x0406
sudo setpci -s 03:00.0 COMMAND=0x0007
systemctl --user restart niri.service
```

### 持久化修复

创建 initramfs 脚本 `/etc/initramfs-tools/scripts/init-premount/swap-gpu-vga`:

```sh
#!/bin/sh
echo 'Swapping GPU VGA I/O: Intel primary...'
setpci -s c8:00.0 COMMAND=0x0406
setpci -s 03:00.0 COMMAND=0x0007
```

```bash
sudo chmod +x /etc/initramfs-tools/scripts/init-premount/swap-gpu-vga
sudo update-initramfs -u -k all
```

### GRUB 配置

添加 `amdgpu.modeset=0` 禁用 AMD 显示输出 (`/etc/default/grub`):

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash pcie_aspm=off pcie_acs_override=downstream,multifunction iommu=pt xe.force_probe=* amdgpu.modeset=0"
```

### 验证结果

| 项目 | 修复前 | 修复后 |
|------|--------|--------|
| 渲染 GPU | AMD 780M (2GB) | **Intel Arc B580 (12GB)** |
| 渲染设备 | /dev/dri/renderD129 | **/dev/dri/renderD128** |
| OpenGL 渲染器 | AMD Radeon 780M | **Mesa Intel Arc B580** |
| 帧传输 | 跨 GPU 拷贝 | 直接输出 |

---

## 6. Claude Code 在终端中无法使用

**原因**: 切换 Niri 后默认终端为 kitty，shell 设为 fish。Claude Code 通过 nvm 安装在 `~/.nvm/versions/node/v22.22.0/bin/claude`，但 fish 不读取 `.bashrc`，nvm 路径未加入 fish PATH。

**解决**:
```fish
fish_add_path ~/.nvm/versions/node/v22.22.0/bin
```

---

## 7. 输入法配置

**问题1**: fcitx5 profile 引用了 mozc（日语输入法），但 fcitx5-mozc 未安装。
- 从 `~/.config/fcitx5/profile` 移除了 mozc 条目。

**问题2**: rime 默认 schema 为 rime_ice（雾凇拼音），但未安装。系统仅预装了 luna_pinyin_simp。
- 下载并安装了雾凇拼音 (rime_ice)，含 cn_dicts 词库 (8105、41448、腾讯词库等)。

**问题3**: 曾尝试仅保留 rime 移除 keyboard-us，但 rime_ice 默认处于英文模式导致无法输入中文。
- 最终配置: keyboard-us + rime（雾凇拼音）两个输入法，在 rime 中按 Shift 切换中英文模式。

**当前输入法配置**:
- Profile: `~/.config/fcitx5/profile` (keyboard-us + rime)
- Rime 配置: `~/.local/share/fcitx5/rime/`
  - `default.custom.yaml` → 仅启用 rime_ice schema
  - `rime_ice.schema.yaml` + `cn_dicts/` 词库 + `lua/` 脚本
- 切换输入法: Super+Space

---

## 8. Clash 代理未在终端中生效

**原因**: Clash Verge 运行在 `127.0.0.1:7890`，但 fish shell 未设置代理环境变量。`.bashrc` 中有代理配置，fish 没有。

**解决**: 在 `~/.config/fish/config.fish` 添加:
```fish
set -gx http_proxy http://127.0.0.1:7890
set -gx https_proxy http://127.0.0.1:7890
set -gx all_proxy socks5://127.0.0.1:7890
set -gx no_proxy localhost,127.0.0.1,::1,.local
```

> 注: TUN 模式无需开启，上述配置即可正常工作。

---

## 9. Fish Shell 环境变量迁移

**原因**: 之前使用 bash，现在切换到 fish，但 `.bashrc` 中大量环境变量和 PATH 条目未迁移到 fish 配置。

已在 `~/.config/fish/config.fish` 补充:

**环境变量**:
- `NVM_DIR=/home/dennis/.nvm`
- `QT_ROOT_DIR=/home/dennis/software/QT/6.10.2/gcc_64`
- `LD_LIBRARY_PATH` (Qt libs + `~/.local/lib`)
- `QT_QPA_PLATFORM_PLUGIN_PATH`
- `CMAKE_PREFIX_PATH`, `CMAKE_ROOT`, `NINJA_ROOT`
- `LIBVA_DRIVER_NAME=iHD` (Intel B580 视频加速)

**PATH 补充**:
- `~/software/vcpkg`
- `~/.opencode/bin`
- Qt 6.10.2/bin, CMake/bin, Ninja
- `~/.local/stm32cube/bin`
- `~/.cargo/bin`
- `~/.local/bin` (已有)
- `~/.nvm/versions/node/v22.22.0/bin` (fish_add_path)

---

## 10. 光标主题修复

**问题**: Ubuntu 缺少 breeze_cursors 光标主题。

**解决**: 从 Arch 复制到 Ubuntu `/usr/share/icons/`。

---

## 11. Kitty 终端版本升级

**问题**: Ubuntu kitty 0.32.2 (旧) vs Arch 0.46.2，cursor_trail 动画效果差。

**解决**:
```bash
# 下载
curl -fSL "https://github.com/kovidgoyal/kitty/releases/download/v0.46.2/kitty-0.46.2-x86_64.txz" \
  -o /tmp/kitty-0.46.2-x86_64.txz

# 安装到用户目录
tar -xJf /tmp/kitty-0.46.2-x86_64.txz -C ~/.local/
ln -sf ~/.local/kitty.app/bin/kitty ~/.local/bin/kitty
```

**配置文件同步**: `dank-tabs.conf`, `dank-theme.conf`, `kitty.conf`

---

## 12. 主题颜色不随壁纸变化

**问题**: Ubuntu 上 DMS 主题颜色不会随壁纸变化，终端和窗口边框配色始终不变。

**根因**: Qt 6.10.2 的 imageformats 插件（libqjpeg.so, libqsvg.so）被从 Arch 复制的不兼容 Qt 6.11 版本覆盖，导致无法解码 JPEG/SVG 图片，DMS 无法从壁纸提取颜色。

**解决**:
1. 从 Flatpak KDE Platform 6.10 运行时复制正确的 Qt 6.10 imageformat 插件
2. 安装 libjpeg62（Flatpak 插件需要的 JPEG 库版本）

---

## 13. 出现两个顶部任务栏

**问题**: DMS 手动重启多次，旧实例未完全退出，导致两个 dms 同时运行。

**解决**: 清理所有 dms 进程后重启单个实例。

```bash
dms kill
pkill -9 -f dms
dms -c ~/.config/quickshell/dms run --daemon
```

---

## 14. Niri 下应用用户数据「丢失」

**原因**: GNOME 设置守护进程（gsd-xsettings 等）的 autostart 文件均有 `OnlyShowIn=GNOME;` 条件，而 Niri 下 `XDG_CURRENT_DESKTOP=niri`，导致这些服务全部未启动。缺少 gsd-xsettings 会使 GTK 应用的主题、字体、图标、缩放等恢复默认值，看起来像是全新安装。

实际上应用数据（Chrome 书签、VS Code 设置、Steam 存档等）一直保存在 `~/.config/` 和 `~/.local/share/` 中，从未丢失。

**解决**:
1. `~/.config/niri/config.kdl` environment 块添加:
   ```
   XDG_CURRENT_DESKTOP niri:GNOME
   ```
   并将 startup 脚本中的值改为 `niri:GNOME`

2. `~/.config/systemd/user/niri.service.d/gnome-compat.conf`:
   ```ini
   [Service]
   Environment=XDG_CURRENT_DESKTOP=niri:GNOME
   ```

3. 修改 session 文件:
   ```bash
   sudo sed -i 's/DesktopNames=niri/DesktopNames=niri:GNOME/' \
     /usr/share/wayland-sessions/niri.desktop
   ```

退出 Niri 重新登录后生效。

---

## 15. 最终文件布局

| 路径 | 说明 |
|------|------|
| `~/.config/niri/` | niri 配置 (config.kdl, dms/, scripts/) |
| `~/.config/quickshell/dms/` | DMS QML 配置 (symlink → ~/.local/share/quickshell/dms) |
| `~/.local/bin/dms` | DMS CLI + Daemon |
| `~/.local/bin/dsearch` | 文件搜索服务 |
| `~/.local/bin/dgop` | 系统监控 |
| `~/.local/bin/quickshell` (qs) | QML 运行时 (本地编译) |
| `~/.config/environment.d/qt.conf` | systemd Qt 环境变量 |
| `~/.local/lib/libcpptrace.so*` | quickshell 依赖库 |
| `/etc/default/grub` | `amdgpu.modeset=0` |
| `/etc/initramfs-tools/scripts/init-premount/swap-gpu-vga` | 持久化 GPU 修复 |
| `~/.config/fish/config.fish` | fish shell 环境变量与 PATH |
| `~/.config/fcitx5/profile` | 输入法配置 (keyboard-us + rime) |
| `~/.local/share/fcitx5/rime/` | 雾凇拼音词库与配置 |

---

## 16. 常用快捷键

| 快捷键 | 功能 |
|--------|------|
| Super+Return | 新终端 (kitty) |
| Super+Space | 切换输入法 |
| Super+Q | 关闭窗口 |
| Super+Shift+E | 退出 Niri |
| Super+B | 浏览器 |
| Super+Z | 应用启动器 |
| Mod+Alt+O | opencode AI 助手 |
