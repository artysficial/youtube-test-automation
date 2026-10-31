"""Channel RSS feeds and thumbnail CDN: public, keyless delivery surfaces."""

import xml.etree.ElementTree as ET
from datetime import datetime

import pytest

from conftest import CHANNEL_ID, VIDEO

NS = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}


@pytest.fixture(scope="module")
def feed(http):
    response = http.get("https://www.youtube.com/feeds/videos.xml", params={"channel_id": CHANNEL_ID}, timeout=15)
    if response.status_code >= 500:
        pytest.skip(f"blocked: feed service returned {response.status_code}")
    assert response.status_code == 200
    return ET.fromstring(response.content)


@pytest.mark.category("Channel RSS feed")
@pytest.mark.severity("high")
def test_feed_is_valid_atom_for_the_channel(feed):
    """The channel feed is valid Atom and identifies the right channel"""
    assert feed.tag == "{http://www.w3.org/2005/Atom}feed"
    # the feed carries the id with or without its "UC" prefix
    assert CHANNEL_ID.endswith(feed.find("yt:channelId", NS).text)


@pytest.mark.category("Channel RSS feed")
@pytest.mark.severity("medium")
def test_feed_lists_up_to_fifteen_recent_videos(feed):
    """The feed contains between 1 and 15 entries, each with a video id and link"""
    entries = feed.findall("atom:entry", NS)
    assert 1 <= len(entries) <= 15
    for entry in entries:
        assert len(entry.find("yt:videoId", NS).text) == 11
        assert entry.find("atom:link", NS).get("href").startswith("https://www.youtube.com/")


@pytest.mark.category("Channel RSS feed")
@pytest.mark.severity("medium")
def test_feed_is_newest_first(feed):
    """Entries are ordered newest first"""
    dates = [datetime.fromisoformat(e.find("atom:published", NS).text) for e in feed.findall("atom:entry", NS)]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.category("Channel RSS feed")
@pytest.mark.severity("low")
def test_entries_carry_media_metadata(feed):
    """Each entry has a media title and thumbnail"""
    for entry in feed.findall("atom:entry", NS):
        group = entry.find("media:group", NS)
        assert group.find("media:title", NS).text
        assert group.find("media:thumbnail", NS).get("url").startswith("https://")


@pytest.mark.category("Thumbnail CDN")
@pytest.mark.severity("high")
@pytest.mark.parametrize("size", ["default", "mqdefault", "hqdefault"])
def test_thumbnails_are_served_as_jpeg(http, size):
    """Standard thumbnail sizes are served as JPEG from the image CDN"""
    response = http.get(f"https://i.ytimg.com/vi/{VIDEO['id']}/{size}.jpg", timeout=15)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content[:3] == b"\xff\xd8\xff"


@pytest.mark.category("Thumbnail CDN")
@pytest.mark.severity("low")
def test_thumbnails_are_cacheable(http):
    """Thumbnails are sent with cache headers for CDN efficiency"""
    response = http.get(f"https://i.ytimg.com/vi/{VIDEO['id']}/hqdefault.jpg", timeout=15)
    assert "max-age" in response.headers.get("cache-control", "")
