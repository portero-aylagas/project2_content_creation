from pathlib import Path

from document_processor import load_knowledge_base, read_file_base


def test_read_file_base_parses_nested_headings(tmp_path: Path) -> None:
    md_file = tmp_path / "sample.md"
    md_file.write_text(
        "\n".join(
            [
                "# Alpha",
                "## One",
                "Line 1",
                "Line 2",
                "## Two",
                "Line 3",
                "# Beta",
                "Line B",
            ]
        ),
        encoding="utf-8",
    )

    parsed = read_file_base(md_file)

    assert parsed == {
        "Alpha": {
            "One": "Line 1\nLine 2",
            "Two": "Line 3",
        },
        "Beta": "Line B",
    }


def test_read_file_base_returns_plain_text_without_headings(tmp_path: Path) -> None:
    md_file = tmp_path / "plain.md"
    md_file.write_text(" first line \nsecond line\n", encoding="utf-8")

    parsed = read_file_base(md_file)

    assert parsed == "first line\nsecond line"


def test_load_knowledge_base_from_custom_path(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    secondary = tmp_path / "secondary"
    primary.mkdir()
    secondary.mkdir()

    (primary / "doc_a.md").write_text("# A\nValue A\n", encoding="utf-8")
    (secondary / "doc_b.md").write_text("# B\nValue B\n", encoding="utf-8")

    kb = load_knowledge_base(base_path=tmp_path)

    assert "primary" in kb
    assert "secondary" in kb
    assert "doc_a" in kb["primary"]
    assert "doc_b" in kb["secondary"]
