#!/usr/bin/env python3
"""Unit tests for tools/__init__.py module.

Tests tool discovery and filtering mechanisms.

Usage:
    python -m pytest tests/test_tools_init.py -v
"""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


class TestToolDiscovery(TestCase):
    """Test tool discovery mechanism."""

    def test_tools_list_is_not_empty(self):
        """Test that at least one tool is discovered."""
        from tools import TOOLS
        self.assertGreater(len(TOOLS), 0)

    def test_all_tools_have_required_attributes(self):
        """Test that all discovered tools have required attributes."""
        from tools import TOOLS
        for tool in TOOLS:
            self.assertTrue(hasattr(tool, 'name'), f"Tool {tool} missing 'name'")
            self.assertTrue(hasattr(tool, 'display_name'), f"Tool {tool} missing 'display_name'")
            self.assertTrue(hasattr(tool, 'description'), f"Tool {tool} missing 'description'")
            self.assertTrue(hasattr(tool, 'distros'), f"Tool {tool} missing 'distros'")
            self.assertTrue(hasattr(tool, 'platforms'), f"Tool {tool} missing 'platforms'")
            self.assertTrue(hasattr(tool, 'run'), f"Tool {tool} missing 'run'")
            self.assertTrue(hasattr(tool, 'mutates_system'), f"Tool {tool} missing 'mutates_system'")
            self.assertTrue(hasattr(tool, 'requires_network'), f"Tool {tool} missing 'requires_network'")
            self.assertTrue(hasattr(tool, 'requires_sudo'), f"Tool {tool} missing 'requires_sudo'")
            self.assertTrue(hasattr(tool, 'safe_for_run_all'), f"Tool {tool} missing 'safe_for_run_all'")

    def test_all_tools_have_unique_names(self):
        """Test that all tools have unique names."""
        from tools import TOOLS
        names = [t.name for t in TOOLS]
        self.assertEqual(len(names), len(set(names)), f"Duplicate tool names: {names}")

    def test_all_tools_have_non_empty_distros(self):
        """Test that all tools have at least one distro."""
        from tools import TOOLS
        for tool in TOOLS:
            self.assertGreater(len(tool.distros), 0, f"Tool {tool.name} has empty distros")

    def test_all_tools_have_non_empty_platforms(self):
        """Test that all tools have at least one platform."""
        from tools import TOOLS
        for tool in TOOLS:
            self.assertGreater(len(tool.platforms), 0, f"Tool {tool.name} has empty platforms")

    def test_all_tools_have_valid_platforms(self):
        """Test that all tools use valid platform values."""
        from tools import TOOLS
        valid_platforms = {"linux", "windows", "macos"}
        for tool in TOOLS:
            for platform in tool.platforms:
                self.assertIn(
                    platform, valid_platforms,
                    f"Tool {tool.name} has invalid platform: {platform}"
                )

    def test_run_all_tools_are_read_only(self):
        """Only explicitly safe read-only tools should participate in run-all."""
        from tools import TOOLS
        safe_tools = [tool for tool in TOOLS if tool.safe_for_run_all]

        self.assertGreater(len(safe_tools), 0)
        for tool in safe_tools:
            self.assertFalse(tool.mutates_system, f"{tool.name} mutates system but is run-all safe")


class TestGetToolsForDistro(TestCase):
    """Test get_tools_for_distro() function."""

    def test_arch_tools(self):
        """Test filtering tools for Arch Linux."""
        from tools import get_tools_for_distro
        arch_tools = get_tools_for_distro("arch")
        self.assertGreater(len(arch_tools), 0)
        for tool in arch_tools:
            self.assertIn("arch", tool.distros)

    def test_debian_tools(self):
        """Test filtering tools for Debian."""
        from tools import get_tools_for_distro
        debian_tools = get_tools_for_distro("debian")
        self.assertGreater(len(debian_tools), 0)
        for tool in debian_tools:
            self.assertIn("debian", tool.distros)

    def test_fedora_tools(self):
        """Test filtering tools for Fedora."""
        from tools import get_tools_for_distro
        fedora_tools = get_tools_for_distro("fedora")
        # Fedora should have at least mirror-optimizer and ai-cli-setup
        self.assertGreater(len(fedora_tools), 0)
        for tool in fedora_tools:
            self.assertIn("fedora", tool.distros)

    def test_unknown_distro_tools(self):
        """Test filtering tools for unknown distro."""
        from tools import get_tools_for_distro
        unknown_tools = get_tools_for_distro("unknown")
        # Should have at least mirror-optimizer and ai-cli-setup
        self.assertGreater(len(unknown_tools), 0)
        for tool in unknown_tools:
            self.assertIn("unknown", tool.distros)

    def test_nonexistent_distro_returns_empty(self):
        """Test that nonexistent distro returns empty list."""
        from tools import get_tools_for_distro
        result = get_tools_for_distro("nonexistent_distro_xyz")
        self.assertEqual(len(result), 0)


class TestGetToolsForPlatform(TestCase):
    """Test get_tools_for_platform() function."""

    def test_linux_tools(self):
        """Test filtering tools for Linux platform."""
        from tools import get_tools_for_platform
        linux_tools = get_tools_for_platform("linux")
        self.assertGreater(len(linux_tools), 0)
        for tool in linux_tools:
            self.assertIn("linux", tool.platforms)

    def test_windows_tools(self):
        """Test filtering tools for Windows platform."""
        from tools import get_tools_for_platform
        windows_tools = get_tools_for_platform("windows")
        # Should have at least system-info, mirror-optimizer, ai-cli-setup
        self.assertGreater(len(windows_tools), 0)
        for tool in windows_tools:
            self.assertIn("windows", tool.platforms)

    def test_macos_tools(self):
        """Test filtering tools for macOS platform."""
        from tools import get_tools_for_platform
        macos_tools = get_tools_for_platform("macos")
        # macOS support is not yet implemented; expect empty
        self.assertEqual(len(macos_tools), 0)

    def test_nonexistent_platform_returns_empty(self):
        """Test that nonexistent platform returns empty list."""
        from tools import get_tools_for_platform
        result = get_tools_for_platform("nonexistent_platform_xyz")
        self.assertEqual(len(result), 0)


class TestGetTools(TestCase):
    """Test get_tools() function with both distro and platform filtering."""

    def test_linux_arch(self):
        """Test filtering for Linux Arch."""
        from tools import get_tools
        tools = get_tools("arch", "linux")
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn("arch", tool.distros)
            self.assertIn("linux", tool.platforms)

    def test_windows(self):
        """Test filtering for Windows."""
        from tools import get_tools
        tools = get_tools("windows", "windows")
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn("windows", tool.distros)
            self.assertIn("windows", tool.platforms)

    def test_no_match_returns_empty(self):
        """Test that non-matching combo returns empty."""
        from tools import get_tools
        # nonexistent distro + nonexistent platform should return nothing
        tools = get_tools("nonexistent_distro_xyz", "nonexistent_platform_xyz")
        self.assertEqual(len(tools), 0)


def run_tests():
    """Standalone test runner."""
    print("Running tools/__init__ unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
