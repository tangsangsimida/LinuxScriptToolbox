"""Tools package — auto-discovers and registers all Tool subclasses.

工具包 — 自动发现并注册所有 Tool 子类。

Uses pkgutil.walk_packages to scan the tools/ directory tree for modules
containing Tool subclasses, then instantiates them into the global TOOLS list.

使用 pkgutil.walk_packages 扫描 tools/ 目录树，找到包含 Tool 子类的模块，
然后实例化并加入全局 TOOLS 列表。
"""

import importlib
import pkgutil
import warnings
from pathlib import Path

from tools.base import Tool

# Root directory of the tools package / tools 包的根目录
_TOOLS_PKG = Path(__file__).parent


def _auto_import_translations(modname: str) -> None:
    """Auto-import the matching *_translations.py sibling of a tool module.

    自动导入工具模块对应的 *_translations.py 兄弟模块。

    For example, tools.common.device_init → tools.common.device_init_translations.
    importlib caches modules in sys.modules, so repeated calls are cheap.

    Args:
        modname: Fully qualified module name (e.g. "tools.common.device_init")
    """
    trans_modname = f"{modname}_translations"
    try:
        importlib.import_module(trans_modname)
    except ImportError as e:
        # Only ignore "module not found"; re-raise syntax/import errors inside the module
        # 只忽略"模块未找到"；模块内部的语法/导入错误需要重新抛出
        if e.name and e.name.replace(".", "_") in trans_modname.replace(".", "_"):
            pass  # Module doesn't exist / 模块不存在
        else:
            warnings.warn(f"Failed to import translations {trans_modname}: {e}")


# Walk the tools/ package and instantiate every Tool subclass found.
#
# 遍历 tools/ 包，实例化找到的每个 Tool 子类。
#
# Skips __init__ modules and tools.base itself to avoid registering
# the abstract base class.
#
# 跳过 __init__ 模块和 tools.base 本身，避免注册抽象基类。
#
# Returns:
#     List of instantiated Tool objects / 已实例化的 Tool 对象列表
def _discover_tools() -> list[Tool]:
    tools: list[Tool] = []
    for _importer, modname, _ispkg in pkgutil.walk_packages(
        path=[str(_TOOLS_PKG)], prefix="tools."
    ):
        # Skip init modules and the base module / 跳过 init 模块和 base 模块
        if modname.endswith(".__init__") or modname == "tools.base":
            continue
        try:
            mod = importlib.import_module(modname)
        except ImportError as e:
            warnings.warn(f"Failed to import tool module {modname}: {e}")
            continue

        # Auto-import sibling translation modules / 自动导入同级翻译模块
        _auto_import_translations(modname)
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if (
                isinstance(cls, type)
                and issubclass(cls, Tool)
                and cls is not Tool
            ):
                try:
                    tools.append(cls())
                except Exception as e:
                    warnings.warn(f"Failed to instantiate {attr} from {modname}: {e}")
    return tools


# Global list of all discovered tool instances / 所有已发现工具实例的全局列表
TOOLS: list[Tool] = _discover_tools()


# Filter tools by Linux distribution name. Deprecated: use get_tools() instead.
#
# 按 Linux 发行版名称过滤工具。已弃用：请使用 get_tools()。
def get_tools_for_distro(distro: str) -> list[Tool]:
    warnings.warn(
        "get_tools_for_distro() is deprecated, use get_tools(distro, platform) instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return [t for t in TOOLS if distro in t.distros]


# Filter tools by platform. Deprecated: use get_tools() instead.
#
# 按平台过滤工具。已弃用：请使用 get_tools()。
def get_tools_for_platform(platform: str) -> list[Tool]:
    warnings.warn(
        "get_tools_for_platform() is deprecated, use get_tools(distro, platform) instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return [t for t in TOOLS if platform in t.platforms]


# Filter tools by distro and/or platform.
#
# 按发行版和/或平台过滤工具。
#
# Both parameters are optional. When provided, a tool must match ALL
# specified criteria to be included. When both are None, all tools are returned.
#
# 两个参数均为可选。提供时，工具必须匹配所有指定条件才会被包含。
# 两者都为 None 时返回所有工具。
#
# Args:
#     distro: Distribution identifier, or None to skip distro filtering
#             / 发行版标识符，或 None 跳过发行版过滤
#     platform: Platform identifier, or None to skip platform filtering
#               / 平台标识符，或 None 跳过平台过滤
#
# Returns:
#     List of tools matching the criteria / 满足条件的工具列表
def get_tools(distro: str | None = None, platform: str | None = None) -> list[Tool]:
    return [
        t for t in TOOLS
        if (distro is None or distro in t.distros)
        and (platform is None or platform in t.platforms)
    ]
