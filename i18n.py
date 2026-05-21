import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

SUPPORTED_LANGS = {"en": "English", "zh": "中文"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # UI
        "ui.available_tools": "Available tools:",
        "ui.run_all": "Run all tools",
        "ui.language": "Language",
        "ui.quit": "Quit",
        "ui.select": "Select: ",
        "ui.detected": "Detected: {distro}",
        "ui.no_tools": "No tools available for this distro.",
        "ui.press_enter": "Press Enter to continue...",
        "ui.running": "--- Running: {name} ---",
        "ui.invalid_selection": "Invalid selection",
        "ui.invalid_input": "Invalid input",
        "ui.goodbye": "Goodbye!",
        "ui.select_language": "Select language:",
        # Tools
        "tool.arch-mirror-optimizer.display_name": "Optimize Pacman Mirrors",
        "tool.arch-mirror-optimizer.description": "Add China mirrors to the top of /etc/pacman.d/mirrorlist",
        "tool.debian-mirror-optimizer.display_name": "Optimize APT Mirrors",
        "tool.debian-mirror-optimizer.description": "Replace mirrors in /etc/apt/sources.list with China mirrors",
        # Messages
        "msg.backup_saved": "Backup saved to {path}",
        "msg.backup_exists": "Backup already exists, skipped",
        "msg.mirrorlist_updated": "Mirrorlist updated with China mirrors at top",
        "msg.mirrorlist_not_found": "Error: /etc/pacman.d/mirrorlist not found",
        "msg.sources_list_not_found": "Error: /etc/apt/sources.list not found",
        "msg.sources_list_updated": "sources.list updated with China mirror",
        "msg.root_required": "Root privileges required",
    },
    "zh": {
        # UI
        "ui.available_tools": "可用工具：",
        "ui.run_all": "运行全部工具",
        "ui.language": "语言",
        "ui.quit": "退出",
        "ui.select": "选择：",
        "ui.detected": "检测到：{distro}",
        "ui.no_tools": "当前发行版没有可用工具。",
        "ui.press_enter": "按回车键继续...",
        "ui.running": "--- 正在运行：{name} ---",
        "ui.invalid_selection": "无效选择",
        "ui.invalid_input": "无效输入",
        "ui.goodbye": "再见！",
        "ui.select_language": "选择语言：",
        # Tools
        "tool.arch-mirror-optimizer.display_name": "优化 Pacman 镜像源",
        "tool.arch-mirror-optimizer.description": "将中国镜像源添加到 /etc/pacman.d/mirrorlist 顶部",
        "tool.debian-mirror-optimizer.display_name": "优化 APT 镜像源",
        "tool.debian-mirror-optimizer.description": "将 /etc/apt/sources.list 中的镜像源替换为中国镜像源",
        # Messages
        "msg.backup_saved": "备份已保存到 {path}",
        "msg.backup_exists": "备份已存在，已跳过",
        "msg.mirrorlist_updated": "镜像源列表已更新，中国镜像源已添加到顶部",
        "msg.mirrorlist_not_found": "错误：/etc/pacman.d/mirrorlist 不存在",
        "msg.sources_list_not_found": "错误：/etc/apt/sources.list 不存在",
        "msg.sources_list_updated": "sources.list 已更新为中国镜像源",
        "msg.root_required": "需要 root 权限",
    },
}

_current_lang: str | None = None


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def _save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


def get_lang() -> str:
    global _current_lang
    if _current_lang is None:
        cfg = _load_config()
        _current_lang = cfg.get("lang", "en")
    return _current_lang


def set_lang(lang: str) -> None:
    global _current_lang
    _current_lang = lang
    cfg = _load_config()
    cfg["lang"] = lang
    _save_config(cfg)


def t(key: str, **kwargs) -> str:
    lang = get_lang()
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


def tool_display_name(tool) -> str:
    key = f"tool.{tool.name}.display_name"
    return t(key) if TRANSLATIONS["en"].get(key) else tool.display_name


def tool_description(tool) -> str:
    key = f"tool.{tool.name}.description"
    return t(key) if TRANSLATIONS["en"].get(key) else tool.description
