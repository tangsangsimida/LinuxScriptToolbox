#!/usr/bin/env python3
"""Unit tests for tools/common/device_init.py helpers."""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from tools.common.device_init import _generate_preview


class TestGeneratePreview(TestCase):
    """Regression: ISSUE-027. Separator entries in INIT_OPTIONS lack an 'id'
    key, causing _generate_preview() to crash with KeyError when it iterates
    the options list looking up each step_id.
    """

    def test_generate_preview_does_not_crash_on_separators(self):
        # Should produce a string with step numbers and NOT crash
        result = _generate_preview()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_generate_preview_contains_ssh_service_steps(self):
        result = _generate_preview()
        # The first preview step is "install-ssh", verify its name_key renders
        self.assertIn("SSH", result)

    def test_generate_preview_contains_preview_header(self):
        result = _generate_preview()
        self.assertTrue(
            "Preview" in result or "完整 SSH" in result,
            f"Expected header in preview, got: {result[:80]}",
        )


if __name__ == "__main__":
    unittest_main()
