"""oEmbed API: the public, keyless endpoint other sites use to embed YouTube videos."""

import pytest

from conftest import MISSING_VIDEO, VIDEO

pytestmark = pytest.mark.category("oEmbed API")
OEMBED = "https://www.youtube.com/oembed"


def oembed(http, video_id, **params):
    return http.get(OEMBED, params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json", **params}, timeout=15)


@pytest.mark.severity("high")
def test_oembed_returns_the_documented_fields(http):
    """oEmbed returns type, title, author, provider, thumbnail and embed HTML"""
    body = oembed(http, VIDEO["id"]).json()
    for field in ("type", "version", "title", "author_name", "author_url", "provider_name", "thumbnail_url", "html", "width", "height"):
        assert field in body, f"missing {field}"
    assert body["type"] == "video" and body["provider_name"] == "YouTube"


@pytest.mark.severity("high")
def test_oembed_metadata_matches_the_video(http):
    """Title and channel in oEmbed match the known video"""
    body = oembed(http, VIDEO["id"]).json()
    assert body["title"] == VIDEO["title"]
    assert body["author_name"] == VIDEO["channel"]


@pytest.mark.severity("medium")
def test_embed_html_is_a_privacy_safe_iframe(http):
    """Embed HTML is a single iframe pointing at youtube.com/embed with the video id"""
    html = oembed(http, VIDEO["id"]).json()["html"]
    assert html.startswith("<iframe") and f"youtube.com/embed/{VIDEO['id']}" in html
    assert "<script" not in html


@pytest.mark.severity("medium")
def test_maxwidth_is_respected(http):
    """maxwidth scales the embed down"""
    body = oembed(http, VIDEO["id"], maxwidth=320).json()
    assert body["width"] <= 320


@pytest.mark.severity("medium")
def test_unknown_video_is_rejected(http):
    """An id that does not exist returns an error status, not an embed"""
    assert oembed(http, MISSING_VIDEO).status_code in (400, 401, 404)


@pytest.mark.severity("low")
def test_non_youtube_url_is_rejected(http):
    """oEmbed refuses URLs from other sites"""
    response = http.get(OEMBED, params={"url": "https://example.com/watch?v=abc", "format": "json"}, timeout=15)
    assert response.status_code in (400, 404)


@pytest.mark.severity("low")
def test_oembed_responds_quickly(http):
    """oEmbed answers within 2 seconds"""
    response = oembed(http, VIDEO["id"])
    assert response.elapsed.total_seconds() < 2
