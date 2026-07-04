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

    Note: setUp explicitly sets i18n to English so assertions on the preview
    text are deterministic regardless of the runtime env's config.json.
    注意：setUp 显式设置 i18n 为英文，使预览文本的断言不受运行环境
    config.json 语言设置影响。
    """

    def setUp(self):
        from utils.i18n import set_lang
        set_lang("en")

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
            "DRY-RUN" in result or "Preview" in result,
            f"Expected header in preview, got: {result[:80]}",
        )


if __name__ == "__main__":
    unittest_main()
