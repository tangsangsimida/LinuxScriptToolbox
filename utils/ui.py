import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich import box

from utils.i18n import t, tool_display_name, tool_description

console = Console()

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


# ── Styled output helpers ───────────────────────────────────────

def print_success(msg: str):
    console.print(f"  [green]✓[/green] {msg}")


def print_error(msg: str):
    console.print(f"  [red]✗[/red] {msg}")


def print_info(msg: str):
    console.print(f"  [blue]ℹ[/blue] {msg}")


def print_warning(msg: str):
    console.print(f"  [yellow]⚠[/yellow] {msg}")


def print_running(name: str):
    console.print()
    console.rule(f"[bold cyan]{name}[/bold cyan]", style="cyan")
    console.print()


def ask(prompt: str, **kwargs) -> str:
    return Prompt.ask(f"  [bold cyan]▸[/bold cyan] {prompt}", **kwargs)
