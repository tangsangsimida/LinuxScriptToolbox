import os
import sys
from typing import Optional

import questionary
from prompt_toolkit.keys import Keys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.spinner import Spinner
from rich.live import Live
from rich import box

from utils.i18n import t, tool_display_name, tool_description

console = Console()

# ── UI Constants ───────────────────────────────────────────────
BACK_ACTION = "back"  # Constant for back/cancel action
CANCEL_ACTION = None  # Constant for cancel (Ctrl+C, ESC)

# ── Theme configuration ────────────────────────────────────────
THEME = {
    "primary": "cyan",
    "secondary": "magenta",
    "accent": "yellow",
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "blue",
    "dim": "dim",
    "border": "bright_blue",
}

# ── Semantic markers (color-coded) ─────────────────────────────
MARKERS = {
    "success": "[green][+][/green]",
    "error": "[red][!][/red]",
    "info": "[blue][i][/blue]",
    "warning": "[yellow][~][/yellow]",
    "running": "[cyan][*][/cyan]",
}

# ── Terminal capability detection ──────────────────────────────
def _is_tty() -> bool:
    """Check if stdout is a real TTY (supports ANSI)."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _get_terminal_width() -> int:
    """Get terminal width, with fallback."""
    try:
        return console.size.width
    except Exception:
        return 80

IS_TTY = _is_tty()
TERM_WIDTH = _get_terminal_width()

# ── Questionary with key bindings ────────────────────────────────

_questionary_style = questionary.Style([
    ("question", "bold"),
    ("answer", "fg:yellow"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan"),
    ("selected", "fg:green"),
    ("separator", "fg:magenta"),
])


def _select_with_keys(message: str, choices: list, char_map: dict[str, int]):
    """questionary.select() with digit/letter key bindings.

    Pressing a key in char_map immediately returns the mapped value.
    Arrow keys and Enter work as normal through questionary.

    Args:
        message: Prompt message
        choices: List of questionary.Choice / Separator
        char_map: {"1": 0, "2": 1, ..., "q": -3}
    """
    session = questionary.select(
        message=message,
        choices=choices,
        use_indicator=True,
        style=_questionary_style,
    )

    def _make_handler(val):
        def handler(event):
            event.app.exit(result=val)
        return handler

    # Add digit/letter bindings to the existing key bindings
    kb = session.application.key_bindings
    for char, val in char_map.items():
        kb.add(char, eager=True)(_make_handler(val))

    return session.unsafe_ask()

# ── Layout helpers ──────────────────────────────────────────────

def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def show_header(distro: str, lang: str = None):
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

    # Status line
    status_parts = [f"Distro: {distro}"]
    if lang:
        status_parts.append(f"Lang: {lang}")
    status_parts.append(f"Width: {TERM_WIDTH}")
    status_line = " | ".join(status_parts)
    console.print(f"  [dim]{status_line}[/dim]")
    console.print()



def _build_tool_choices(tools: list) -> tuple[list, dict[str, int]]:
    """Build questionary choices and key map for the tool menu."""
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

    Returns:
        Selected tool index (0-based), or special values:
        -1 for "run all", -2 for "language", -3 for "quit"
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
    """Group tools by their distro category."""
    groups = {}
    for i, tool in enumerate(tools):
        module = type(tool).__module__
        if "common" in module:
            group = t("ui.group_common")
        elif "arch" in module:
            group = t("ui.group_arch")
        elif "debian" in module:
            group = t("ui.group_debian")
        else:
            group = "Other"

        if group not in groups:
            groups[group] = []
        groups[group].append((i, tool))

    return groups


def _select_tool_fallback(tools: list) -> Optional[int]:
    """Fallback selection for non-TTY environments (plain input)."""
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
    console.print(f"  {MARKERS['success']} {msg}")


def print_error(msg: str):
    console.print(f"  {MARKERS['error']} {msg}")


def print_info(msg: str):
    console.print(f"  {MARKERS['info']} {msg}")


def print_warning(msg: str):
    console.print(f"  {MARKERS['warning']} {msg}")


def print_running(name: str):
    console.print()
    console.rule(f"[bold cyan]{name}[/bold cyan]", style="cyan")
    console.print()


def show_tool_header(name: str):
    clear_screen()
    console.rule(f"[bold cyan]{name}[/bold cyan]", style="cyan")
    console.print()


def ask(prompt: str, **kwargs) -> str:
    return Prompt.ask(f"  [bold cyan]▸[/bold cyan] {prompt}", **kwargs)


def confirm(message: str, default: bool = False) -> bool:
    """Yes/no confirmation dialog.

    Args:
        message: Question to ask
        default: Default answer (True=yes, False=no)

    Returns:
        True if user confirmed, False otherwise
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

    Args:
        message: Prompt message
        options: List of (value, label) tuples
        default: Default value (optional)

    Returns:
        Selected value, or None if cancelled
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
    """Fallback for non-TTY environments."""
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

    Args:
        message: Prompt message
        options: List of dicts with 'id', 'name_key', 'desc_key' keys
        show_back: Whether to show "Back" option (returns BACK_ACTION)

    Returns:
        Selected option id, BACK_ACTION if user chose back, or CANCEL_ACTION if cancelled
    """
    # Build choices and key map
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
    """Wait for user to press any key (or Enter)."""
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

    Usage:
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

    Usage:
        spinner = create_spinner("Installing...")
        with Live(spinner, console=console):
            do_long_task()
    """
    return Spinner("dots", text=f"[cyan]{text}[/cyan]")


def run_with_spinner(task_func, description: str):
    """Run a function with a spinner showing progress.

    Args:
        task_func: Callable to execute
        description: Text to show next to spinner

    Returns:
        The return value of task_func
    """
    spinner = create_spinner(description)
    with Live(spinner, console=console, refresh_per_second=10):
        result = task_func()
    return result


def run_with_progress(items: list, task_func, description: str = "Processing..."):
    """Run a function for each item with a progress bar.

    Args:
        items: List of items to process
        task_func: Callable(item, progress, task) for each item
        description: Text to show in progress bar

    Returns:
        List of results from task_func
    """
    results = []
    with create_progress() as progress:
        task = progress.add_task(description, total=len(items))
        for item in items:
            result = task_func(item, progress, task)
            results.append(result)
            progress.advance(task)
    return results
