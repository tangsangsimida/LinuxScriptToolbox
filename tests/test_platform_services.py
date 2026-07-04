#!/usr/bin/env python3
"""Unit tests for utils/platform_services.py — package detection."""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from utils import platform_services


class TestPackageIsInstalled(TestCase):
    """Regression: ISSUE-022. alinux/RHEL-family packages must use rpm,
    not dpkg. Verify that alinux and unknown distros go through rpm,
    while debian/ubuntu go through dpkg.
    """

    @patch("utils.platform_services.run_cmd", return_value=(0, "git 2.43.0\n"))
    def test_alinux_uses_rpm(self, mock_run_cmd):
        self.assertTrue(platform_services.package_is_installed("git", "alinux"))
        self.assertIn("rpm", mock_run_cmd.call_args[0][0])

    @patch("utils.platform_services.run_cmd", return_value=(0, "git 2.43.0\n"))
    def test_unknown_uses_rpm(self, mock_run_cmd):
        self.assertTrue(platform_services.package_is_installed("git", "unknown"))
        self.assertIn("rpm", mock_run_cmd.call_args[0][0])

    @patch("utils.platform_services.run_cmd", return_value=(0, "git 2.43.0\n"))
    def test_fedora_uses_rpm(self, mock_run_cmd):
        self.assertTrue(platform_services.package_is_installed("git", "fedora"))
        self.assertIn("rpm", mock_run_cmd.call_args[0][0])

    @patch("utils.platform_services.run_cmd", return_value=(0, "dpkg -s output\n"))
    def test_debian_uses_dpkg(self, mock_run_cmd):
        self.assertTrue(platform_services.package_is_installed("git", "debian"))
        self.assertIn("dpkg", mock_run_cmd.call_args[0][0])

    @patch("utils.platform_services.run_cmd", return_value=(1, ""))
    def test_not_installed_returns_false(self, mock_run_cmd):
        self.assertFalse(platform_services.package_is_installed("nonexistent-pkg", "alinux"))


if __name__ == "__main__":
    unittest_main()
