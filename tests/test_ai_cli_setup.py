#!/usr/bin/env python3
"""Unit tests for AI CLI setup helpers."""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from tools.common import ai_cli_setup


class TestAiCliSetup(TestCase):
    """Test npm-based AI CLI package definitions and update helpers."""

    def test_mimo_cli_is_available_for_install(self):
        """MiMo Code should be included in the shared npm CLI list."""
        mimo = next(
            opt for opt in ai_cli_setup.AI_CLI_OPTIONS if opt["id"] == "mimo"
        )

        self.assertEqual(mimo["package"], "@mimo-ai/cli")
        self.assertEqual(mimo["name_key"], "msg.ai_cli_mimo")
        self.assertEqual(mimo["desc_key"], "msg.ai_cli_mimo_desc")

    @patch("tools.common.ai_cli_setup._has_npm", return_value=True)
    @patch("tools.common.ai_cli_setup._update_npm_package", return_value=True)
    @patch("tools.common.ai_cli_setup._get_installed_clis")
    def test_update_installed_ai_clis_updates_only_installed(
        self, mock_installed, mock_update, _mock_has_npm
    ):
        """Quick update should update installed CLIs and skip missing ones."""
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

    @patch("tools.common.ai_cli_setup._has_npm", return_value=False)
    def test_update_installed_ai_clis_requires_npm(self, _mock_has_npm):
        """Quick update should fail clearly when npm is missing."""
        self.assertFalse(ai_cli_setup.update_installed_ai_clis())


if __name__ == "__main__":
    unittest_main()
