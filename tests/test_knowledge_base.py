import pytest

from knowledge_base import _get_required, filter_sections, get_section_context


@pytest.fixture
def sample_kb() -> dict:
    return {
        "primary": {
            "believe_competitive_positioning": {"Strength": "Local editorial expertise"},
            "believe_company_profile": {"Overview": "Independent distributor profile"},
        },
        "secondary": {
            "market_trends_DE_UK_FR": {
                "2026 April": {
                    "Germany": "Germany trend",
                    "UK": "UK trend",
                    "France": "France trend",
                }
            },
            "platform_policy_updates": {
                "2026 April": {"Spotify": "Policy update"}
            },
            "streaming_platforms_landscape": {
                "2026 April": {"Spotify": "Landscape update"}
            },
            "competitor_intelligence": {
                "2026 April": {"AWAL": "Competitive move"}
            },
            "independent_music_industry": {
                "2026 April": {"Market Size": "30.4% share"}
            },
        },
    }


def test_get_required_returns_value() -> None:
    assert _get_required({"k": 1}, "k", "ctx") == 1


def test_get_required_raises_with_available_keys() -> None:
    with pytest.raises(ValueError) as exc:
        _get_required({"a": 1, "b": 2}, "c", "my_context")

    msg = str(exc.value)
    assert "my_context" in msg
    assert "Available keys" in msg
    assert "a" in msg and "b" in msg


def test_filter_sections_rejects_unsupported_section(sample_kb: dict) -> None:
    with pytest.raises(ValueError, match="Unsupported section"):
        filter_sections(sample_kb, "unknown_section", "2026 April")


def test_filter_sections_market_trends_requires_country(sample_kb: dict) -> None:
    with pytest.raises(ValueError, match="Country is required"):
        filter_sections(sample_kb, "market_trends", "2026 April")


def test_filter_sections_platform_updates_contains_expected_headers(sample_kb: dict) -> None:
    content = filter_sections(sample_kb, "platform_updates", "2026 April")
    assert "# Platform policy updates for 2026 April:" in content
    assert "# Streaming platforms landscape for 2026 April:" in content
    assert "Spotify -- Policy update" in content


def test_get_section_context_requires_list_inputs(sample_kb: dict) -> None:
    with pytest.raises(ValueError, match="sections must be a list"):
        get_section_context(sample_kb, "market_trends", "2026 April", ["Germany"])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="markets must be a list"):
        get_section_context(sample_kb, ["market_trends"], "2026 April", "Germany")  # type: ignore[arg-type]


def test_get_section_context_market_trends_for_multiple_markets(sample_kb: dict) -> None:
    content = get_section_context(
        sample_kb,
        ["market_trends"],
        "2026 April",
        ["Germany", "UK"],
    )
    assert "# Market trends for Germany in 2026 April:" in content
    assert "# Market trends for UK in 2026 April:" in content
