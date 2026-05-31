import os
from typing import Optional

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

# ── Layout helpers ──────────────────────────────────────────────

def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def show_header(distro: str):
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

    # Build choices with tool info
    choices = []
    for i, tool in enumerate(tools):
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


# ── Styled output helpers ───────────────────────────────────────

def print_success(msg: str):
    console.print(f"  [green][+][/green] {msg}")


def print_error(msg: str):
    console.print(f"  [red][!][/red] {msg}")


def print_info(msg: str):
    console.print(f"  [blue][i][/blue] {msg}")


def print_warning(msg: str):
    console.print(f"  [yellow][~][/yellow] {msg}")


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
