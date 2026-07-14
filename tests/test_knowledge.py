from nyxora_concierge.knowledge import KnowledgeBase


def test_search_ranks_relevant_entry() -> None:
    matches = KnowledgeBase.from_package().search("How do I prepare before treatment?")
    assert matches
    assert matches[0].entry_id == "preparation"


def test_search_returns_empty_for_unrelated_query() -> None:
    assert KnowledgeBase.from_package().search("nearby restaurant recommendation") == []

