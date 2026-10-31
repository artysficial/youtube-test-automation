"""YouTube Data API v3. Negative tests run always; positive tests need YOUTUBE_API_KEY."""

import re

import pytest

from conftest import CHANNEL_ID, MISSING_VIDEO, VIDEO

pytestmark = pytest.mark.category("Data API v3")
BASE = "https://www.googleapis.com/youtube/v3"
ISO_DURATION = re.compile(r"^P(T(\d+H)?(\d+M)?(\d+S)?|\d+D.*)$")


@pytest.mark.severity("high")
def test_invalid_api_key_is_refused_with_a_clear_error(http):
    """An invalid key gets 400 with a machine-readable reason (keyless test)"""
    response = http.get(f"{BASE}/videos", params={"part": "snippet", "id": VIDEO["id"], "key": "invalid-key"}, timeout=15)
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == 400
    assert any(e.get("reason") in ("keyInvalid", "badRequest") for e in error["errors"]) or "API key" in error["message"]


@pytest.mark.severity("medium")
def test_missing_key_is_refused(http):
    """A request without credentials is refused (keyless test)"""
    response = http.get(f"{BASE}/videos", params={"part": "snippet", "id": VIDEO["id"]}, timeout=15)
    assert response.status_code in (401, 403)


@pytest.mark.severity("high")
def test_video_details_match_the_known_video(http, api_key):
    """videos.list returns the right title, channel and an ISO-8601 duration"""
    item = http.get(f"{BASE}/videos", params={"part": "snippet,contentDetails,statistics", "id": VIDEO["id"], "key": api_key}, timeout=15).json()["items"][0]
    assert item["snippet"]["title"] == VIDEO["title"]
    assert item["snippet"]["channelTitle"] == VIDEO["channel"]
    assert ISO_DURATION.match(item["contentDetails"]["duration"])
    assert int(item["statistics"]["viewCount"]) > 1_000_000


@pytest.mark.severity("medium")
def test_unknown_video_returns_an_empty_list(http, api_key):
    """A missing video id yields zero items, not an error"""
    body = http.get(f"{BASE}/videos", params={"part": "snippet", "id": MISSING_VIDEO, "key": api_key}, timeout=15).json()
    assert body["items"] == [] and body["pageInfo"]["totalResults"] == 0


@pytest.mark.severity("medium")
def test_search_pagination_returns_distinct_pages(http, api_key):
    """search.list pages with nextPageToken and returns no duplicates across pages"""
    params = {"part": "snippet", "channelId": CHANNEL_ID, "maxResults": 5, "order": "date", "type": "video", "key": api_key}
    first = http.get(f"{BASE}/search", params=params, timeout=15).json()
    second = http.get(f"{BASE}/search", params={**params, "pageToken": first["nextPageToken"]}, timeout=15).json()
    ids = [i["id"]["videoId"] for i in first["items"] + second["items"]]
    assert len(ids) == len(set(ids)) == 10


@pytest.mark.severity("low")
def test_max_results_above_fifty_is_rejected(http, api_key):
    """maxResults is capped at 50"""
    response = http.get(f"{BASE}/search", params={"part": "snippet", "q": "test", "maxResults": 51, "key": api_key}, timeout=15)
    assert response.status_code == 400


@pytest.mark.severity("medium")
def test_oembed_and_data_api_agree(http, api_key):
    """oEmbed and the Data API report the same title (cross-source consistency)"""
    oembed = http.get("https://www.youtube.com/oembed", params={"url": f"https://www.youtube.com/watch?v={VIDEO['id']}", "format": "json"}, timeout=15).json()
    api = http.get(f"{BASE}/videos", params={"part": "snippet", "id": VIDEO["id"], "key": api_key}, timeout=15).json()["items"][0]
    assert oembed["title"] == api["snippet"]["title"]
