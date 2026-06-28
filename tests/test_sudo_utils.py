#!/usr/bin/env python3
"""Unit tests for utils/sudo_utils.py."""

import sys
import tempfile
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


# Test sudo-aware file helper behavior
class TestSudoUtils(TestCase):

    def test_need_sudo_uses_parent_for_missing_path(self):
        from utils.sudo_utils import need_sudo

        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "new-file"
            self.assertFalse(need_sudo(missing))

    @patch("utils.sudo_utils._needs_sudo_to_read", return_value=True)
    @patch("utils.sudo_utils.need_sudo", return_value=False)
    @patch("utils.sudo_utils._read_file_with_sudo", return_value=b"secret")
    def test_copy_file_uses_sudo_read_without_sudo_write(
        self, mock_read, _mock_need_sudo, _mock_needs_read
    ):
        from utils.sudo_utils import copy_file

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "source"
            dst = Path(tmp) / "dest"
            src.write_text("unreadable")

            copy_file(src, dst)

            mock_read.assert_called_once_with(src)
            self.assertEqual(dst.read_bytes(), b"secret")

    @patch("utils.sudo_utils.run")
    @patch("utils.sudo_utils.need_sudo", return_value=True)
    def test_copy_file_uses_sudo_cp_when_destination_needs_sudo(self, _mock_need_sudo, mock_run):
        from utils.sudo_utils import copy_file

        copy_file("/tmp/source", "/etc/dest")

        mock_run.assert_called_once_with(["cp", "/tmp/source", "/etc/dest"])


if __name__ == "__main__":
    unittest_main()
