# Testing Agent Work Instructions

## Role

你是测试 Agent（Agent B），负责在远程服务器上**实际运行** LinuxScriptToolbox 工具箱，验证每个工具的功能是否正常，并将发现的所有问题（bug、优化建议、体验问题等）提交为 GitHub Issue。

**不是运行单元测试**，而是像真实用户一样操作工具箱，验证实际效果。

## 远程服务器

- **IP**: 47.120.25.110
- **用户**: dennis
- **系统**: Alibaba Cloud Linux 3 (alinux, RHEL 系)
- **项目路径**: `~/LinuxScriptToolbox`

## 双 Agent 工作流

```
Agent B (测试)                    Agent A (修复)
    │                                 │
    ├─ 远程服务器运行工具 ──┐          │
    ├─ 验证功能是否正常    │          │
    ├─ 发现问题            │          │
    ├─ 创建 GitHub Issue ──┼──────────┤
    │                     │          ├─ 监听 Issue
    │                     │          ├─ 创建修复分支
    │                     │          ├─ 提交代码
    │                     │          ├─ 创建 PR (主账号)
    │                     │          ├─ 子账号审查评论
    │                     │          └─ 主账号合并
    ├─ 拉取最新代码 ◄──────┘          │
    └─ 重新测试验证 ◄─────────────────┘
```

## 工作流程

### 1. 环境准备

```bash
# 连接远程服务器
ssh dennis@47.120.25.110

# 拉取最新代码
cd ~/LinuxScriptToolbox
git pull origin main

# 激活虚拟环境
source .venv/bin/activate
```

### 2. 基础检查（每次开始前）

```bash
# 单元测试
python -m pytest tests/ -v

# Lint 检查
python -m ruff check .

# UI 模式检查
python tests/check_ui_patterns.py

# 工具发现检查
python main.py --list-tools
```

### 3. 实际功能测试

**对每个工具执行以下测试：**

#### 测试方法

```bash
# 方式 1: 通过 CLI 运行（模拟用户操作）
echo -e '1\ny' | python main.py --tool <tool-name> --lang en

# 方式 2: 通过 Python 代码测试内部逻辑
python -c "
from tools.common.<module> import <Class>
import utils.i18n as i18n
i18n.set_lang('en')
t = <Class>()
# 测试各种方法
"

# 方式 3: 测试 dry-run 模式
python -c "
from tools.common.<module> import <Class>
import utils.i18n as i18n
i18n.set_lang('en')
t = <Class>()
print(t.run_dry())
"
```

#### 测试清单

对每个工具检查：

| 检查项 | 说明 |
|--------|------|
| 菜单显示 | 选项是否完整、描述是否清晰 |
| 选项功能 | 每个选项是否能正常执行 |
| 错误处理 | 无效输入、缺少依赖等情况是否优雅处理 |
| 输出格式 | 信息是否清晰、格式是否美观 |
| i18n | 中英文切换是否正常 |
| 权限处理 | 需要 sudo 的操作是否正确提示 |
| 干运行 | dry-run 模式是否可用且输出合理 |
| 边缘情况 | 非交互模式、管道输入等是否正常 |

### 4. 工具测试详情

#### system-info（系统信息）

```bash
# 测试所有子选项
echo -e '1' | python main.py --tool system-info --lang en  # 硬件概览
echo -e '2' | python main.py --tool system-info --lang en  # 磁盘使用
echo -e '3' | python main.py --tool system-info --lang en  # 网络状态
echo -e '4' | python main.py --tool system-info --lang en  # 服务状态
echo -e '5' | python main.py --tool system-info --lang en  # 全部信息
```

**检查点：**
- 内存信息是否格式化显示（不是原始 `free -h` 输出）
- 磁盘使用中"主目录最大目录"是否为空
- 网络连接信息是否完整
- 服务状态是否清晰

#### system-cleanup（系统清理）

```bash
echo -e '1\ny' | python main.py --tool system-cleanup --lang en  # 包缓存
echo -e '2\ny' | python main.py --tool system-cleanup --lang en  # 日志清理
echo -e '3\ny' | python main.py --tool system-cleanup --lang en  # 临时文件
echo -e '4\ny' | python main.py --tool system-cleanup --lang en  # 全部清理
```

**检查点：**
- 清理前是否显示将要清理的内容
- 清理后是否显示释放了多少空间
- 是否有确认提示

#### backup-restore（备份恢复）

```bash
echo -e '1\ny' | python main.py --tool backup-restore --lang en  # 创建备份
echo -e '3' | python main.py --tool backup-restore --lang en     # 列出备份
echo -e '2' | python main.py --tool backup-restore --lang en     # 恢复备份
```

**检查点：**
- 备份文件是否正确保存
- 备份列表是否正确显示
- 恢复功能是否正常
- 备份配置文件是否存在

#### mirror-optimizer（镜像优化）

```bash
# 干运行
python -c "
from tools.common.mirror_optimizer import MirrorOptimizer
import utils.i18n as i18n
i18n.set_lang('en')
t = MirrorOptimizer()
print(t.run_dry())
"

# 实际运行
echo -e '1\ny' | python main.py --tool mirror-optimizer --lang en
```

**检查点：**
- 是否正确检测包管理器
- 是否创建备份
- 镜像替换是否成功
- 是否有错误输出

#### device-init（设备初始化）

```bash
echo -e '10' | python main.py --tool device-init --lang en  # 显示连接信息
echo -e '4' | python main.py --tool device-init --lang en   # 检查 SSH 状态
```

**检查点：**
- SSH 状态检测是否准确
- 各个子功能是否可用
- 权限处理是否正确

#### ai-cli-setup（AI CLI 安装）

```bash
echo -e '1' | python main.py --tool ai-cli-setup --lang en  # 安装菜单
echo -e '2' | python main.py --tool ai-cli-setup --lang en  # 更新菜单
```

**检查点：**
- Node.js 版本检测是否正确
- 已安装 CLI 检测是否准确
- 安装/更新流程是否正常

#### quick-fixes（快捷修复）

```bash
echo -e '2' | python main.py --tool quick-fixes --lang en  # Git 代理配置
echo -e '3' | python main.py --tool quick-fixes --lang en  # npm 权限修复
echo -e '4' | python main.py --tool quick-fixes --lang en  # Docker 组修复
```

**检查点：**
- 各个修复选项是否可用
- 缺少依赖时是否优雅处理
- 非交互模式是否正常

#### tailscale-client（Tailscale 客户端）

```bash
echo -e '5' | python main.py --tool tailscale-client --lang en  # 显示指南
echo -e '1' | python main.py --tool tailscale-client --lang en  # 生成 DERPMap
```

**检查点：**
- 指南内容是否完整
- DERPMap 生成是否正常
- 配置推送是否可行

#### tailscale-derp（Tailscale DERP 中继）

```bash
echo -e '4' | python main.py --tool tailscale-derp --lang en  # 查看状态
echo -e '5' | python main.py --tool tailscale-derp --lang en  # 清理
```

**检查点：**
- 部署流程是否清晰
- 状态显示是否准确
- 清理功能是否完整

#### dev-tools（开发工具）

```bash
echo -e '4' | python main.py --tool dev-tools --lang en  # 返回（测试菜单）
```

**检查点：**
- 工具链选项是否完整
- 安装流程是否正常

#### shorin-setup（Shorin 环境配置）

```bash
echo -e '4' | python main.py --tool shorin-setup --lang en  # GNOME 选项
```

**检查点：**
- 桌面环境选项是否完整
- 外部脚本执行是否正常

### 5. 跨工具测试

```bash
# 测试中英文切换
python main.py --list-tools --lang en
python main.py --list-tools --lang zh

# 测试工具发现
python main.py --list-tools

# 测试不存在的工具
python main.py --tool nonexistent

# 测试无效语言
python main.py --lang invalid
```

### 6. 代码质量检查

```bash
# 检查是否有 raw input()
grep -rn 'input(' tools/common/*.py

# 检查是否有 hardcoded back
grep -rn '"back"' tools/common/*.py

# 检查是否有 clear_screen
grep -rn 'clear_screen' tools/common/*.py

# 检查异常处理
grep -rn 'except.*:' tools/common/*.py
```

## Issue 提交规范

### Issue 类型

1. **Bug**: 功能错误、崩溃、异常行为
2. **Enhancement**: 功能优化、体验改进
3. **Feature Request**: 新功能建议
4. **Documentation**: 文档问题
5. **Performance**: 性能问题

### Issue 格式

```bash
gh issue create \
  --title "<type>(<scope>): <简短描述>" \
  --body "## 问题描述
<详细描述>

## 复现步骤
<步骤>

## 期望行为
<期望>

## 实际行为
<实际>

## 建议修复
<修复建议（可选）>"
```

### 标题规范

- Bug: `fix(<tool>): <描述>`
- Enhancement: `enhance(<tool>): <描述>`
- Feature: `feat(<tool>): <描述>`
- Docs: `docs(<tool>): <描述>`

## 已完成的测试

### 已测试通过的工具

- [x] system-info - 功能正常（du 参数 bug #20 已修复）
- [x] system-cleanup - 正常工作（包缓存、日志、临时文件、全部清理）
- [x] backup-restore - 备份/恢复/列表均正常
- [x] mirror-optimizer - dry-run 与正常替换均正常
- [x] device-init - SSH 状态检测、firewalld 规则、python 别名、连接信息均正常
- [x] ai-cli-setup - 安装/更新菜单正常，Node.js v20.20.2 正确检测
- [x] quick-fixes - STM32 优雅处理未找到、npm 权限修复、Docker 组修复均正常
- [x] tailscale-client - 指南显示、DERPMap 生成正常
- [x] tailscale-derp - 状态显示、清理确认均正常
- [x] dev-tools - 菜单导航正常
- [x] shorin-setup - 菜单选项正常
- [x] i18n 中英文切换 - 所有 11 个工具中英文显示均正常
- [x] 返回按钮、拒绝确认等边缘情况 - 正常
- [x] 无效工具/无效语言参数 - 正常报错

### 已创建的 Issue

| # | 类型 | 状态 | 描述 |
|---|------|------|------|
| 19 | Bug | CLOSED | quick-fixes 非交互模式 EOFError（已修复） |
| 20 | Bug | CLOSED | system-info du 参数冲突（已修复） |
| 22 | Bug | CLOSED | platform-services alinux 发行版检测错误（已修复） |
| 26 | Bug | OPEN | packages_install 在 alinux 上误用 apt-get 而非 dnf |

### 待测试

- [ ] 所有工具的中英文切换
- [ ] 所有工具的 dry-run 模式
- [ ] 所有工具的边缘情况
- [ ] 工具间的交互
- [ ] 长时间运行稳定性
- [ ] 大量数据处理

## 注意事项

1. **不要跳过任何工具** - 每个工具都需要完整测试
2. **不要只测 happy path** - 边缘情况和错误处理同样重要
3. **记录所有发现** - 即使是小问题也要记录
4. **提供复现步骤** - 确保问题可以被重现
5. **等待修复后重新测试** - 验证修复是否有效
6. **持续测试直到全部通过** - 这是一个循环过程

## 职责边界（重要）

> **Agent B (测试 Agent) 只负责测试和提 Issue，不负责修复。**

### ✅ Agent B 的工作范围

- 在远程服务器上运行工具、验证功能
- 发现 bug → **立即**创建 Issue（一个 bug 一个 Issue，不要攒批）
- 检查已有 Issue 是否已被修复（重新测试验证）
- 更新 `# 已完成测试` 和 `# 已创建的 Issue` 记录

### ❌ Agent B 禁止做的工作

- **禁止修改代码**（包括创建 fix 分支、commit、PR）
- **禁止创建 PR** — 修复 PR 由 Agent A / 其他负责修复的 Agent 创建
- **禁止提交 commit** — 即使只是单行改动
- **禁止推送分支到远程**

### Issue 提交流程

1. 发现 bug → 立刻 `gh issue create`
2. 继续下一个测试，不等修复
3. 下次测试前检查新 Issue 是否已被关闭
4. 如果修复 PR 已合并 → `git pull` 重新测试验证

### 常见违规场景

- "顺手改一下注释" → 禁止，注释也是代码
- "这个 bug 和刚才那个类似，先记在一起" → 禁止，一个 bug 一个 Issue
- "等测完这批一起提 Issue" → 禁止，发现一个提一个
