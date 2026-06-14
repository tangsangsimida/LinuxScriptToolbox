#!/usr/bin/env python3
"""Unit tests for mirror optimizer helper behavior."""

import sys
import tempfile
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from tools.common import mirror_optimizer


class TestMirrorOptimizerHelpers(TestCase):
    """Test pure mirror optimizer helpers."""

    def test_arch_managed_block_is_idempotent(self):
        original = "# Original mirror\nServer = https://example.invalid/$repo/os/$arch\n"
        first = mirror_optimizer._prepend_managed_block(original, ["Server = https://mirror/arch"])
        second = mirror_optimizer._prepend_managed_block(first, ["Server = https://mirror/arch"])

        self.assertEqual(second.count(mirror_optimizer.MANAGED_BLOCK_START), 1)
        self.assertEqual(second.count("Server = https://mirror/arch"), 1)
        self.assertIn("# Original mirror", second)

    def test_deb822_uses_debian_mirror_for_debian_sources(self):
        content = """Types: deb
URIs: https://deb.debian.org/debian/
Suites: bookworm
Components: main
"""

        result = mirror_optimizer._optimize_deb822(content)

        self.assertIn("URIs: https://mirrors.ustc.edu.cn/debian/", result)

    def test_get_apt_sources_path_detects_any_sources_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources_dir = Path(tmp) / "sources.list.d"
            sources_dir.mkdir()
            custom_sources = sources_dir / "debian.sources"
            custom_sources.write_text("Types: deb\n")

            with patch.object(mirror_optimizer, "SOURCES_LIST_DIR", sources_dir):
                with patch.object(mirror_optimizer, "SOURCES_LIST", Path(tmp) / "sources.list"):
                    self.assertEqual(mirror_optimizer._get_apt_sources_path(), custom_sources)


if __name__ == "__main__":
    unittest_main()
