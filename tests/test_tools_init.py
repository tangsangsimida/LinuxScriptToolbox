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


# Test tool discovery mechanism
class TestToolDiscovery(TestCase):

    # Test that at least one tool is discovered
    def test_tools_list_is_not_empty(self):
        from tools import TOOLS
        self.assertGreater(len(TOOLS), 0)

    # Test that all discovered tools have required attributes
    def test_all_tools_have_required_attributes(self):
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

    # Test that all tools have unique names
    def test_all_tools_have_unique_names(self):
        from tools import TOOLS
        names = [t.name for t in TOOLS]
        self.assertEqual(len(names), len(set(names)), f"Duplicate tool names: {names}")

    # Test that all tools have at least one distro
    def test_all_tools_have_non_empty_distros(self):
        from tools import TOOLS
        for tool in TOOLS:
            self.assertGreater(len(tool.distros), 0, f"Tool {tool.name} has empty distros")

    # Test that all tools have at least one platform
    def test_all_tools_have_non_empty_platforms(self):
        from tools import TOOLS
        for tool in TOOLS:
            self.assertGreater(len(tool.platforms), 0, f"Tool {tool.name} has empty platforms")

    # Test that all tools use valid platform values
    def test_all_tools_have_valid_platforms(self):
        from tools import TOOLS
        valid_platforms = {"linux", "windows", "macos"}
        for tool in TOOLS:
            for platform in tool.platforms:
                self.assertIn(
                    platform, valid_platforms,
                    f"Tool {tool.name} has invalid platform: {platform}"
                )

    # Only explicitly safe read-only tools should participate in run-all
    def test_run_all_tools_are_read_only(self):
        from tools import TOOLS
        safe_tools = [tool for tool in TOOLS if tool.safe_for_run_all]

        self.assertGreater(len(safe_tools), 0)
        for tool in safe_tools:
            self.assertFalse(tool.mutates_system, f"{tool.name} mutates system but is run-all safe")


# Test get_tools(distro=...) filtering
class TestGetToolsByDistro(TestCase):
    """Test get_tools(distro=...) filtering.

    Use the unified get_tools() API rather than the deprecated
    get_tools_for_distro() so DeprecationWarning does not pollute test output.
    使用统一的 get_tools() API，替代已废弃的 get_tools_for_distro()，
    避免测试输出中出现 DeprecationWarning。
    """

    # Test filtering tools for Arch Linux
    def test_arch_tools(self):
        from tools import get_tools
        arch_tools = get_tools(distro="arch")
        self.assertGreater(len(arch_tools), 0)
        for tool in arch_tools:
            self.assertIn("arch", tool.distros)

    # Test filtering tools for Debian
    def test_debian_tools(self):
        from tools import get_tools
        debian_tools = get_tools(distro="debian")
        self.assertGreater(len(debian_tools), 0)
        for tool in debian_tools:
            self.assertIn("debian", tool.distros)

    # Test filtering tools for Fedora
    def test_fedora_tools(self):
        from tools import get_tools
        fedora_tools = get_tools(distro="fedora")
        # Fedora should have at least mirror-optimizer and ai-cli-setup
        self.assertGreater(len(fedora_tools), 0)
        for tool in fedora_tools:
            self.assertIn("fedora", tool.distros)

    # Test filtering tools for unknown distro
    def test_unknown_distro_tools(self):
        from tools import get_tools
        unknown_tools = get_tools(distro="unknown")
        # Should have at least mirror-optimizer and ai-cli-setup
        self.assertGreater(len(unknown_tools), 0)
        for tool in unknown_tools:
            self.assertIn("unknown", tool.distros)

    # Test that nonexistent distro returns empty list
    def test_nonexistent_distro_returns_empty(self):
        from tools import get_tools
        result = get_tools(distro="nonexistent_distro_xyz")
        self.assertEqual(len(result), 0)


# Test get_tools(platform=...) filtering
class TestGetToolsByPlatform(TestCase):
    """Test get_tools(platform=...) filtering.

    Mirrors TestGetToolsByDistro but for platform dimension; uses the
    unified get_tools() API to avoid DeprecationWarning.
    与 TestGetToolsByDistro 对称，针对平台维度；同样使用统一的
    get_tools() API 以避免 DeprecationWarning。
    """

    # Test filtering tools for Linux platform
    def test_linux_tools(self):
        from tools import get_tools
        linux_tools = get_tools(platform="linux")
        self.assertGreater(len(linux_tools), 0)
        for tool in linux_tools:
            self.assertIn("linux", tool.platforms)

    # Test filtering tools for Windows platform
    def test_windows_tools(self):
        from tools import get_tools
        windows_tools = get_tools(platform="windows")
        # Should have at least system-info, mirror-optimizer, ai-cli-setup
        self.assertGreater(len(windows_tools), 0)
        for tool in windows_tools:
            self.assertIn("windows", tool.platforms)

    # Test filtering tools for macOS platform
    def test_macos_tools(self):
        from tools import get_tools
        macos_tools = get_tools(platform="macos")
        # macOS support is not yet implemented; expect empty
        self.assertEqual(len(macos_tools), 0)

    # Test that nonexistent platform returns empty list
    def test_nonexistent_platform_returns_empty(self):
        from tools import get_tools
        result = get_tools(platform="nonexistent_platform_xyz")
        self.assertEqual(len(result), 0)


# Test get_tools() with combined distro and platform filtering
class TestGetTools(TestCase):

    # Test filtering for Linux Arch
    def test_linux_arch(self):
        from tools import get_tools
        tools = get_tools("arch", "linux")
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn("arch", tool.distros)
            self.assertIn("linux", tool.platforms)

    # Test filtering for Windows
    def test_windows(self):
        from tools import get_tools
        tools = get_tools("windows", "windows")
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn("windows", tool.distros)
            self.assertIn("windows", tool.platforms)

    # Test that non-matching combo returns empty
    def test_no_match_returns_empty(self):
        from tools import get_tools
        # nonexistent distro + nonexistent platform should return nothing
        tools = get_tools("nonexistent_distro_xyz", "nonexistent_platform_xyz")
        self.assertEqual(len(tools), 0)

    # Test filtering by distro only (platform=None)
    def test_distro_only_filter(self):
        from tools import get_tools
        tools = get_tools(distro="arch")
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn("arch", tool.distros)

    # Test filtering by platform only (distro=None)
    def test_platform_only_filter(self):
        from tools import get_tools
        tools = get_tools(platform="linux")
        self.assertGreater(len(tools), 0)
        for tool in tools:
            self.assertIn("linux", tool.platforms)

    # Test that get_tools() with no args returns all tools
    def test_no_filter_returns_all(self):
        from tools import get_tools, TOOLS
        tools = get_tools()
        self.assertEqual(len(tools), len(TOOLS))

    # Test that distro-only filter excludes tools without that distro
    def test_distro_only_excludes_non_matching(self):
        from tools import get_tools
        tools = get_tools(distro="arch")
        for tool in tools:
            self.assertIn("arch", tool.distros)

    # Test that platform-only filter excludes tools without that platform
    def test_platform_only_excludes_non_matching(self):
        from tools import get_tools
        tools = get_tools(platform="windows")
        for tool in tools:
            self.assertIn("windows", tool.platforms)


# Standalone test runner
def run_tests():
    print("Running tools/__init__ unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
