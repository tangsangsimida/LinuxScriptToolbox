#!/usr/bin/env python3
"""Unit tests for utils/i18n.py module.

Tests translation lookup, fallback behavior, and language persistence.

Usage:
    python -m pytest tests/test_i18n.py -v
"""

import sys
import ast
from pathlib import Path
from collections import Counter
from unittest import TestCase, main as unittest_main
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


# Test t() function for translation lookup
class TestTranslationLookup(TestCase):

    # Reset global language state before each test
    def setUp(self):
        import utils.i18n
        utils.i18n._current_lang = None

    # Test English translation lookup
    @patch("utils.i18n.get_lang", return_value="en")
    def test_english_translation(self, mock_get_lang):
        from utils.i18n import t
        result = t("ui.available_tools")
        self.assertEqual(result, "Available tools:")

    # Test Chinese translation lookup
    @patch("utils.i18n.get_lang", return_value="zh")
    def test_chinese_translation(self, mock_get_lang):
        from utils.i18n import t
        result = t("ui.available_tools")
        self.assertEqual(result, "可用工具：")

    # Test translation with format kwargs
    @patch("utils.i18n.get_lang", return_value="en")
    def test_translation_with_kwargs(self, mock_get_lang):
        from utils.i18n import t
        result = t("ui.detected", distro="arch")
        self.assertEqual(result, "Detected: arch")

    # Test fallback to English when key missing in current language
    @patch("utils.i18n.get_lang", return_value="en")
    def test_missing_key_fallback_to_english(self, mock_get_lang):
        from utils.i18n import t, TRANSLATIONS
        # Temporarily add a key only to English
        TRANSLATIONS["en"]["test.key"] = "English only"
        result = t("test.key")
        self.assertEqual(result, "English only")
        del TRANSLATIONS["en"]["test.key"]

    # Test that missing key returns the key itself
    @patch("utils.i18n.get_lang", return_value="en")
    def test_missing_key_returns_key(self, mock_get_lang):
        from utils.i18n import t
        result = t("nonexistent.key.name")
        self.assertEqual(result, "nonexistent.key.name")

    # Test fallback to English for unsupported language
    @patch("utils.i18n.get_lang", return_value="fr")
    def test_unsupported_lang_falls_back_to_english(self, mock_get_lang):
        from utils.i18n import t
        result = t("ui.available_tools")
        self.assertEqual(result, "Available tools:")


# Test translation catalog consistency
class TestTranslationCatalog(TestCase):

    # Every supported language should define the same translation keys
    def test_supported_languages_have_same_keys(self):
        from utils.i18n import TRANSLATIONS

        baseline = set(TRANSLATIONS["en"])
        for lang, translations in TRANSLATIONS.items():
            with self.subTest(lang=lang):
                keys = set(translations)
                self.assertEqual(keys, baseline)

    # Literal translation dictionaries should not define duplicate keys
    def test_translation_source_has_no_duplicate_keys(self):
        source = (PROJECT_DIR / "utils" / "i18n.py").read_text()
        tree = ast.parse(source)
        duplicates = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                is_translations = any(
                    isinstance(target, ast.Name) and target.id == "TRANSLATIONS"
                    for target in node.targets
                )
            elif isinstance(node, ast.AnnAssign):
                is_translations = (
                    isinstance(node.target, ast.Name) and node.target.id == "TRANSLATIONS"
                )
            else:
                is_translations = False

            if not is_translations or not isinstance(node.value, ast.Dict):
                continue

            for lang_node, catalog_node in zip(node.value.keys, node.value.values):
                if not isinstance(lang_node, ast.Constant) or not isinstance(catalog_node, ast.Dict):
                    continue
                keys = [
                    key.value
                    for key in catalog_node.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                ]
                duplicates[lang_node.value] = [
                    key for key, count in Counter(keys).items() if count > 1
                ]

        self.assertEqual(duplicates, {"en": [], "zh": []})

    # Every literal t('key') usage should exist in the translation catalog
    def test_constant_translation_keys_exist(self):
        from utils.i18n import TRANSLATIONS

        used_keys = set()
        source_dirs = [PROJECT_DIR / "main.py", PROJECT_DIR / "tools", PROJECT_DIR / "utils"]
        files = []
        for path in source_dirs:
            if path.is_file():
                files.append(path)
            else:
                files.extend(path.rglob("*.py"))

        for file_path in files:
            tree = ast.parse(file_path.read_text(), filename=str(file_path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Name) or node.func.id != "t":
                    continue
                if not node.args:
                    continue
                key = node.args[0]
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    used_keys.add(key.value)

        missing = sorted(key for key in used_keys if key not in TRANSLATIONS["en"])
        self.assertEqual(missing, [])


# Test get_lang() and set_lang() functions
class TestLanguagePersistence(TestCase):

    # Reset global language state before each test
    def setUp(self):
        import utils.i18n
        utils.i18n._current_lang = None

    # Test that default language is English
    @patch("utils.i18n._load_config", return_value={})
    def test_default_language_is_english(self, mock_load):
        from utils.i18n import get_lang
        result = get_lang()
        self.assertEqual(result, "en")

    # Test loading language from config file
    @patch("utils.i18n._load_config", return_value={"lang": "zh"})
    def test_load_language_from_config(self, mock_load):
        from utils.i18n import get_lang
        result = get_lang()
        self.assertEqual(result, "zh")

    # Test that set_lang() persists to config
    @patch("utils.i18n._save_config")
    @patch("utils.i18n._load_config", return_value={})
    def test_set_language_persists(self, mock_load, mock_save):
        from utils.i18n import set_lang, get_lang
        set_lang("zh")
        self.assertEqual(get_lang(), "zh")
        mock_save.assert_called_once_with({"lang": "zh"})


# Test tool_display_name() and tool_description() functions
class TestToolDisplayNames(TestCase):

    # Reset global language state before each test
    def setUp(self):
        import utils.i18n
        utils.i18n._current_lang = None

    # Test tool display name lookup
    @patch("utils.i18n.get_lang", return_value="en")
    def test_tool_display_name(self, mock_get_lang):
        from utils.i18n import tool_display_name
        mock_tool = MagicMock()
        mock_tool.name = "mirror-optimizer"
        mock_tool.display_name = "Fallback Name"
        result = tool_display_name(mock_tool)
        self.assertEqual(result, "Optimize Mirrors")

    # Test tool description lookup
    @patch("utils.i18n.get_lang", return_value="en")
    def test_tool_description(self, mock_get_lang):
        from utils.i18n import tool_description
        mock_tool = MagicMock()
        mock_tool.name = "mirror-optimizer"
        mock_tool.description = "Fallback description"
        result = tool_description(mock_tool)
        self.assertIn("China mirrors", result)

    # Test fallback to tool.display_name when translation missing
    @patch("utils.i18n.get_lang", return_value="en")
    def test_tool_display_name_fallback(self, mock_get_lang):
        from utils.i18n import tool_display_name
        mock_tool = MagicMock()
        mock_tool.name = "nonexistent-tool"
        mock_tool.display_name = "Fallback Name"
        result = tool_display_name(mock_tool)
        self.assertEqual(result, "Fallback Name")


# Standalone test runner
def run_tests():
    print("Running i18n unit tests...")
    print("=" * 60)
    unittest_main(module=__name__, exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
