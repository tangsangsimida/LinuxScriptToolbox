import importlib
import pkgutil
import warnings
from pathlib import Path

from tools.base import Tool

_TOOLS_PKG = Path(__file__).parent


def _discover_tools() -> list[Tool]:
    tools: list[Tool] = []
    for _importer, modname, _ispkg in pkgutil.walk_packages(
        path=[str(_TOOLS_PKG)], prefix="tools."
    ):
        if modname.endswith(".__init__") or modname == "tools.base":
            continue
        mod = importlib.import_module(modname)
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if (
                isinstance(cls, type)
                and issubclass(cls, Tool)
                and cls is not Tool
            ):
                tools.append(cls())
    return tools


TOOLS: list[Tool] = _discover_tools()


def get_tools_for_distro(distro: str) -> list[Tool]:
    """Deprecated. Use get_tools(distro=...) instead.

    已废弃。请使用 get_tools(distro=...) 替代。
    """
    warnings.warn(
        "get_tools_for_distro() is deprecated, use get_tools(distro=...) instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return [t for t in TOOLS if distro in t.distros]


def get_tools_for_platform(platform: str) -> list[Tool]:
    """Deprecated. Use get_tools(platform=...) instead.

    已废弃。请使用 get_tools(platform=...) 替代。
    """
    warnings.warn(
        "get_tools_for_platform() is deprecated, use get_tools(platform=...) instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return [t for t in TOOLS if platform in t.platforms]


def get_tools(distro: str | None = None, platform: str | None = None) -> list[Tool]:
    """Filter tools by distro and/or platform.

    Both arguments are optional. When provided, a tool must match ALL
    specified criteria.

    按发行版和/或平台过滤工具。两个参数均为可选；提供时工具必须匹配
    所有指定条件。

    Args:
        distro: Distro identifier, or None to skip distro filtering.
                发行版标识符，或 None 跳过发行版过滤。
        platform: Platform identifier, or None to skip platform filtering.
                  平台标识符，或 None 跳过平台过滤。

    Returns:
        List of tools matching the criteria.
    """
    return [
        t for t in TOOLS
        if (distro is None or distro in t.distros)
        and (platform is None or platform in t.platforms)
    ]