#!/usr/bin/env python3
"""Unit tests for tools/common/system_info.py helpers."""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


# Test disk usage presentation logic
class TestDiskHomeScan(TestCase):
    """Regression: ISSUE-020. du -sh --max-depth=1 are mutually exclusive.
    The `-s` flag conflicts with `--max-depth=1`, causing du to return
    exit code 1 with no output. Verify the command uses `-h` only.
    """

    @patch("tools.common.system_info.Path.home")
    @patch("tools.common.system_info.run_cmd")
    def test_home_scan_uses_h_not_sh(self, mock_run_cmd, mock_home):
        mock_home.return_value = Path("/home/testuser")
        mock_run_cmd.return_value = (0, "")
        from tools.common.system_info import _show_disk

        _show_disk()

        # Verify the command does NOT contain -s alongside --max-depth
        args, _ = mock_run_cmd.call_args_list[1]  # second call is home scan
        cmd = args[0]
        self.assertIn("--max-depth=1", cmd)
        self.assertNotIn("-s", cmd)  # The bug: -s makes du exit 1
        self.assertIn("-h", cmd)


if __name__ == "__main__":
    unittest_main()
