from .arch.mirror_optimizer import ArchMirrorOptimizer

TOOLS = [
    ArchMirrorOptimizer(),
]


def get_tools_for_distro(distro: str) -> list:
    return [t for t in TOOLS if distro in t.distros]


def list_all_tools() -> list:
    return TOOLS
