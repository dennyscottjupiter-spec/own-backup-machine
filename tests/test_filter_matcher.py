import pytest

from obm.filter import matcher

CASES = [
    ("C:\\Users\\me\\docs\\report.docx", True, ""),
    ("C:\\Users\\me\\project\\node_modules\\pkg\\index.js", False, "blocked-dir:node_modules"),
    ("C:\\Users\\me\\thumbs.db", False, "blocked-file:thumbs.db"),
    ("C:\\Users\\me\\build.log", False, "blocked-ext:.log"),
    ("C:\\Users\\me\\AppData\\Local\\Temp\\scratch.txt", False, "blocked-pattern:\\\\appdata\\\\local\\\\temp\\\\"),
    ("C:\\Users\\me\\mystery.xyz123", True, ""),  # unrecognised extension is KEPT
    ("C:\\Users\\me\\notes", True, ""),  # no extension at all is KEPT
]


@pytest.mark.parametrize("path,expect_keep,expect_rule_prefix", CASES)
def test_matcher_table(path, expect_keep, expect_rule_prefix):
    keep, rule = matcher.match(path)
    assert keep is expect_keep
    if expect_keep:
        assert rule == ""
    else:
        assert rule == expect_rule_prefix


def test_user_exclude_drops_subtree():
    keep, rule = matcher.match("C:\\Users\\me\\Secret\\file.txt", extra_excludes=["C:\\Users\\me\\Secret"])
    assert keep is False
    assert rule == "user-exclude"


def test_user_exclude_does_not_affect_siblings():
    keep, _ = matcher.match("C:\\Users\\me\\NotSecret\\file.txt", extra_excludes=["C:\\Users\\me\\Secret"])
    assert keep is True
