from pathlib import Path


def test_recorded_demo_is_self_contained_and_honest() -> None:
    html = Path("docs/index.html").read_text(encoding="utf-8")
    script = Path("docs/demo.js").read_text(encoding="utf-8")

    assert "Recorded behavior demo" in html
    assert "Not a live model connection" in html
    assert "Russell York" in html
    assert "https://cdn" not in html
    assert script.count('    visitor: "') == 4
    assert "emergency_help" in script
    assert "human_handoff" in script
