# 优化方案报告

> 由测试 Agent（Agent B）持续收集。所有优化建议不构成 Issue，仅作参考。

## 2026-07-07 第二轮 - 回归 + 全量测试

### 验证 Issue 修复

| Issue | 标题 | 状态 | 实际验证 |
|-------|------|------|---------|
| #39 | mirror-optimizer 第三方 repo 误伤 | CLOSED (PR #40) | ✅ tailscale.repo / docker-ce.repo 保持原样 |
| #41 | shorin-setup git clone 无超时 | CLOSED (PR #42) | ✅ 源代码已含 `--depth 1 ... timeout=60` |

### 发现的 Bug

#### BUG-001 (Issue #44): tailscale-client derp_port/stun_port 空输入崩溃

- **严重性**: 中高
- **触发**: `tailscale-client` → `Generate DERPMap Config` → 4 个 ask 中任一为空（管道 EOF 或连续回车）
- **崩溃点**: `tools/common/tailscale_client.py:114-115` 直接 `int(derp_port.strip())` 无 try/except
- **traceback**: `ValueError: invalid literal for int() with base 10: ''`
- **影响**: 自动化脚本无法安全使用 DERPMap 生成；用户困惑

### UX/体验优化

1. **system-info 内存显示**: 当前直接显示 `free -h` 原始 `Mem: 14Gi 1.9Gi 5.7Gi 19Mi 7.6Gi 12Gi`，列标题缺失。建议使用表格格式标注 Total / Used / Free / Shared / Buff/Cache / Available。

2. **system-info 网络状态**: 输出格式松散（ss 原始输出），建议按状态分组（LISTEN / ESTABLISHED）。

3. **backup-restore 备份列表**: 当有 14+ 个备份时，菜单中使用纯时间戳 `20260707_141324`，难以人工识别。建议增加"取最早/最近 N 个"选项或加可读标签。

4. **quick-fixes Git 代理**: 当前 agent 没有保存历史代理值供重用，建议增加记忆功能（最近一次使用的代理）。

5. **CLI 帮助信息**: 当前仅 `main.py -h` 有输出，但 `python main.py --tool device-init` 等子工具的 `-h` 没有。建议每个工具添加 `__doc__` 帮助。

### 架构优化

1. **数字输入验证统一化**: BUG-001 暴露了多处 `int(<ask>)` 直接转换而无 try/except。建议在 `utils/ui.py` 增加 `ask_int()` / `ask_port()` 辅助函数统一处理空字符串和非数字输入回退。

2. **Backup 备份点累积**: 10+ 个备份点未自动清理，磁盘占用约 316K。建议增加 `--keep-last N` 参数，保留最近 N 个备份。

3. **system-info 服务状态**: 当前显示 Failed services 但未提供修复指引。建议点击 failed 服务名尝试自动修复（如 `systemctl reset-failed` + 重启）。

4. **mirror-optimizer dry-run 错误信息**: 当前 `need_sudo` 检测后无 sudo 提示，建议 dry-run 模式也提示 "需要 sudo"。

### 测试覆盖观察

- **管道输入测试**: 大部分工具对管道输入提供 default 值即可工作，但 tailscale-client 的 int 转换是例外
- **中英文菜单**: 12 个工具的中英文切换全部正常，翻译对齐
- **代码质量**: ruff/UI patterns/unit tests (185 passed) 全部通过
- **跨发行版**: 仅在 alinux 上测试，其他发行版（arch/debian/fedora/suse）的功能验证需在不同环境

## 2026-07-04 第一轮 (历史)

### UX/体验优化

- Git 代理配置: 建议 `ask()` 支持预填默认值检测当前代理
- 备份文件可读性: 14+ 备份列表排序问题
- system-info 网络状态: 缺少分组
- system-info 内存: 缺少列标题

### 功能增强

- backup-restore 支持加密
- mirror-optimizer 并行测试镜像源

### 架构优化

- repo 文件处理白名单（已修复 #39 验证）
- 分组翻译（误报 Issue #38）

### 持续监控

- [ ] 文件系统增长跟踪 (60M /var/log/journal)
- [ ] 备份点累积清理策略 (316K, 14个备份)
- [ ] 服务运行状态变化 (33 个服务, dnf-makecache failed)

---

**最后更新**: 2026-07-07 14:30 UTC+8
**测试轮次**: 2
**新发现 Bug**: BUG-001 (Issue #44 已创建)
**回归通过率**: 100% (2/2 已关闭 Issue 全部验证修复)
