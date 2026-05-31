import os
import sys
from typing import Optional, Callable, Any

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.spinner import Spinner
from rich.live import Live
from rich import box

from utils.i18n import t, tool_display_name, tool_description

console = Console()

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


def show_menu(tools: list) -> int:
    console.print(f"  [bold]{t('ui.available_tools')}[/bold]")
    console.print()

    if not tools:
        console.print(f"  [dim]{t('ui.no_tools')}[/dim]")
    else:
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.SIMPLE_HEAVY,
            padding=(0, 1),
            expand=False,
        )
        table.add_column("#", style="bold yellow", justify="right")
        table.add_column("Tool", style="bold cyan")
        table.add_column("Description", style="dim")

        for i, tool in enumerate(tools, 1):
            table.add_row(str(i), tool_display_name(tool), tool_description(tool))

        console.print(table)

    console.print()
    console.print(f"  [[bold yellow]a[/bold yellow]] {t('ui.run_all')}    "
                  f"[[bold yellow]l[/bold yellow]] {t('ui.language')}    "
                  f"[[bold yellow]q[/bold yellow]] {t('ui.quit')}")
    console.print()
    return len(tools)


def select_tool(tools: list) -> Optional[int]:
    """Interactive tool selection using questionary.

    Returns:
        Selected tool index (0-based), or special values:
        -1 for "run all", -2 for "language", -3 for "quit"
    """
    if not tools:
        console.print(f"  [dim]{t('ui.no_tools')}[/dim]")
        ask(t("ui.press_enter"))
        return None

    # Fallback for non-TTY environments
    if not IS_TTY:
        return _select_tool_fallback(tools)

    # Build choices with tool info
    choices = []

    # Group tools by category
    groups = _group_tools(tools)
    for group_name, group_tools in groups.items():
        if len(groups) > 1:  # Only show headers if multiple groups
            choices.append(questionary.Separator(f"  {group_name}"))
        for i, tool in group_tools:
            name = tool_display_name(tool)
            desc = tool_description(tool)
            choices.append(
                questionary.Choice(
                    title=f"{name} — {desc}",
                    value=i,
                )
            )

    # Add separator and special actions
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(
        title=f"[{t('ui.run_all')}]",
        value=-1,
    ))
    choices.append(questionary.Choice(
        title=f"[{t('ui.language')}]",
        value=-2,
    ))
    choices.append(questionary.Choice(
        title=f"[{t('ui.quit')}]",
        value=-3,
    ))

    console.print(f"  [dim]{t('ui.arrow_hint')}[/dim]")
    console.print()

    try:
        result = questionary.select(
            message=t("ui.select"),
            choices=choices,
            use_indicator=True,
            style=questionary.Style([
                ("question", "bold"),
                ("answer", "fg:yellow"),
                ("pointer", "fg:cyan bold"),
                ("highlighted", "fg:cyan"),
                ("selected", "fg:green"),
                ("separator", "fg:magenta"),
            ]),
        ).ask()

        return result  # None if user pressed Ctrl+C
    except KeyboardInterrupt:
        return -3


def _group_tools(tools: list) -> dict:
    """Group tools by their distro category."""
    groups = {}
    for i, tool in enumerate(tools):
        # Determine group from tool module path
        module = type(tool).__module__
        if "common" in module:
            group = t("ui.group_common") if "ui.group_common" in _get_translations() else "Common"
        elif "arch" in module:
            group = t("ui.group_arch") if "ui.group_arch" in _get_translations() else "Arch Linux"
        elif "debian" in module:
            group = t("ui.group_debian") if "ui.group_debian" in _get_translations() else "Debian"
        else:
            group = "Other"

        if group not in groups:
            groups[group] = []
        groups[group].append((i, tool))

    return groups


def _get_translations() -> dict:
    """Get current language translations."""
    from utils.i18n import TRANSLATIONS, get_lang
    lang = get_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))


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


def select_option(message: str, options: list[tuple[str, str]], default: str = None) -> Optional[str]:
    """Interactive option selection using questionary.

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
    for value, label in options:
        choices.append(questionary.Choice(title=label, value=value))

    try:
        return questionary.select(
            message=message,
            choices=choices,
            default=default,
            style=questionary.Style([
                ("question", "bold"),
                ("answer", "fg:yellow"),
                ("pointer", "fg:cyan bold"),
                ("highlighted", "fg:cyan"),
                ("selected", "fg:green"),
            ]),
        ).ask()
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
