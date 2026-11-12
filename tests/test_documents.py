from docqa import config, documents


def test_saved_documents_can_be_found_again():
    documents.clear()
    document_id = documents.save_document("a.pdf", 1, [], None)
    assert len(document_id) == 32
    assert documents.get_document(document_id)["filename"] == "a.pdf"
    assert documents.get_document("not-a-real-id") is None


def test_oldest_document_is_dropped_when_full(monkeypatch):
    documents.clear()
    monkeypatch.setattr(config, "MAX_DOCUMENTS", 2)
    clock = {"now": 1000.0}
    monkeypatch.setattr(documents.time, "time", lambda: clock["now"])

    first = documents.save_document("first.pdf", 1, [], None)
    clock["now"] += 1
    second = documents.save_document("second.pdf", 1, [], None)
    clock["now"] += 1
    documents.get_document(first)  # using it makes "second" the least recently used
    clock["now"] += 1
    third = documents.save_document("third.pdf", 1, [], None)

    assert documents.get_document(first) is not None
    assert documents.get_document(second) is None
    assert documents.get_document(third) is not None


def test_documents_expire_after_ttl(monkeypatch):
    documents.clear()
    monkeypatch.setattr(config, "DOCUMENT_TTL_MINUTES", 60)
    clock = {"now": 1000.0}
    monkeypatch.setattr(documents.time, "time", lambda: clock["now"])

    document_id = documents.save_document("a.pdf", 1, [], None)
    clock["now"] += 59 * 60
    assert documents.get_document(document_id) is not None  # this use resets the timer
    clock["now"] += 61 * 60
    assert documents.get_document(document_id) is None
