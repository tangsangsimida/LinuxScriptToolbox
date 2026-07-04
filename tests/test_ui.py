#!/usr/bin/env python3
"""Unit tests for utils/ui.py module.

Tests the unified UI interfaces with mocked inputs to ensure
consistent behavior across different scenarios.

Usage:
    python -m pytest tests/test_ui.py -v
    python tests/test_ui.py  # Standalone runner
"""

import sys
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


# Test UI constants are defined correctly
class TestUIConstants(TestCase):

    def test_back_action_constant(self):
        from utils.ui import BACK_ACTION
        self.assertEqual(BACK_ACTION, "back")

    def test_cancel_action_constant(self):
        from utils.ui import CANCEL_ACTION
        self.assertIsNone(CANCEL_ACTION)


# Test semantic markers are defined
class TestMarkers(TestCase):

    def test_markers_exist(self):
        from utils.ui import MARKERS
        expected_keys = {"success", "error", "info", "warning", "running"}
        self.assertEqual(set(MARKERS.keys()), expected_keys)

    def test_markers_are_strings(self):
        from utils.ui import MARKERS
        for key, value in MARKERS.items():
            self.assertIsInstance(value, str, f"MARKERS[{key!r}] should be a string")


# Test confirm() function
class TestConfirm(TestCase):

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui.questionary.confirm")
    def test_confirm_yes(self, mock_confirm):
        mock_confirm.return_value.ask.return_value = True
        from utils.ui import confirm
        result = confirm("Continue?")
        self.assertTrue(result)
        mock_confirm.assert_called_once_with("Continue?", default=False)

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui.questionary.confirm")
    def test_confirm_no(self, mock_confirm):
        mock_confirm.return_value.ask.return_value = False
        from utils.ui import confirm
        result = confirm("Continue?")
        self.assertFalse(result)

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui.questionary.confirm")
    def test_confirm_keyboard_interrupt(self, mock_confirm):
        mock_confirm.return_value.ask.side_effect = KeyboardInterrupt
        from utils.ui import confirm
        result = confirm("Continue?")
        self.assertFalse(result)

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="y")
    def test_confirm_fallback_yes(self, mock_input):
        from utils.ui import confirm
        result = confirm("Continue?")
        self.assertTrue(result)

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="n")
    def test_confirm_fallback_no(self, mock_input):
        from utils.ui import confirm
        result = confirm("Continue?")
        self.assertFalse(result)

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="")
    def test_confirm_fallback_default_true(self, mock_input):
        from utils.ui import confirm
        result = confirm("Continue?", default=True)
        self.assertTrue(result)

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="")
    def test_confirm_fallback_default_false(self, mock_input):
        from utils.ui import confirm
        result = confirm("Continue?", default=False)
        self.assertFalse(result)


# Regression: ISSUE-019. ask() must not crash with EOFError when stdin is
# piped (non-TTY) and the stream ends. It should return "" so callers like
# quick-fixes' _fix_stm32cubemx_wayland can detect "no input available"
# and abort cleanly.
class TestAskNonTTY(TestCase):

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="")
    def test_ask_non_tty_empty_input_returns_empty(self, mock_input):
        from utils.ui import ask
        self.assertEqual(ask("Enter path:"), "")

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="/opt/stm32cubemx")
    def test_ask_non_tty_returns_stripped_user_input(self, mock_input):
        from utils.ui import ask
        self.assertEqual(ask("Enter path:"), "/opt/stm32cubemx")

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", side_effect=EOFError)
    def test_ask_non_tty_eof_returns_empty(self, mock_input):
        # The original bug: ask() crashed with EOFError when stdin ended
        # mid-prompt, taking down the whole main.py entry point.
        from utils.ui import ask
        self.assertEqual(ask("Enter path:"), "")

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_ask_non_tty_keyboard_interrupt_returns_empty(self, mock_input):
        from utils.ui import ask
        self.assertEqual(ask("Enter path:"), "")


# Test select_option() function
class TestSelectOption(TestCase):

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui._select_with_keys")
    def test_select_option_returns_value(self, mock_select):
        mock_select.return_value = "opt1"
        from utils.ui import select_option
        options = [("opt1", "Option 1"), ("opt2", "Option 2")]
        result = select_option("Choose:", options)
        self.assertEqual(result, "opt1")

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui._select_with_keys")
    def test_select_option_cancel(self, mock_select):
        mock_select.return_value = None
        from utils.ui import select_option
        options = [("opt1", "Option 1")]
        result = select_option("Choose:", options)
        self.assertIsNone(result)

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui._select_with_keys")
    def test_select_option_keyboard_interrupt(self, mock_select):
        mock_select.side_effect = KeyboardInterrupt
        from utils.ui import select_option
        options = [("opt1", "Option 1")]
        result = select_option("Choose:", options)
        self.assertIsNone(result)

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="1")
    def test_select_option_fallback_first(self, mock_input):
        from utils.ui import select_option
        options = [("opt1", "Option 1"), ("opt2", "Option 2")]
        result = select_option("Choose:", options)
        self.assertEqual(result, "opt1")

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="2")
    def test_select_option_fallback_second(self, mock_input):
        from utils.ui import select_option
        options = [("opt1", "Option 1"), ("opt2", "Option 2")]
        result = select_option("Choose:", options)
        self.assertEqual(result, "opt2")

    @patch("utils.ui.IS_TTY", False)
    @patch("builtins.input", return_value="invalid")
    def test_select_option_fallback_invalid(self, mock_input):
        from utils.ui import select_option
        options = [("opt1", "Option 1")]
        result = select_option("Choose:", options)
        self.assertIsNone(result)


# Test prompt_selection() function
class TestPromptSelection(TestCase):

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui._select_with_keys")
    def test_prompt_selection_returns_id(self, mock_select):
        mock_select.return_value = "tool1"
        from utils.ui import prompt_selection
        options = [
            {"id": "tool1", "name_key": "Tool 1", "desc_key": "Desc 1"},
            {"id": "tool2", "name_key": "Tool 2", "desc_key": "Desc 2"},
        ]
        with patch("utils.ui.t", side_effect=lambda k: k):
            result = prompt_selection("Select:", options)
        self.assertEqual(result, "tool1")

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui._select_with_keys")
    def test_prompt_selection_back(self, mock_select):
        mock_select.return_value = "back"
        from utils.ui import prompt_selection, BACK_ACTION
        options = [{"id": "tool1", "name_key": "Tool 1"}]
        with patch("utils.ui.t", side_effect=lambda k: k):
            result = prompt_selection("Select:", options)
        self.assertEqual(result, BACK_ACTION)

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui._select_with_keys")
    def test_prompt_selection_cancel(self, mock_select):
        mock_select.return_value = None
        from utils.ui import prompt_selection
        options = [{"id": "tool1", "name_key": "Tool 1"}]
        with patch("utils.ui.t", side_effect=lambda k: k):
            result = prompt_selection("Select:", options)
        self.assertIsNone(result)

    @patch("utils.ui.IS_TTY", True)
    @patch("utils.ui._select_with_keys")
    def test_prompt_selection_no_back_option(self, mock_select):
        mock_select.return_value = "tool1"
        from utils.ui import prompt_selection
        options = [{"id": "tool1", "name_key": "Tool 1"}]
        with patch("utils.ui.t", side_effect=lambda k: k):
            result = prompt_selection("Select:", options, show_back=False)
        self.assertEqual(result, "tool1")


# Test print helper functions
class TestPrintHelpers(TestCase):

    @patch("utils.ui.console")
    def test_print_success(self, mock_console):
        from utils.ui import print_success
        print_success("Done")
        mock_console.print.assert_called_once()

    @patch("utils.ui.console")
    def test_print_error(self, mock_console):
        from utils.ui import print_error
        print_error("Failed")
        mock_console.print.assert_called_once()

    @patch("utils.ui.console")
    def test_print_info(self, mock_console):
        from utils.ui import print_info
        print_info("Info")
        mock_console.print.assert_called_once()

    @patch("utils.ui.console")
    def test_print_warning(self, mock_console):
        from utils.ui import print_warning
        print_warning("Warning")
        mock_console.print.assert_called_once()


# Standalone test runner
def run_tests():
    print("Running UI unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
