import pytest

from docqa.chunker import chunk_pages, split_into_chunks

TEN_WORDS = "one two three four five six seven eight nine ten"


def test_chunks_share_overlap_words():
    chunks = split_into_chunks(TEN_WORDS, 4, 1)
    assert chunks == [
        "one two three four",
        "four five six seven",
        "seven eight nine ten",
    ]


def test_last_chunk_can_be_shorter():
    chunks = split_into_chunks(TEN_WORDS + " eleven", 4, 1)
    assert chunks[-1] == "ten eleven"
    assert len(chunks) == 4


def test_empty_text_gives_no_chunks():
    assert split_into_chunks("   ", 4, 1) == []


@pytest.mark.parametrize("chunk_size, overlap", [(0, 0), (4, 4), (4, 5), (4, -1)])
def test_bad_settings_are_rejected(chunk_size, overlap):
    with pytest.raises(ValueError):
        split_into_chunks(TEN_WORDS, chunk_size, overlap)


def test_chunks_remember_their_page():
    pages = [
        {"page": 1, "text": "alpha beta gamma"},
        {"page": 2, "text": ""},
        {"page": 3, "text": "delta epsilon"},
    ]
    chunks = chunk_pages(pages, 2, 0)
    assert chunks == [
        {"id": 1, "page": 1, "text": "alpha beta"},
        {"id": 2, "page": 1, "text": "gamma"},
        {"id": 3, "page": 3, "text": "delta epsilon"},
    ]
