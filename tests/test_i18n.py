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


# Regression: ISSUE-017. config.json may be corrupt, missing, or hold a value
# of the wrong type. None of these should ever crash main.py. _load_config
# must always return a dict, and get_lang/set_lang must always succeed with
# a valid SUPPORTED_LANGS code.
class TestConfigResilience(TestCase):
    """Test that i18n never crashes on corrupt config.json.

    Each test writes a bad config, resets the cached _current_lang, and
    verifies that get_lang() returns DEFAULT_LANG ("en") without raising.
    Uses a temp file via monkey-patching CONFIG_PATH so the real
    config.json is not touched.
    每个测试写入坏 config、重置 _current_lang 缓存，验证 get_lang()
    返回 DEFAULT_LANG ("en") 且不抛异常。通过 monkey-patch CONFIG_PATH
    使用临时文件，不触碰真实 config.json。
    """

    def setUp(self):
        import utils.i18n
        utils.i18n._current_lang = None
        # Point CONFIG_PATH at a fresh temp file for the duration of each test
        import tempfile
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self._tmp_path = Path(self._tmp.name)
        self._tmp.close()
        self._orig_config = utils.i18n.CONFIG_PATH
        utils.i18n.CONFIG_PATH = self._tmp_path

    def tearDown(self):
        import utils.i18n
        utils.i18n.CONFIG_PATH = self._orig_config
        self._tmp_path.unlink(missing_ok=True)

    def _reset_cache(self):
        import utils.i18n
        utils.i18n._current_lang = None

    def _assert_default(self, body: str, label: str):
        self._tmp_path.write_text(body)
        self._reset_cache()
        from utils.i18n import get_lang
        self.assertEqual(
            get_lang(), "en",
            f"corrupt config {label!r} should fall back to 'en'",
        )

    def test_corrupt_json_falls_back(self):
        self._assert_default("{this is not valid json}", "{x}")

    def test_empty_file_falls_back(self):
        self._assert_default("", "empty")

    def test_null_root_falls_back(self):
        self._assert_default("null", "null")

    def test_string_root_falls_back(self):
        self._assert_default('"just a string"', "str")

    def test_list_root_falls_back(self):
        self._assert_default("[1, 2, 3]", "list")

    def test_number_root_falls_back(self):
        self._assert_default("42", "number")

    def test_lang_wrong_type_falls_back(self):
        self._assert_default('{"lang": 12345}', "lang=number")

    def test_lang_unknown_code_falls_back(self):
        self._assert_default('{"lang": "jp"}', "lang=jp")

    def test_lang_null_falls_back(self):
        self._assert_default('{"lang": null}', "lang=null")

    def test_set_lang_invalid_string_falls_back(self):
        # An external caller passing a bad value should not crash the program.
        # _save_config will still be called (with the default) so the next
        # set_lang('en') or get_lang() lands on a clean dict.
        from utils.i18n import set_lang, get_lang
        with patch("utils.i18n._save_config") as mock_save:
            set_lang("not-a-real-lang")
        self.assertEqual(get_lang(), "en")
        # _save_config should have been called with a dict containing the
        # coerced default. The exact dict from a fresh temp file is {}.
        mock_save.assert_called_once_with({"lang": "en"})

    def test_set_lang_non_string_falls_back(self):
        from utils.i18n import set_lang, get_lang
        with patch("utils.i18n._save_config"):
            set_lang(None)  # type: ignore[arg-type]
        self.assertEqual(get_lang(), "en")

    def test_corrupt_config_self_heals_on_next_set_lang(self):
        # Real-world flow: user has a bad config, runs `set_lang("zh")`,
        # next time the file is read it should be a clean {"lang": "zh"}.
        import json
        self._tmp_path.write_text("{not json")
        self._reset_cache()
        from utils.i18n import set_lang
        set_lang("zh")
        # Parse the saved file rather than string-compare (it's pretty-printed).
        self.assertEqual(
            json.loads(self._tmp_path.read_text()),
            {"lang": "zh"},
            "next set_lang should overwrite the corrupt file with a clean dict",
        )


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
