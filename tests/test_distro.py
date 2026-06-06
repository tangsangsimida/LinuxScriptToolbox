#!/usr/bin/env python3
"""Unit tests for utils/distro.py module.

Tests distribution detection with mocked /etc/os-release content.

Usage:
    python -m pytest tests/test_distro.py -v
"""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


class TestDetectDistro(TestCase):
    """Test detect_distro() function."""

    @patch("utils.distro.Path")
    def test_arch_linux(self, mock_path):
        """Test detection of Arch Linux."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=arch\nNAME="Arch Linux"'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "arch")

    @patch("utils.distro.Path")
    def test_arch_like(self, mock_path):
        """Test detection of Arch-like distros (e.g., Manjaro)."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=manjaro\nID_LIKE=arch'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "arch")

    @patch("utils.distro.Path")
    def test_debian(self, mock_path):
        """Test detection of Debian."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=debian\nNAME="Debian GNU/Linux"'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "debian")

    @patch("utils.distro.Path")
    def test_ubuntu(self, mock_path):
        """Test detection of Ubuntu."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=ubuntu\nNAME="Ubuntu"'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "debian")

    @patch("utils.distro.Path")
    def test_debian_like(self, mock_path):
        """Test detection of Debian-like distros (ID_LIKE=debian)."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=linuxmint\nID_LIKE=debian'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "debian")

    @patch("utils.distro.Path")
    def test_fedora(self, mock_path):
        """Test detection of Fedora."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=fedora\nNAME="Fedora Linux"'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "fedora")

    @patch("utils.distro.Path")
    def test_opensuse(self, mock_path):
        """Test detection of openSUSE."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=opensuse\nNAME="openSUSE Tumbleweed"'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "suse")

    @patch("utils.distro.Path")
    def test_suse(self, mock_path):
        """Test detection of SUSE."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=suse\nNAME="SUSE Linux"'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "suse")

    @patch("utils.distro.Path")
    def test_unknown_distro(self, mock_path):
        """Test detection of unknown distribution."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = 'ID=centos\nNAME="CentOS Linux"'
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "unknown")

    @patch("utils.distro.Path")
    def test_no_os_release(self, mock_path):
        """Test when /etc/os-release does not exist."""
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = False
        mock_path.return_value = mock_os_release

        from utils.distro import detect_distro
        result = detect_distro()
        self.assertEqual(result, "unknown")


def run_tests():
    """Standalone test runner."""
    print("Running distro detection unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
