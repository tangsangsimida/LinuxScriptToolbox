# 优化方案报告

> 由测试 Agent（Agent B）持续收集。所有优化建议不构成 Issue，仅作参考。

## 2026-07-04 第一轮

### UX/体验优化

- **Git 代理配置**：当前 `quick-fixes` 的 Git 代理设置要求用户手动输入完整 URL。若能自动检测当前代理然后提供一个可编辑的默认值（如 `ask()` 支持预填），体验会更流畅。
- **备份文件可读性**：`backup-restore` 的备份文件名使用时间戳 `YYYYMMDD_HHMMSS`，列表中有7个备份时难以一眼识别。建议在列表时显示 `从旧到新` 排序，或在文件名中增加可读标签选项。
- **备份列表排序**: 当前最新备份在最前，人工观察时最新在最前是合理的。但选项索引从 1 开始，第 1 个总是最新的。

### 功能增强

- **system-info 网络状态**: 当前显示 `ss` 原始输出，格式较松散。可考虑按连接状态（LISTEN/ESTABLISHED）分组显示。
- **system-info 内存**: 当前 `Mem` 行是原始 `free -h` 输出格式，意义不明确。建议拆分为 Total/Used/Available 等命名列。

### 架构优化

- **分组翻译**: Issue #38 确认翻译正常，但实际测试是在主菜单渲染时验证的，直接用 `t()` 函数在 SSH 管道模式调用时因语法问题产生误报。
- **repo 文件处理白名单**: Issue #39 - `_optimize_fedora()` 无条件替换所有 `.repo` 文件的 baseurl host，但 tailscale、docker-ce 等第三方仓库不应被替换。建议增加白名单机制，只替换已知的发行版官方仓库（如 AliYun.repo、epel.repo 等），或至少检查 host 不是已知的第三方域名。

### 测试覆盖率

- 对 shorin-setup 等外部脚本执行工具，测试范围有限（需要实际执行外部脚本才能验证）。网络不可达时已优雅降级。
- 跨平台（Windows/macOS）无法在 alinux 上测试。

## 2026-07-04 第二轮（实际操作测试）

### 发现的新问题

- **mirror-optimizer 误伤第三方 repo** (Issue #39): 替换 baseurl 操作同时影响了 `tailscale.repo` 和 `docker-ce.repo`。由于正则替换 baseurl host 的逻辑是不区分的，导致 `pkgs.tailscale.com/stable/fedora/` 被替换为 `mirrors.ustc.edu.cn/fedora/stable/fedora/`。tailscale 和 docker-ce 仓库在替换后均不可用（404）。

### 实际安装验证

- **Tailscale**: 成功安装 1.98.8 版本，`tailscaled` 服务已启动并正常运行
- **ARM GCC**: `arm-none-eabi-gcc-cs-12.4.0` 从 EPEL 成功安装
- **RISC-V GCC**: 通过 `alinux_pkgs` 使用 `gcc-riscv64-linux-gnu` 成功安装（无 `gdb-multiarch`）
- **恢复原始仓库**: 需要保存 v2 版本备份用于恢复（repo 备份机制正常工作）
