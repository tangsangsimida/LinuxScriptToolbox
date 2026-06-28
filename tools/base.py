"""Base module for all tools in the LinuxScriptToolbox project.

LinuxScriptToolbox 项目中所有工具的基类模块。

Every tool must subclass Tool and implement the run() method.
Tool attributes control how the tool appears in menus and whether
it can run in batch mode.

每个工具必须继承 Tool 并实现 run() 方法。
Tool 属性控制工具在菜单中的显示方式以及是否可在批量模式下运行。
"""

from abc import ABC, abstractmethod


class Tool(ABC):
    """Abstract base class that all tools must inherit from.

    所有工具必须继承的抽象基类。定义了工具的通用属性和接口。

    Attributes:
        name: Unique identifier used in CLI --tool flag / CLI --tool 参数使用的唯一标识符
        display_name: Human-readable name shown in menus / 菜单中显示的人类可读名称
        description: Brief summary of what the tool does / 工具功能的简要描述
        distros: List of supported distro identifiers / 支持的发行版标识符列表
        platforms: Tuple of supported platforms / 支持的平台元组
        mutates_system: Whether the tool modifies system state / 工具是否修改系统状态
        requires_network: Whether the tool needs network access / 工具是否需要网络访问
        requires_sudo: Whether the tool requires root privileges / 工具是否需要 root 权限
        safe_for_run_all: Whether safe to run in batch "run all" mode / 是否可在批量"全部运行"模式下安全运行
    """

    name: str
    display_name: str
    description: str
    distros: list[str]
    platforms: list[str] = ["linux"]  # Supported platforms / 支持的平台
    mutates_system: bool = True  # Modifies system state / 修改系统状态
    requires_network: bool = False  # Needs network access / 需要网络访问
    requires_sudo: bool = False  # Requires root privileges / 需要 root 权限
    safe_for_run_all: bool = False  # Safe for batch mode / 可在批量模式下安全运行

    @abstractmethod
    def run(self) -> bool | None:
        """Run the tool interactively.

        交互式运行工具。

        Returns:
            True/False to show "press enter" prompt, None to skip it.
            返回 True/False 表示需要显示"按回车继续"提示，返回 None 则跳过。
        """
        ...

    def run_all(self) -> bool | None:
        """Run the tool in non-destructive run-all mode.

        以非破坏性的批量运行模式执行工具。

        Default implementation delegates to run(). Override for tools
        that need different behavior in batch mode.

        默认实现委托给 run()。需要在批量模式下有不同行为的工具可重写此方法。
        """
        return self.run()
    def run_dry(self) -> str | None:
        """Preview what the tool would do without making changes.

        预览工具将要执行的操作，不进行实际修改。

        Returns a human-readable string describing the planned actions,
        or None if dry-run is not supported for this tool.

        返回描述计划操作的人类可读字符串，如果不支持 dry-run 则返回 None。
        """
        return None

