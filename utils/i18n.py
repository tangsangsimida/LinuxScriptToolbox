"""Internationalization (i18n) module for LinuxScriptToolbox.

This module provides translation support for English and Chinese.
It loads/saves language preferences from config.json and provides
a translation lookup function `t()` for use throughout the project.

LinuxScriptToolbox 的国际化（i18n）模块。

本模块提供英文和中文的翻译支持。
它从 config.json 加载/保存语言偏好设置，并提供翻译查找函数 `t()`
供整个项目使用。

Translation Key Conventions / 翻译键命名规范:
- UI elements / UI 元素: "ui.<element>"
- Tool display names / 工具显示名称: "tool.<tool-name>.display_name"
- Tool descriptions / 工具描述: "tool.<tool-name>.description"
- Messages / 消息: "msg.<category>_<message>"
- Group names / 分组名称: "ui.group_<group>"

Sections / 分区:
- UI: General interface elements / 通用界面元素
- Tools: Tool display names and descriptions / 工具显示名称和描述
- Messages: Tool-specific messages (grouped by tool) / 工具相关消息（按工具分组）
"""

import json
from pathlib import Path

# Path to the project-level config file that persists user language preference / 项目级配置文件路径，用于持久化用户语言偏好
CONFIG_PATH = Path(__file__).parent.parent / "config.json"

# Map of supported language codes to display names / 支持的语言代码到显示名称的映射
SUPPORTED_LANGS = {"en": "English", "zh": "中文"}

# Default language when config is missing, corrupt, or holds an unknown code.
# 配置缺失、损坏或包含未知语言代码时使用的默认语言。
DEFAULT_LANG = "en"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # ============================================================
        # UI Elements / 界面元素
        # ============================================================
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
        "msg.tool_not_available": "Tool '{tool}' exists but is not available for {distro}/{platform}",
        "msg.tool_not_found": "Tool not found: {tool}",
        "msg.tools_available": "Available: {tools}",
        "ui.goodbye": "Goodbye!",
        "ui.back": "Back",
        "ui.select_language": "Select language:",
        "ui.arrow_hint": "Type a number/letter to select, or use ↑↓ to navigate",
        "ui.group_common": "Common",
        "ui.group_system": "System",
        "ui.group_dev": "Development",
        "ui.group_env": "Environment",
        "ui.group_data": "Data",
        "ui.group_fix": "Fixes",
        "ui.group_other": "Other",
        "ui.group_arch": "Arch Linux",
        "ui.group_debian": "Debian/Ubuntu",
        "ui.group_fedora": "Fedora",
        "ui.group_suse": "openSUSE",
        "ui.group_windows": "Windows",
        "ui.platform": "Platform",
        "ui.shell": "Shell",
        "ui.run_all_safe_only": "Run all only runs safe read-only tools; skipped {skipped} tool(s).",
        "ui.no_run_all_tools": "No safe tools are available for Run all.",
        "msg.command_timeout": "Command timed out after {seconds}s: {cmd}",
        "ui.run_tool": "Run",
        "ui.dry_run": "Dry-run",
        "ui.tool_action": "Select action:",
        "msg.installing": "Installing {package}...",
        "msg.install_success": "{package} installed successfully.",
        "msg.install_failed": "Failed to install {package}.",
        "msg.already_installed": "{package} is already installed.",

        # ============================================================
        # Framework-level messages (shared across multiple tools)
        # 框架级消息（跨多个工具共享）
        # ============================================================
    },
    "zh": {
        # ============================================================
        # UI Elements / 界面元素
        # ============================================================
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
        "msg.tool_not_available": "工具 '{tool}' 存在但不适用于 {distro}/{platform}",
        "msg.tool_not_found": "未找到工具：{tool}",
        "msg.tools_available": "可用工具：{tools}",
        "ui.goodbye": "再见！",
        "ui.back": "返回",
        "ui.select_language": "选择语言：",
        "ui.arrow_hint": "输入数字/字母选择，或使用 ↑↓ 导航",
        "ui.group_common": "通用",
        "ui.group_system": "系统",
        "ui.group_dev": "开发",
        "ui.group_env": "环境",
        "ui.group_data": "数据",
        "ui.group_fix": "修复",
        "ui.group_other": "其他",
        "ui.group_arch": "Arch Linux",
        "ui.group_debian": "Debian/Ubuntu",
        "ui.group_fedora": "Fedora",
        "ui.group_suse": "openSUSE",
        "ui.group_windows": "Windows",
        "ui.platform": "平台",
        "ui.shell": "Shell",
        "ui.run_all_safe_only": "“运行全部”仅运行安全的只读工具；已跳过 {skipped} 个工具。",
        "ui.no_run_all_tools": "没有安全的工具可用于“运行全部”。",
        "ui.run_tool": "运行",
        "ui.dry_run": "预览",
        "ui.tool_action": "选择操作：",
        "msg.command_timeout": "命令超时（{seconds}s）：{cmd}",
        "msg.installing": "正在安装 {package}...",
        "msg.install_success": "{package} 安装成功。",
        "msg.install_failed": "{package} 安装失败。",
        "msg.already_installed": "{package} 已安装。",

        # ============================================================
        # Framework-level messages (shared across multiple tools)
        # 框架级消息（跨多个工具共享）
        # ============================================================
    },
}

# Register additional translations for a language.
#
# 为指定语言注册额外的翻译。
#
# Called by per-tool translation modules at import time to populate
# tool-specific translations into the global TRANSLATIONS dict.
#
# 由各工具的翻译模块在导入时调用，将工具特定的翻译填充到全局
# TRANSLATIONS 字典中。
#
# Args:
#     lang: Two-letter language code (e.g. "en", "zh") / 两位语言代码（如 "en"、"zh"）
#     translations: Mapping of translation keys to text / 翻译键到文本的映射
def register_translations(lang: str, translations: dict[str, str]) -> None:
    if lang not in TRANSLATIONS:
        TRANSLATIONS[lang] = {}
    TRANSLATIONS[lang].update(translations)


# Cached current language code; lazily loaded from config on first access / 缓存的当前语言代码；首次访问时从配置文件延迟加载
_current_lang: str | None = None


# Load the project config file and return its contents as a dict.
#
# 加载项目配置文件并以字典形式返回其内容。
#
# This function is intentionally fault-tolerant: any error reading or parsing
# config.json (corrupt JSON, wrong root type, OSError) yields an empty dict
# so that downstream code can keep running with default values.
# 此函数刻意容错：读取或解析 config.json 的任何错误（JSON 损坏、根类型错误、
# OSError）都返回空字典，使下游代码可以继续以默认值运行。
#
# Returns:
#     dict: Parsed config dict, or empty dict on any error.
#     解析后的配置字典，任何错误时返回空字典。
def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


# Save the given config dict to the project config file as pretty-printed JSON.
#
# 将给定的配置字典以格式化 JSON 的形式保存到项目配置文件。
#
# Args:
#     cfg: Config dict to save. / 要保存的配置字典。
def _save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


# Get the current language code, loading from config on first call.
#
# 获取当前语言代码，首次调用时从配置文件加载。
#
# The lang field is validated against SUPPORTED_LANGS; a missing/unknown
# value falls back to DEFAULT_LANG so a corrupt config can never crash the
# caller. Once _current_lang is set, subsequent calls bypass the config.
# lang 字段会对照 SUPPORTED_LANGS 校验；缺失或未知值回退到 DEFAULT_LANG，
# 这样损坏的配置永远不会让调用方崩溃。_current_lang 一旦设置，后续调用
# 直接返回，不再读 config。
#
# Returns:
#     str: Two-letter language code (e.g. "en", "zh").
#     两位语言代码（如 "en"、"zh"）。
def get_lang() -> str:
    global _current_lang
    # Lazy-load: only read config on the first call to avoid repeated file I/O / 延迟加载：仅在首次调用时读取配置，避免重复文件 I/O
    if _current_lang is None:
        cfg = _load_config()
        candidate = cfg.get("lang", DEFAULT_LANG)
        if not isinstance(candidate, str) or candidate not in SUPPORTED_LANGS:
            candidate = DEFAULT_LANG
        _current_lang = candidate
    return _current_lang


# Set the current language and persist the choice to config.json.
#
# 设置当前语言并将选择持久化到 config.json。
#
# Invalid language values are silently coerced to DEFAULT_LANG rather than
# crashing, so an external caller passing a bad value can't break the rest
# of the program. _load_config() is itself fault-tolerant, so this also
# self-heals any prior corruption on the next save.
# 无效的语言值会静默回退到 DEFAULT_LANG 而不是崩溃，外部调用方传入错误值
# 不会破坏程序其余部分。_load_config() 自身已容错，下次保存时会自动
# 覆盖修复先前的损坏。
#
# Args:
#     lang: Two-letter language code (e.g. "en", "zh"). / 两位语言代码（如 "en"、"zh"）。
def set_lang(lang: str) -> None:
    global _current_lang
    if not isinstance(lang, str) or lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    _current_lang = lang
    cfg = _load_config()  # Always returns dict (fault-tolerant). / 始终返回 dict（已容错）
    cfg["lang"] = lang
    _save_config(cfg)


# Look up a translation key in the current language.
#
# 在当前语言中查找翻译键。
#
# Falls back to English if the key is missing in the current language,
# and to the raw key itself if it is missing in English as well.
#
# 如果当前语言缺少该键，则回退到英语；
# 如果英语中也缺少该键，则返回原始键名。
#
# Args:
#     key: Translation key following the naming conventions above.
#          翻译键，遵循上述命名规范。
#     **kwargs: Optional format arguments for str.format() interpolation.
#               可选的 str.format() 格式化参数。
#
# Returns:
#     str: Translated (and optionally formatted) string.
#     翻译后的（可选格式化的）字符串。
def t(key: str, **kwargs) -> str:
    lang = get_lang()
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key)
    if text is None:
        # Fallback to English, then to the raw key as a last resort / 回退到英语，最后回退到原始键名
        text = TRANSLATIONS["en"].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


# Get the localized display name for a tool.
#
# 获取工具的本地化显示名称。
#
# Args:
#     tool: Tool object with `name` and `display_name` attributes.
#           具有 `name` 和 `display_name` 属性的工具对象。
#
# Returns:
#     str: Localized display name if a translation exists, otherwise the
#          tool's own display_name attribute.
#
#     如果存在翻译则返回本地化显示名称，否则返回工具自身的 display_name 属性。
def tool_display_name(tool) -> str:
    key = f"tool.{tool.name}.display_name"
    return t(key) if TRANSLATIONS["en"].get(key) else tool.display_name


# Get the localized description for a tool.
#
# 获取工具的本地化描述。
#
# Args:
#     tool: Tool object with `name` and `description` attributes.
#           具有 `name` 和 `description` 属性的工具对象。
#
# Returns:
#     str: Localized description if a translation exists, otherwise the
#          tool's own description attribute.
#
#     如果存在翻译则返回本地化描述，否则返回工具自身的 description 属性。
def tool_description(tool) -> str:
    key = f"tool.{tool.name}.description"
    return t(key) if TRANSLATIONS["en"].get(key) else tool.description
