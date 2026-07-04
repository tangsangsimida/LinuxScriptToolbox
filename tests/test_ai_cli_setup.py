#!/usr/bin/env python3
"""Unit tests for AI CLI setup helpers."""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from tools.common import ai_cli_setup


# Test npm-based AI CLI package definitions and update helpers
class TestAiCliSetup(TestCase):

    # MiMo Code should be included in the shared npm CLI list
    def test_mimo_cli_is_available_for_install(self):
        mimo = next(
            opt for opt in ai_cli_setup.AI_CLI_OPTIONS if opt["id"] == "mimo"
        )

        self.assertEqual(mimo["package"], "@mimo-ai/cli")
        self.assertEqual(mimo["name_key"], "msg.ai_cli_mimo")
        self.assertEqual(mimo["desc_key"], "msg.ai_cli_mimo_desc")

    # Node version parsing should accept normal Node.js version strings
    def test_node_major_version_parsing(self):
        self.assertEqual(ai_cli_setup._parse_node_major("v20.11.1"), 20)
        self.assertEqual(ai_cli_setup._parse_node_major("18.19.0"), 18)
        self.assertIsNone(ai_cli_setup._parse_node_major("not-a-version"))
        self.assertIsNone(ai_cli_setup._parse_node_major(None))

    # AI CLI npm installs require Node.js 18 or newer
    def test_node_version_support_threshold(self):
        self.assertTrue(ai_cli_setup._is_node_version_supported("v18.0.0"))
        self.assertTrue(ai_cli_setup._is_node_version_supported("v20.11.1"))
        self.assertFalse(ai_cli_setup._is_node_version_supported("v16.20.2"))
        self.assertFalse(ai_cli_setup._is_node_version_supported(None))

    # Install flow should stop before npm install when Node.js is too old
    @patch("tools.common.ai_cli_setup._get_node_version", return_value="v16.20.2")
    @patch("tools.common.ai_cli_setup._has_nodejs", return_value=True)
    def test_ensure_nodejs_rejects_old_node(self, _mock_has_nodejs, _mock_version):
        tool = ai_cli_setup.AiCliSetup()

        self.assertFalse(tool._ensure_nodejs("debian"))

    # Quick update should update installed CLIs and skip missing ones
    @patch("tools.common.ai_cli_setup._has_npm", return_value=True)
    @patch("tools.common.ai_cli_setup._update_npm_package", return_value=True)
    @patch("tools.common.ai_cli_setup._get_installed_clis")
    def test_update_installed_ai_clis_updates_only_installed(
        self, mock_installed, mock_update, _mock_has_npm
    ):
        mock_installed.return_value = [
            {
                "id": "mimo",
                "name_key": "msg.ai_cli_mimo",
                "desc_key": "msg.ai_cli_mimo_desc",
                "package": "@mimo-ai/cli",
            }
        ]

        result = ai_cli_setup.update_installed_ai_clis()

        self.assertTrue(result)
        mock_update.assert_called_once_with("@mimo-ai/cli", "MiMo Code")

    # Quick update should fail clearly when npm is missing
    @patch("tools.common.ai_cli_setup._has_npm", return_value=False)
    def test_update_installed_ai_clis_requires_npm(self, _mock_has_npm):
        self.assertFalse(ai_cli_setup.update_installed_ai_clis())

    # Alibaba Cloud Linux should be a recognized distro for the tool,
    # so the menu does not filter it out, and the auto-install path can
    # pick the right package list.
    def test_alinux_is_a_supported_distro(self):
        self.assertIn("alinux", ai_cli_setup.AiCliSetup.distros)

    # Node.js install should look up the package list by distro key,
    # including alinux (RHEL family), so users on alinux can hit the
    # auto-install path instead of seeing 'unknown distro'.
    def test_nodejs_pkg_list_covers_alinux(self):
        self.assertIn("alinux", ai_cli_setup.DISTRO_NODEJS_PKGS)
        self.assertEqual(ai_cli_setup.DISTRO_NODEJS_PKGS["alinux"], ["nodejs", "npm"])

    # On Linux, npm install -g should be prefixed with sudo so it can write
    # to /usr/local/lib/node_modules. Mock both the existence check and the
    # run_verbose call to verify the command shape.
    @patch("tools.common.ai_cli_setup.run_verbose")
    @patch("tools.common.ai_cli_setup._is_npm_package_installed", return_value=False)
    def test_install_npm_package_uses_sudo_on_linux(
        self, mock_installed, mock_run_verbose
    ):
        # Force IS_WINDOWS=False for the duration of this test
        with patch.object(ai_cli_setup, "IS_WINDOWS", False):
            mock_run_verbose.return_value = 0
            result = ai_cli_setup._install_npm_package("@mimo-ai/cli", "MiMo Code")

            self.assertTrue(result)
            mock_run_verbose.assert_called_once_with(
                ["sudo", "npm", "install", "-g", "@mimo-ai/cli"]
            )

    # On Windows, no sudo prefix — npm install -g runs as-is.
    @patch("tools.common.ai_cli_setup.run_verbose")
    @patch("tools.common.ai_cli_setup._is_npm_package_installed", return_value=False)
    def test_install_npm_package_skips_sudo_on_windows(
        self, mock_installed, mock_run_verbose
    ):
        with patch.object(ai_cli_setup, "IS_WINDOWS", True):
            mock_run_verbose.return_value = 0
            result = ai_cli_setup._install_npm_package("@mimo-ai/cli", "MiMo Code")

            self.assertTrue(result)
            mock_run_verbose.assert_called_once_with(
                ["npm", "install", "-g", "@mimo-ai/cli"]
            )

    # If npm install exits non-zero, the helper should return False and not
    # raise — the user sees a friendly error via t() / print_error.
    @patch("tools.common.ai_cli_setup.run_verbose")
    @patch("tools.common.ai_cli_setup._is_npm_package_installed", return_value=False)
    def test_install_npm_package_returns_false_on_failure(
        self, mock_installed, mock_run_verbose
    ):
        with patch.object(ai_cli_setup, "IS_WINDOWS", False):
            mock_run_verbose.return_value = 1  # EACCES / generic failure
            result = ai_cli_setup._install_npm_package("@mimo-ai/cli", "MiMo Code")
            self.assertFalse(result)

    # If the package is already installed, skip the install call entirely.
    @patch("tools.common.ai_cli_setup.run_verbose")
    @patch("tools.common.ai_cli_setup._is_npm_package_installed", return_value=True)
    def test_install_npm_package_skips_when_already_installed(
        self, mock_installed, mock_run_verbose
    ):
        result = ai_cli_setup._install_npm_package("@mimo-ai/cli", "MiMo Code")
        self.assertTrue(result)
        mock_run_verbose.assert_not_called()

    # On Linux, _update_npm_package should also use sudo for parity with install.
    @patch("tools.common.ai_cli_setup.run_verbose")
    @patch("tools.common.ai_cli_setup._is_npm_package_installed", return_value=True)
    def test_update_npm_package_uses_sudo_on_linux(
        self, mock_installed, mock_run_verbose
    ):
        with patch.object(ai_cli_setup, "IS_WINDOWS", False):
            mock_run_verbose.return_value = 0
            result = ai_cli_setup._update_npm_package("@mimo-ai/cli", "MiMo Code")

            self.assertTrue(result)
            mock_run_verbose.assert_called_once_with(
                ["sudo", "npm", "install", "-g", "@mimo-ai/cli@latest"]
            )


if __name__ == "__main__":
    unittest_main()
