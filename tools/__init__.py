import importlib
import pkgutil
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
    return [t for t in TOOLS if distro in t.distros]
