from obm.filter import classify
from obm.winapi.constants import (
    FILE_ATTRIBUTE_OFFLINE,
    FILE_ATTRIBUTE_PINNED,
    FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS,
    FILE_ATTRIBUTE_RECALL_ON_OPEN,
)

MB = 1024 * 1024


def test_offline_is_placeholder():
    assert classify.is_placeholder(FILE_ATTRIBUTE_OFFLINE) is True


def test_recall_on_open_is_placeholder():
    assert classify.is_placeholder(FILE_ATTRIBUTE_RECALL_ON_OPEN) is True


def test_recall_on_data_access_is_placeholder():
    assert classify.is_placeholder(FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS) is True


def test_pinned_alone_is_not_a_placeholder():
    assert classify.is_placeholder(FILE_ATTRIBUTE_PINNED) is False


def test_pinned_combined_with_cloud_flag_is_still_a_placeholder():
    assert classify.is_placeholder(FILE_ATTRIBUTE_PINNED | FILE_ATTRIBUTE_OFFLINE) is True


def test_big_tag_threshold():
    tags = classify.classify_tags(attributes=0, size=100 * MB, big_file_mb=100)
    assert "big" in tags
    tags_small = classify.classify_tags(attributes=0, size=99 * MB, big_file_mb=100)
    assert "big" not in tags_small


def test_category_unknown_for_unrecognised_extension():
    assert classify.category_of("C:\\f.xyz123") == "unknown"


def test_category_known_extension():
    assert classify.category_of("C:\\f.pdf") == "document"


def test_gguf_is_its_own_llm_model_category():
    assert classify.category_of("C:\\models\\llama-3-8b.gguf") == "llm model"


def test_iso_stays_in_the_archive_category():
    assert classify.category_of("C:\\images\\win11.iso") == "archive"
