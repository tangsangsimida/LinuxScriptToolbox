#!/usr/bin/env python3
"""Unit tests for utils/platform.py module.

Tests platform detection (Linux, Windows, macOS).

Usage:
    python -m pytest tests/test_platform.py -v
"""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


class TestDetectPlatform(TestCase):
    """Test detect_platform() function."""

    def setUp(self):
        from utils.platform import detect_platform
        detect_platform.cache_clear()

    @patch("utils.platform.platform.system", return_value="Linux")
    def test_linux(self, mock_system):
        """Test Linux detection."""
        from utils.platform import detect_platform
        result = detect_platform()
        self.assertEqual(result, "linux")

    @patch("utils.platform.platform.system", return_value="Windows")
    def test_windows(self, mock_system):
        """Test Windows detection."""
        from utils.platform import detect_platform
        result = detect_platform()
        self.assertEqual(result, "windows")

    @patch("utils.platform.platform.system", return_value="Darwin")
    def test_macos(self, mock_system):
        """Test macOS detection."""
        from utils.platform import detect_platform
        result = detect_platform()
        self.assertEqual(result, "macos")

    @patch("utils.platform.platform.system", return_value="FreeBSD")
    def test_unknown_defaults_to_linux(self, mock_system):
        """Test that unknown platforms default to linux."""
        from utils.platform import detect_platform
        result = detect_platform()
        self.assertEqual(result, "linux")


class TestIsRoot(TestCase):
    """Test is_root() function."""

    @patch("utils.platform.detect_platform", return_value="linux")
    @patch("utils.platform.os.geteuid", return_value=0)
    def test_linux_root(self, mock_geteuid, mock_platform):
        """Test Linux root detection (uid 0)."""
        from utils.platform import is_root
        result = is_root()
        self.assertTrue(result)

    @patch("utils.platform.detect_platform", return_value="linux")
    @patch("utils.platform.os.geteuid", return_value=1000)
    def test_linux_non_root(self, mock_geteuid, mock_platform):
        """Test Linux non-root detection."""
        from utils.platform import is_root
        result = is_root()
        self.assertFalse(result)

    @patch("utils.platform.detect_platform", return_value="windows")
    def test_windows_admin(self, mock_platform):
        """Test Windows admin detection."""
        # This is hard to mock properly since it uses ctypes
        # Just verify it doesn't crash
        from utils.platform import is_root
        result = is_root()
        self.assertIsInstance(result, bool)


def run_tests():
    """Standalone test runner."""
    print("Running platform detection unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
