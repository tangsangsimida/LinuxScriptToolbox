# LinuxScriptToolbox

A Python CLI toolbox that auto-detects your Linux distribution and presents a menu of system administration tools specific to that distro.

## Features

- **Auto-detection**: Automatically detects your Linux distribution (Arch, Debian, Fedora, openSUSE, etc.)
- **Interactive menus**: Arrow-key navigation with fallback for non-interactive terminals
- **Cross-distro tools**: Tools that work across multiple Linux distributions
- **i18n support**: English and Chinese interfaces
- **Extensible**: Easy to add new tools via plugin architecture

## Installation

### Prerequisites

- Python 3.10+
- Linux system with `/etc/os-release`

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/LinuxScriptToolbox.git
cd LinuxScriptToolbox

# Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Interactive Menu

```bash
python main.py
```

### List Available Tools

```bash
python main.py --list-tools
```

### Run a Specific Tool

```bash
python main.py --tool mirror-optimizer
python main.py --tool device-init
python main.py --tool dev-tools
```

### Set Language

```bash
python main.py --lang en  # English
python main.py --lang zh  # 中文
```

## Available Tools

### Common Tools (Cross-distro)

| Tool | Description |
|------|-------------|
| **Mirror Optimizer** | Replace package manager mirrors with China mirrors (supports pacman, apt, dnf, zypper) |
| **Device Initialize** | Set up SSH access (install, password, config, firewall) and python alias |
| **Dev Tools Setup** | Quick install embedded toolchains (ARM GCC, RISC-V GCC) |
| **Quick Fixes** | One-click fixes for common Linux software issues |
| **Shorin Setup** | Clone and run shorin-arch-setup for desktop environment configuration |
| **AI CLI Setup** | One-click install AI coding assistant CLIs (Claude Code, Codex, Gemini, OpenCode) |

### Supported Distributions

| Distribution | Status |
|--------------|--------|
| Arch Linux | ✅ Full support |
| Debian/Ubuntu | ✅ Full support |
| Fedora | ⚠️ Partial (ai-cli-setup, mirror-optimizer) |
| openSUSE | ⚠️ Partial (ai-cli-setup, mirror-optimizer) |
| Others | ⚠️ Basic support (mirror-optimizer only) |

## Project Structure

```
LinuxScriptToolbox/
├── main.py                  # Entry point
├── distro.py                # Distribution detection
├── ui.py                    # Terminal UI utilities
├── tools/
│   ├── base.py              # Abstract Tool class
│   ├── __init__.py          # Tool auto-discovery
│   └── common/              # Cross-distro tools
│       ├── mirror_optimizer.py
│       ├── device_init.py
│       ├── dev_tools.py
│       ├── quick_fixes.py
│       ├── shorin_setup.py
│       └── ai_cli_setup.py
├── utils/
│   ├── cmd_utils.py         # Subprocess helpers
│   ├── sudo_utils.py        # Privileged I/O wrappers
│   └── i18n.py              # Internationalization
├── tests/
│   ├── test_ui.py           # UI unit tests
│   ├── test_config.py.example  # Test config template
│   └── remote_test.sh       # Integration tests
└── docs/
    └── config_merged.md     # Configuration notes
```

## Adding a New Tool

1. Create `tools/common/<tool_name>.py`
2. Define a class inheriting from `tools.base.Tool`:
   ```python
   from tools.base import Tool

   class MyTool(Tool):
       name = "my-tool"
       display_name = "My Tool"
       description = "Description of my tool"
       distros = ["arch", "debian", "fedora", "suse"]

       def run(self) -> bool | None:
           # Implementation here
           return True
   ```
3. Add translations in `utils/i18n.py` for `tool.<name>.display_name` and `tool.<name>.description`
4. The tool will be automatically discovered at import time

## Testing

### Unit Tests

```bash
# Run all unit tests
python -m pytest tests/ -v

# Run UI tests only
python -m pytest tests/test_ui.py -v
```

### Integration Tests

Integration tests run over SSH against remote VMs. Credentials are resolved in this order:

1. **Environment variables** (recommended for CI/CD)
2. Config files (for local development)

#### Option A: Environment Variables (Recommended)

```bash
export TEST_HOSTS="192.168.1.100,192.168.1.101"
export TEST_USER="dennis"
export TEST_PASS="dennis"

./tests/remote_test.sh
```

#### Option B: Config Files

```bash
# Copy example configs
cp tests/test_config.py.example tests/test_config.py
cp tests/test_config.sh.example tests/test_config.sh

# Edit with your credentials
vim tests/test_config.py
```

#### Running Tests

```bash
./tests/remote_test.sh                    # All tests
./tests/remote_test.sh ssh-init           # SSH init test only
./tests/remote_test.sh dev-tools          # Dev tools test only
./tests/remote_test.sh mirror-opt         # Mirror optimizer test only
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings for public functions
- Run `python tests/check_ui_patterns.py` to verify UI patterns

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Rich](https://github.com/Textualize/rich) for terminal UI
- [questionary](https://github.com/tmbo/questionary) for interactive prompts
- [shorin-arch-setup](https://github.com/SHORiN-KiWATA/shorin-arch-setup) for desktop environment scripts
