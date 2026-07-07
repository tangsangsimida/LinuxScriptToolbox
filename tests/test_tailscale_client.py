#!/usr/bin/env python3
"""Unit tests for tools/common/tailscale_client.py helpers."""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from tools.common import tailscale_client


class TestGetDerpInfo(TestCase):
    """Regression: ISSUE-044. _get_derp_info crashed with ValueError when
    derp_port or stun_port was an empty string (e.g. non-TTY mode from
    ISSUE-019, or user pressing enter without input).
    """

    def test_empty_derp_port_falls_back_to_default(self):
        """Empty string (e.g. non-TTY mode) should not crash; use 443."""
        # ask() is called: host, cert_name, derp_port, stun_port (4 times)
        with patch("tools.common.tailscale_client.confirm", return_value=False), \
             patch(
                 "tools.common.tailscale_client.ask",
                 side_effect=["8.8.8.8", "", "", "3478"],
             ):
            result = tailscale_client._get_derp_info()
        self.assertEqual(result["host"], "8.8.8.8")
        self.assertEqual(result["derp_port"], 443)
        self.assertEqual(result["stun_port"], 3478)

    def test_empty_stun_port_falls_back_to_default(self):
        with patch("tools.common.tailscale_client.confirm", return_value=False), \
             patch(
                 "tools.common.tailscale_client.ask",
                 side_effect=["8.8.8.8", "mycert", "8443", ""],
             ):
            result = tailscale_client._get_derp_info()
        self.assertEqual(result["derp_port"], 8443)
        self.assertEqual(result["stun_port"], 3478)

    def test_invalid_port_falls_back_to_default(self):
        with patch("tools.common.tailscale_client.confirm", return_value=False), \
             patch(
                 "tools.common.tailscale_client.ask",
                 side_effect=["8.8.8.8", "mycert", "abc", "xyz"],
             ):
            result = tailscale_client._get_derp_info()
        self.assertEqual(result["derp_port"], 443)
        self.assertEqual(result["stun_port"], 3478)

    def test_valid_ports_pass_through(self):
        with patch("tools.common.tailscale_client.confirm", return_value=False), \
             patch(
                 "tools.common.tailscale_client.ask",
                 side_effect=["8.8.8.8", "mycert", "8443", "3479"],
             ):
            result = tailscale_client._get_derp_info()
        self.assertEqual(result["derp_port"], 8443)
        self.assertEqual(result["stun_port"], 3479)
        self.assertEqual(result["cert_name"], "mycert")


if __name__ == "__main__":
    unittest_main()
