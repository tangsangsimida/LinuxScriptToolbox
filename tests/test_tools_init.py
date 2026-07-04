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

    def test_run_all_tools_are_read_only(self):
        """Only explicitly safe read-only tools should participate in run-all."""
        from tools import TOOLS
        safe_tools = [tool for tool in TOOLS if tool.safe_for_run_all]

        self.assertGreater(len(safe_tools), 0)
        for tool in safe_tools:
            self.assertFalse(tool.mutates_system, f"{tool.name} mutates system but is run-all safe")


class TestGetToolsByDistro(TestCase):
    """Test get_tools(distro=...) filtering.

    Use the unified get_tools() API rather than the deprecated
    get_tools_for_distro() so DeprecationWarning does not pollute test output.
    使用统一的 get_tools() API，替代已废弃的 get_tools_for_distro()，
    避免测试输出中出现 DeprecationWarning。
    """

    def test_arch_tools(self):
        """Test filtering tools for Arch Linux."""
        from tools import get_tools
        arch_tools = get_tools(distro="arch")
        self.assertGreater(len(arch_tools), 0)
        for tool in arch_tools:
            self.assertIn("arch", tool.distros)

    def test_debian_tools(self):
        """Test filtering tools for Debian."""
        from tools import get_tools
        debian_tools = get_tools(distro="debian")
        self.assertGreater(len(debian_tools), 0)
        for tool in debian_tools:
            self.assertIn("debian", tool.distros)

    def test_fedora_tools(self):
        """Test filtering tools for Fedora."""
        from tools import get_tools
        fedora_tools = get_tools(distro="fedora")
        # Fedora should have at least mirror-optimizer and ai-cli-setup
        self.assertGreater(len(fedora_tools), 0)
        for tool in fedora_tools:
            self.assertIn("fedora", tool.distros)

    def test_unknown_distro_tools(self):
        """Test filtering tools for unknown distro."""
        from tools import get_tools
        unknown_tools = get_tools(distro="unknown")
        # Should have at least mirror-optimizer and ai-cli-setup
        self.assertGreater(len(unknown_tools), 0)
        for tool in unknown_tools:
            self.assertIn("unknown", tool.distros)

    def test_nonexistent_distro_returns_empty(self):
        """Test that nonexistent distro returns empty list."""
        from tools import get_tools
        result = get_tools(distro="nonexistent_distro_xyz")
        self.assertEqual(len(result), 0)


def run_tests():
    """Standalone test runner."""
    print("Running tools/__init__ unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
