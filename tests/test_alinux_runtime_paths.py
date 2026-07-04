#!/usr/bin/env python3
"""Regression tests for ISSUE-015: alinux runtime paths.

PR #14 (issue #10 fix) added 'alinux' to every Tool's distros list, but the
internal 'pick packages / pick install command by distro' branches still had
alinux falling through to the debian/apt path. This test suite pins each of
those branches to a fedora-family path (since alinux = RHEL = dnf).
"""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


# dev-tools: alinux should pick fedora_pkgs, not debian_pkgs.
class TestDevToolsAlinux(TestCase):

    def test_alinux_uses_fedora_pkgs_not_debian(self):
        from tools.common import dev_tools

        option = {
            "name_key": "msg.devtool_arm_gcc",
            "arch_pkgs": ["arch-pkg"],
            "fedora_pkgs": ["arm-none-eabi-gcc", "arm-none-eabi-newlib"],
            "suse_pkgs": ["suse-pkg"],
            "debian_pkgs": ["gcc-arm-none-eabi", "libnewlib-arm-none-eabi"],
        }

        # Make every package look already installed so the call returns True
        # before reaching _install_packages. We only care that the right list
        # was selected, not whether the actual install was attempted.
        with patch.object(dev_tools, "package_is_installed", return_value=True):
            tool = dev_tools.DevToolsSetup()
            self.assertTrue(tool._install_toolchain(option, "alinux"))


# shorin-setup: alinux should dispatch to _run_fedora_setup.
class TestShorinSetupAlinux(TestCase):

    def test_alinux_dispatches_to_fedora_setup(self):
        from tools.common import shorin_setup

        tool = shorin_setup.ShorinSetup()

        with patch.object(tool, "_clone_repo", return_value=True), \
             patch.object(tool, "_run_fedora_setup", return_value=True) as mock_fedora, \
             patch.object(tool, "_run_ubuntu_setup", return_value=True) as mock_ubuntu, \
             patch("tools.common.shorin_setup.detect_distro", return_value="alinux"), \
             patch(
                 "tools.common.shorin_setup.prompt_selection",
                 side_effect=lambda *a, **kw: "gnome",
             ), \
             patch("tools.common.shorin_setup.confirm", return_value=True):
            # run() returns the inner method's result on the first option.
            self.assertTrue(tool.run())
            mock_fedora.assert_called_once_with("gnome")
            mock_ubuntu.assert_not_called()


# tailscale-client: alinux should call _install_tailscale_fedora.
class TestTailscaleClientAlinux(TestCase):

    def test_alinux_routes_to_fedora_installer(self):
        from tools.common import tailscale_client

        with patch.object(tailscale_client, "detect_distro", return_value="alinux"), \
             patch.object(
                 tailscale_client, "_install_tailscale_fedora", return_value=True
             ) as mock_fedora, \
             patch.object(
                 tailscale_client, "_install_tailscale_generic", return_value=True
             ) as mock_generic:
            self.assertTrue(tailscale_client._install_tailscale_linux())
            mock_fedora.assert_called_once_with()
            mock_generic.assert_not_called()


# system-cleanup: alinux should run dnf clean all, not apt-get clean.
class TestSystemCleanupAlinux(TestCase):

    def test_alinux_pkg_cache_uses_dnf(self):
        from tools.common import system_cleanup

        with patch.object(system_cleanup, "run_verbose", return_value=0) as mock_run:
            self.assertTrue(system_cleanup._clean_pkg_cache("alinux"))
            # First positional call is the cache-clean command
            first_cmd = mock_run.call_args_list[0].args[0]
            self.assertIn("dnf", first_cmd)
            self.assertIn("clean", first_cmd)
            self.assertNotIn("apt-get", " ".join(first_cmd))

    def test_run_dry_lists_dnf_for_alinux(self):
        from tools.common import system_cleanup

        with patch.object(system_cleanup, "detect_distro", return_value="alinux"):
            preview = system_cleanup.SystemCleanup().run_dry()
        self.assertIn("dnf", preview)
        self.assertIn("Package cache", preview)


if __name__ == "__main__":
    unittest_main()
