# Repository Guidelines

## Project Structure & Module Organization

`main.py` is the CLI entry point and handles argument parsing, distro detection, menu flow, and virtualenv bootstrap. Shared helpers live in `utils/`: `distro.py` detects Linux distributions, `platform.py` detects OS (`IS_WINDOWS`, `command_exists()`), `shell.py` detects shell type and version, `ui.py` owns terminal prompts and Rich output, `cmd_utils.py` wraps subprocess calls, `sudo_utils.py` handles privileged file operations, `platform_services.py` wraps cross-platform service/package/OS operations, and `i18n.py` stores English/Chinese translations. Tool implementations live in `tools/common/` and inherit from `tools/base.py`; `tools/__init__.py` auto-discovers concrete `Tool` subclasses via `pkgutil.walk_packages()`. Tests live in `tests/`, quick helper scripts in `scripts/`, and project notes in `docs/`.

## Build, Test, and Development Commands

```bash
python main.py
python main.py --list-tools
python main.py --tool mirror-optimizer --lang en
python scripts/update_ai_clis.py
python -m ruff check .
python -m pytest tests/ -v
python tests/check_ui_patterns.py
./tests/remote_test.sh
```

`python main.py` runs the interactive toolbox and bootstraps `.venv` if needed. `--list-tools` verifies discovery. `--tool` runs one tool directly. `scripts/update_ai_clis.py` updates installed npm-based AI CLI tools. `ruff` runs lint checks. `pytest` runs unit tests. `check_ui_patterns.py` enforces menu and prompt conventions. `remote_test.sh` runs SSH-based integration tests and requires configured hosts.

CI runs on Python 3.10–3.13: `ruff check .` → `pytest tests/ -v` → `check_ui_patterns.py`.

## Coding Style & Naming Conventions

Follow PEP 8 with 4-space indentation, type hints for new public functions, and concise docstrings where behavior is not obvious. Line length is 100 (ruff config); `E501` is ignored in `pyproject.toml`. Use snake_case for modules, functions, variables, and tool files, for example `tools/common/backup_restore.py`. Tool `name` values use kebab-case, for example `backup-restore`. Prefer shared helpers from `utils.cmd_utils`, `utils.sudo_utils`, and `utils.ui` over local subprocess, sudo, or prompt implementations. For cross-platform service/package/OS-version code, prefer `utils.platform_services` over hand-rolled `IS_WINDOWS` branches. Use `utils.platform.command_exists(name)` instead of `"where"/"which"` command patterns.

## Adding a New Tool

1. Create `tools/common/<tool_name>.py`
2. Define a class inheriting from `tools.base.Tool` with `name = "kebab-case"`, `platforms`, `distros`
3. Use `prompt_selection()` inside `run()` for menus (use `run_submenu()` helper for standard option → dispatch pattern)
4. Add i18n keys `tool.<name>.display_name` and `tool.<name>.description` in `utils/i18n.py` (both EN and ZH)
5. Create a sibling `tools/common/<name>_translations.py` for tool-specific translations; auto-imported by `tools/__init__.py`
6. The tool is auto-discovered at import time — no registration needed

### Tool Base Class Key Patterns

- **`run_submenu(options, prompt_msg, dispatch)`** — handles the standard option → dispatch boilerplate. Special options: `"all"` runs every handler in dispatch order; `"preview"` returns `None` without dispatch. Use `{"type": "separator", "text_key": ...}` for dividers.
- **`run_dry() -> str | None`** — return a human-readable preview string if the tool supports dry-run; `main.py` shows a Run / Dry-Run / Back sub-prompt before invoking `run()`.
- **`run_all()`** — override for non-destructive batch mode; defaults to calling `run()`. Only tools with `safe_for_run_all = True` run in "Run all".
- **Translation registration** — tool-specific translations must import the `_translations.py` sibling via side-effect import: `from . import <name>_translations  # noqa: F401`.

## Testing Guidelines

Unit tests use `pytest` with `unittest`-style test cases. Name test files `tests/test_<module>.py` and keep tests focused on observable behavior. When adding a tool, include discovery/i18n/UI coverage where practical and run:

```bash
python -m pytest tests/ -v
python tests/check_ui_patterns.py
```

For remote tests, copy `tests/test_config.py.example` and `tests/test_config.sh.example`, or set `TEST_HOSTS`, `TEST_USER`, and `TEST_PASS`.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style prefixes, often scoped: `feat(i18n): ...`, `refactor(tools): ...`, `feat: ...`. Match that pattern and keep each commit focused. Pull requests should describe the user-visible change, list tests run, link related issues, and mention any distro-specific or sudo-requiring behavior. Include screenshots or terminal output when changing interactive UI.

## Security & Configuration Tips

Do not commit local `config.json`, generated `.venv/`, pytest cache, or copied remote test credentials. Tools that edit system files should use `utils.sudo_utils.write_file()` or `copy_file()` and create backups when changing persistent system configuration.

## Critical UI Constraints (Enforced by `tests/check_ui_patterns.py`)

- **Never use raw `input()` in tools** — use `utils.ui` functions.
- **Never use `clear_screen` directly** — `prompt_selection()` handles it.
- **Never hardcode `"back"` strings** — use `BACK_ACTION` constant from `utils.ui`.
- **Never define `_show_menu` methods** — legacy pattern; use `prompt_selection()` inside `run()`.
- **All user-facing strings must go through `t()` for i18n** — add keys to both EN and ZH dicts in `i18n.py`.
- **Render tool names/descriptions via `tool_display_name()` / `tool_description()`** from `utils.i18n`, not `tool.display_name` directly.
