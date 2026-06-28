"""UI utility module for terminal-based interactive interfaces.

终端交互界面工具模块，提供选择菜单、进度条、提示框等 UI 组件。
"""

import os
import sys
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.spinner import Spinner
from rich.live import Live
from rich import box

from utils.i18n import t, tool_display_name, tool_description

console = Console()  # Global Rich console instance / 全局 Rich 控制台实例

# ── UI Constants ───────────────────────────────────────────────
BACK_ACTION = "back"  # Constant for back/cancel action / 返回操作常量
CANCEL_ACTION = None  # Constant for cancel (Ctrl+C, ESC) / 取消操作常量（Ctrl+C、ESC）

# ── Theme configuration ────────────────────────────────────────
THEME = {
    "primary": "cyan",       # Primary color for main UI elements / 主要 UI 元素颜色
    "secondary": "magenta",  # Secondary color for accents / 次要强调颜色
    "accent": "yellow",      # Accent color for highlights / 高亮强调颜色
    "success": "green",      # Success state color / 成功状态颜色
    "error": "red",          # Error state color / 错误状态颜色
    "warning": "yellow",     # Warning state color / 警告状态颜色
    "info": "blue",          # Information state color / 信息状态颜色
    "dim": "dim",            # Dimmed/muted text style / 暗淡/静音文本样式
    "border": "bright_blue", # Border color for panels / 面板边框颜色
}

# ── Semantic markers (color-coded) ─────────────────────────────
MARKERS = {
    "success": "[green][+][/green]",   # Success marker / 成功标记
    "error": "[red][!][/red]",         # Error marker / 错误标记
    "info": "[blue][i][/blue]",        # Info marker / 信息标记
    "warning": "[yellow][~][/yellow]", # Warning marker / 警告标记
    "running": "[cyan][*][/cyan]",     # Running/active marker / 运行中标记
}

# ── Terminal capability detection ──────────────────────────────
def _is_tty() -> bool:
    """Check if stdout is a real TTY (supports ANSI).

    检查标准输出是否为真实 TTY（支持 ANSI 转义序列）。
    """
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _get_terminal_width() -> int:
    """Get terminal width, with fallback.

    获取终端宽度，失败时返回默认值 80。
    """
    try:
        return console.size.width
    except Exception:
        return 80  # Fallback width / 回退默认宽度

IS_TTY = _is_tty()            # Whether stdout is a TTY / 标准输出是否为 TTY
TERM_WIDTH = _get_terminal_width()  # Detected terminal width / 检测到的终端宽度

# ── Questionary with key bindings ────────────────────────────────

# Questionary custom style / Questionary 自定义样式
_questionary_style = questionary.Style([
    ("question", "bold"),          # Prompt text style / 提示文本样式
    ("answer", "fg:yellow"),       # Answer text color / 回答文本颜色
    ("pointer", "fg:cyan bold"),   # Pointer/marker style / 指针标记样式
    ("highlighted", "fg:cyan"),    # Highlighted item style / 高亮选项样式
    ("selected", "fg:green"),      # Selected item style / 已选选项样式
    ("separator", "fg:magenta"),   # Separator line style / 分隔线样式
])


def _select_with_keys(message: str, choices: list, char_map: dict[str, int]):
    """questionary.select() with digit/letter key bindings.

    Pressing a key in char_map immediately returns the mapped value.
    Arrow keys and Enter work as normal through questionary.

    为 questionary.select() 添加数字/字母快捷键绑定。
    按下 char_map 中的键会立即返回对应的值，方向键和回车键按 questionary 默认行为工作。

    Args:
        message: Prompt message / 提示消息。
        choices: List of questionary.Choice / Separator / questionary 选项/分隔符列表。
        char_map: {"1": 0, "2": 1, ..., "q": -3} / 快捷键到值的映射字典。
    """
    session = questionary.select(
        message=message,
        choices=choices,
        use_indicator=True,
        style=_questionary_style,
    )

    def _make_handler(val):
        """Create a key handler that exits with the given value.

        创建一个按键处理器，按下时以指定值退出应用。
        """
        def handler(event):
            event.app.exit(result=val)
        return handler

    # Add digit/letter bindings to the existing key bindings / 向现有按键绑定中添加数字/字母快捷键
    kb = session.application.key_bindings
    for char, val in char_map.items():
        kb.add(char, eager=True)(_make_handler(val))

    return session.unsafe_ask()

# ── Layout helpers ──────────────────────────────────────────────

def clear_screen():
    """Clear the terminal screen.

    清除终端屏幕。
    """
    os.system("clear" if os.name == "posix" else "cls")


def show_header(distro: str, lang: str = None, platform: str = None, shell: str = None):
    """Display the application header with system information.

    显示应用程序标题栏及系统信息。

    Args:
        distro: Linux distribution name / Linux 发行版名称。
        lang: Current language setting / 当前语言设置。
        platform: System platform info / 系统平台信息。
        shell: Current shell name / 当前 Shell 名称。
    """
    clear_screen()
    title = Text("LinuxScriptToolbox", style="bold cyan")
    subtitle = Text(t("ui.detected", distro=distro), style="dim")
    panel = Panel(
        subtitle,
        title=title,
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(0, 2),
    )
    console.print(panel)

    # Status line: build a summary of detected system info / 状态行：构建检测到的系统信息摘要
    status_parts = [f"Distro: {distro}"]
    if platform:
        status_parts.append(f"Platform: {platform}")
    if shell:
        status_parts.append(f"Shell: {shell}")
    if lang:
        status_parts.append(f"Lang: {lang}")
    status_parts.append(f"Width: {TERM_WIDTH}")
    status_line = " | ".join(status_parts)
    console.print(f"  [dim]{status_line}[/dim]")
    console.print()



def _build_tool_choices(tools: list) -> tuple[list, dict[str, int]]:
    """Build questionary choices and key map for the tool menu.

    为工具菜单构建 questionary 选项列表和快捷键映射。
    """
    choices = []
    char_map: dict[str, int] = {}
    num = 0

    groups = _group_tools(tools)
    for group_name, group_tools in groups.items():
        if len(groups) > 1:
            choices.append(questionary.Separator(f"  {group_name}"))
        for i, tool in group_tools:
            num += 1
            name = tool_display_name(tool)
            desc = tool_description(tool)
            choices.append(
                questionary.Choice(title=f"[{num}] {name} — {desc}", value=i)
            )
            char_map[str(num)] = i

    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title=f"[0/a] {t('ui.run_all')}", value=-1))
    choices.append(questionary.Choice(title=f"[l] {t('ui.language')}", value=-2))
    choices.append(questionary.Choice(title=f"[q] {t('ui.quit')}", value=-3))
    char_map["0"] = -1
    char_map["a"] = -1
    char_map["l"] = -2
    char_map["q"] = -3

    return choices, char_map


def select_tool(tools: list) -> Optional[int]:
    """Interactive tool selection — supports both arrow keys and direct input.

    交互式工具选择 —— 支持方向键浏览和快捷键直接输入。

    Returns:
        Selected tool index (0-based), or special values:
        -1 for "run all", -2 for "language", -3 for "quit" /
        选中的工具索引（从 0 开始），或特殊值：-1 表示"全部运行"，-2 表示"语言"，-3 表示"退出"。
    """
    if not tools:
        console.print(f"  [dim]{t('ui.no_tools')}[/dim]")
        ask(t("ui.press_enter"))
        return None

    if not IS_TTY:
        return _select_tool_fallback(tools)

    choices, char_map = _build_tool_choices(tools)

    console.print(f"  [dim]{t('ui.arrow_hint')}[/dim]")
    console.print()

    try:
        return _select_with_keys(t("ui.select"), choices, char_map)
    except KeyboardInterrupt:
        return -3


def _group_tools(tools: list) -> dict:
    """Group tools by their distro category.

    按发行版类别对工具进行分组。
    """
    groups = {}
    for i, tool in enumerate(tools):
        module = type(tool).__module__
        if "common" in module:
            group = t("ui.group_common")
        elif "arch" in module:
            group = t("ui.group_arch")
        elif "debian" in module:
            group = t("ui.group_debian")
        elif "windows" in module:
            group = t("ui.group_windows")
        else:
            group = "Other"

        if group not in groups:
            groups[group] = []
        groups[group].append((i, tool))

    return groups


def _select_tool_fallback(tools: list) -> Optional[int]:
    """Fallback selection for non-TTY environments (plain input).

    非 TTY 环境下的回退选择方案（使用纯文本输入）。
    """
    console.print(f"  [bold]{t('ui.available_tools')}[/bold]")
    console.print()

    for i, tool in enumerate(tools, 1):
        name = tool_display_name(tool)
        desc = tool_description(tool)
        console.print(f"  [{i}] {name} — {desc}")

    console.print()
    console.print(f"  [a] {t('ui.run_all')}  [l] {t('ui.language')}  [q] {t('ui.quit')}")
    console.print()

    try:
        choice = input(f"  {t('ui.select')}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return -3

    if choice == "q":
        return -3
    elif choice == "l":
        return -2
    elif choice == "a":
        return -1
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(tools):
                return idx
        except ValueError:
            pass

    return None


# ── Styled output helpers ───────────────────────────────────────

def print_success(msg: str):
    """Print a success message with a green marker.

    打印带绿色标记的成功消息。
    """
    console.print(f"  {MARKERS['success']} {msg}")


def print_error(msg: str):
    """Print an error message with a red marker.

    打印带红色标记的错误消息。
    """
    console.print(f"  {MARKERS['error']} {msg}")


def print_info(msg: str):
    """Print an informational message with a blue marker.

    打印带蓝色标记的信息消息。
    """
    console.print(f"  {MARKERS['info']} {msg}")


def print_warning(msg: str):
    """Print a warning message with a yellow marker.

    打印带黄色标记的警告消息。
    """
    console.print(f"  {MARKERS['warning']} {msg}")


def print_running(name: str):
    """Print a running indicator with a horizontal rule.

    打印运行指示器，带水平分隔线。
    """
    console.print()
    console.rule(f"[bold cyan]{name}[/bold cyan]", style="cyan")
    console.print()


def show_tool_header(name: str):
    """Clear screen and display a tool header with a horizontal rule.

    清屏并显示带水平分隔线的工具标题。

    Args:
        name: Tool name to display / 要显示的工具名称。
    """
    clear_screen()
    console.rule(f"[bold cyan]{name}[/bold cyan]", style="cyan")
    console.print()


def ask(prompt: str, **kwargs) -> str:
    """Display a styled prompt and return user input.

    显示带样式的提示符并返回用户输入。

    Args:
        prompt: Prompt text to display / 要显示的提示文本。
        **kwargs: Additional arguments passed to Rich Prompt.ask / 传递给 Rich Prompt.ask 的额外参数。

    Returns:
        User input string / 用户输入的字符串。
    """
    return Prompt.ask(f"  [bold cyan]▸[/bold cyan] {prompt}", **kwargs)


def confirm(message: str, default: bool = False) -> bool:
    """Yes/no confirmation dialog.

    是/否确认对话框。

    Args:
        message: Question to ask / 要询问的问题。
        default: Default answer (True=yes, False=no) / 默认回答（True=是，False=否）。

    Returns:
        True if user confirmed, False otherwise / 用户确认返回 True，否则返回 False。
    """
    if not IS_TTY:
        suffix = " [Y/n]" if default else " [y/N]"
        try:
            choice = input(f"  {message}{suffix}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        if not choice:
            return default
        return choice in ("y", "yes")

    try:
        return questionary.confirm(message, default=default).ask() or False
    except KeyboardInterrupt:
        return False


def select_option(message: str, options: list[tuple[str, str]], default: str = None) -> Optional[str]:
    """Interactive option selection — supports both arrow keys and direct input.

    交互式选项选择 —— 支持方向键浏览和快捷键直接输入。

    Args:
        message: Prompt message / 提示消息。
        options: List of (value, label) tuples / (值, 标签) 元组列表。
        default: Default value (optional) / 默认值（可选）。

    Returns:
        Selected value, or None if cancelled / 选中的值，取消时返回 None。
    """
    if not IS_TTY:
        return _select_option_fallback(message, options, default)

    choices = []
    char_map: dict[str, int] = {}
    for i, (value, label) in enumerate(options, 1):
        choices.append(questionary.Choice(title=label, value=value))
        char_map[str(i)] = value

    try:
        return _select_with_keys(message, choices, char_map)
    except KeyboardInterrupt:
        return None


def _select_option_fallback(message: str, options: list[tuple[str, str]], default: str = None) -> Optional[str]:
    """Fallback for non-TTY environments.

    非 TTY 环境下的回退选项选择方案。

    Args:
        message: Prompt message / 提示消息。
        options: List of (value, label) tuples / (值, 标签) 元组列表。
        default: Default value (optional) / 默认值（可选）。

    Returns:
        Selected value, or None if cancelled / 选中的值，取消时返回 None。
    """
    console.print(f"\n  [bold]{message}[/bold]\n")
    for i, (value, label) in enumerate(options, 1):
        marker = " (default)" if value == default else ""
        console.print(f"  [{i}] {label}{marker}")
    console.print()

    try:
        choice = input(f"  {t('ui.select')}").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if not choice and default:
        return default

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            return options[idx][0]
    except ValueError:
        pass

    return None


def prompt_selection(message: str, options: list[dict], show_back: bool = True) -> Optional[str]:
    """Unified sub-menu selection for tool classes.

    统一的子菜单选择函数，供工具类使用。

    Args:
        message: Prompt message / 提示消息。
        options: List of dicts with 'id', 'name_key', 'desc_key' keys /
                 包含 'id'、'name_key'、'desc_key' 键的字典列表。
        show_back: Whether to show "Back" option (returns BACK_ACTION) /
                   是否显示"返回"选项（返回 BACK_ACTION）。

    Returns:
        Selected option id, BACK_ACTION if user chose back, or CANCEL_ACTION if cancelled /
        选中的选项 id，用户选择返回时返回 BACK_ACTION，取消时返回 CANCEL_ACTION。
    """
    # Build choices and key map / 构建选项列表和快捷键映射
    choices = []
    char_map: dict[str, int] = {}

    for i, opt in enumerate(options, 1):
        name = t(opt["name_key"])
        desc = t(opt.get("desc_key", "")) if opt.get("desc_key") else ""
        label = f"[{i}] {name} — {desc}" if desc else f"[{i}] {name}"
        choices.append(questionary.Choice(title=label, value=opt["id"]))
        char_map[str(i)] = opt["id"]

    if show_back:
        choices.append(questionary.Choice(title=f"[0] {t('ui.back')}", value=BACK_ACTION))
        char_map["0"] = BACK_ACTION

    if not IS_TTY:
        fallback_options = [(opt["id"], f"[{i}] {t(opt['name_key'])}") for i, opt in enumerate(options, 1)]
        if show_back:
            fallback_options.append((BACK_ACTION, f"[0] {t('ui.back')}"))
        return _select_option_fallback(message, fallback_options)

    try:
        return _select_with_keys(message, choices, char_map)
    except KeyboardInterrupt:
        return CANCEL_ACTION


def press_any_key(prompt: str = None):
    """Wait for user to press any key (or Enter).

    等待用户按下任意键（或回车键）。

    Args:
        prompt: Prompt text to display (defaults to localized message) /
                要显示的提示文本（默认为本地化消息）。
    """
    if prompt is None:
        prompt = t("ui.press_enter")

    if IS_TTY:
        try:
            questionary.press_any_key_to_continue(prompt).ask()
        except KeyboardInterrupt:
            pass
    else:
        try:
            input(f"  {prompt}")
        except (EOFError, KeyboardInterrupt):
            pass


# ── Progress & Spinner helpers ──────────────────────────────────

def create_progress(**kwargs) -> Progress:
    """Create a Rich progress bar with sensible defaults.

    创建带有合理默认配置的 Rich 进度条。

    Usage / 用法:
        with create_progress() as progress:
            task = progress.add_task("Downloading...", total=100)
            while not progress.finished:
                progress.update(task, advance=1)
                do_work()
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        **kwargs,
    )


def create_spinner(text: str) -> Spinner:
    """Create a spinner for indeterminate-length tasks.

    为不确定时长的任务创建加载动画。

    Args:
        text: Text to display next to the spinner / 加载动画旁显示的文本。

    Usage / 用法:
        spinner = create_spinner("Installing...")
        with Live(spinner, console=console):
            do_long_task()
    """
    return Spinner("dots", text=f"[cyan]{text}[/cyan]")


def run_with_spinner(task_func, description: str):
    """Run a function with a spinner showing progress.

    在加载动画下运行函数。

    Args:
        task_func: Callable to execute / 要执行的可调用对象。
        description: Text to show next to spinner / 加载动画旁显示的文本。

    Returns:
        The return value of task_func / task_func 的返回值。
    """
    spinner = create_spinner(description)
    with Live(spinner, console=console, refresh_per_second=10):
        result = task_func()
    return result


def run_with_progress(items: list, task_func, description: str = "Processing..."):
    """Run a function for each item with a progress bar.

    使用进度条对每个项目执行函数。

    Args:
        items: List of items to process / 要处理的项目列表。
        task_func: Callable(item, progress, task) for each item /
                   对每个项目调用的 Callable(item, progress, task)。
        description: Text to show in progress bar / 进度条中显示的文本。

    Returns:
        List of results from task_func / task_func 的结果列表。
    """
    results = []
    with create_progress() as progress:
        task = progress.add_task(description, total=len(items))
        for item in items:
            result = task_func(item, progress, task)
            results.append(result)
            progress.advance(task)
    return results
