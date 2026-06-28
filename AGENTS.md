# Repository Guidelines

## Project Structure & Module Organization

`main.py` is the CLI entry point and handles argument parsing, distro detection, menu flow, and virtualenv bootstrap. Shared helpers live in `utils/`: `distro.py` detects Linux distributions, `ui.py` owns terminal prompts and Rich output, `cmd_utils.py` wraps subprocess calls, `sudo_utils.py` handles privileged file operations, and `i18n.py` stores English/Chinese translations. Tool implementations live in `tools/common/` and inherit from `tools/base.py`; `tools/__init__.py` auto-discovers concrete `Tool` subclasses. Tests live in `tests/`, quick helper scripts in `scripts/`, and project notes in `docs/`.

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

## Coding Style & Naming Conventions

Follow PEP 8 with 4-space indentation, type hints for new public functions, and concise docstrings where behavior is not obvious. Use snake_case for modules, functions, variables, and tool files, for example `tools/common/backup_restore.py`. Tool `name` values use kebab-case, for example `backup-restore`. Prefer shared helpers from `utils.cmd_utils`, `utils.sudo_utils`, and `utils.ui` over local subprocess, sudo, or prompt implementations.

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
