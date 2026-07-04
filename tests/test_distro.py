#!/usr/bin/env python3
"""Unit tests for utils/distro.py module.

Tests distribution detection with mocked /etc/os-release content
and platform detection.

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


# Test detect_distro() function on Linux
class TestDetectDistro(TestCase):

    def setUp(self):
        from utils.distro import detect_distro
        detect_distro.cache_clear()
        self._patch_platform = patch("utils.distro.detect_platform", return_value="linux")
        self._patch_path = patch("utils.distro.Path")
        self.mock_platform = self._patch_platform.start()
        self.mock_path = self._patch_path.start()

    def tearDown(self):
        self._patch_path.stop()
        self._patch_platform.stop()

    def _set_os_release(self, content: str):
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = True
        mock_os_release.read_text.return_value = content
        self.mock_path.return_value = mock_os_release

    # Test detection of Arch Linux
    def test_arch_linux(self):
        self._set_os_release('ID=arch\nNAME="Arch Linux"')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "arch")

    # Test detection of Arch-like distros (e.g., Manjaro)
    def test_arch_like(self):
        self._set_os_release('ID=manjaro\nID_LIKE=arch')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "arch")

    # Test detection of Debian
    def test_debian(self):
        self._set_os_release('ID=debian\nNAME="Debian GNU/Linux"')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "debian")

    # Test detection of Ubuntu
    def test_ubuntu(self):
        self._set_os_release('ID=ubuntu\nNAME="Ubuntu"')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "debian")

    # Test detection of Debian-like distros (ID_LIKE=debian)
    def test_debian_like(self):
        self._set_os_release('ID=linuxmint\nID_LIKE=debian')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "debian")

    # Test detection of Fedora
    def test_fedora(self):
        self._set_os_release('ID=fedora\nNAME="Fedora Linux"')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "fedora")

    # Test detection of openSUSE
    def test_opensuse(self):
        self._set_os_release('ID=opensuse\nNAME="openSUSE Tumbleweed"')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "suse")

    # Test detection of SUSE
    def test_suse(self):
        self._set_os_release('ID=suse\nNAME="SUSE Linux"')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "suse")

    # Test detection of unknown distribution
    def test_unknown_distro(self):
        self._set_os_release('ID=centos\nNAME="CentOS Linux"')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "unknown")

# Test detection of Alibaba Cloud Linux 3 (ID=alinux)
    def test_alibaba_cloud_linux(self):
        self._set_os_release(
            'NAME="Alibaba Cloud Linux"\n'
            'VERSION="3 (OpenAnolis Edition)"\n'
            'ID="alinux"\n'
            'ID_LIKE="rhel fedora centos anolis"\n'
        )
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "alinux")

    # Test when /etc/os-release does not exist
    def test_no_os_release(self):
        mock_os_release = MagicMock()
        mock_os_release.exists.return_value = False
        self.mock_path.return_value = mock_os_release
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "unknown")

    # ID=archcraft alone should NOT match as arch (regression test)
    def test_archcraft_not_arch(self):
        self._set_os_release('ID=archcraft\nNAME="ArchCraft"')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "unknown")

    # ID=archcraft with ID_LIKE=arch should match as arch
    def test_archcraft_with_arch_id_like(self):
        self._set_os_release('ID=archcraft\nID_LIKE=arch')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "arch")

    # ID=opensuse-tumbleweed should match as suse
    def test_opensuse_tumbleweed(self):
        self._set_os_release('ID=opensuse-tumbleweed')
        from utils.distro import detect_distro
        self.assertEqual(detect_distro(), "suse")


# Test detect_distro() function on Windows
class TestDetectDistroWindows(TestCase):

    # Test that Windows platform returns 'windows' distro
    @patch("utils.distro.detect_platform", return_value="windows")
    def test_windows_returns_windows(self, mock_platform):
        from utils.distro import detect_distro
        detect_distro.cache_clear()
        result = detect_distro()
        self.assertEqual(result, "windows")


# Test detect_distro() function on macOS
class TestDetectDistroMacOS(TestCase):

    # Test that macOS platform returns 'macos' distro
    @patch("utils.distro.detect_platform", return_value="macos")
    def test_macos_returns_macos(self, mock_platform):
        from utils.distro import detect_distro
        detect_distro.cache_clear()
        result = detect_distro()
        self.assertEqual(result, "macos")


# Standalone test runner
def run_tests():
    print("Running distro detection unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
