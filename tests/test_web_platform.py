"""youtube.com as a web platform: security headers, crawler policy and the embed player (HTTP level)."""

import pytest

from conftest import VIDEO

pytestmark = pytest.mark.category("Web platform")


@pytest.fixture(scope="module")
def home(http):
    return http.get("https://www.youtube.com/", timeout=20)


@pytest.mark.severity("high")
def test_https_is_enforced(http):
    """Plain HTTP redirects to HTTPS"""
    response = http.get("http://www.youtube.com/", allow_redirects=False, timeout=15)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].startswith("https://")


@pytest.mark.severity("medium")
def test_home_sends_hsts(home):
    """The home page sends Strict-Transport-Security"""
    assert "max-age" in home.headers.get("strict-transport-security", "")


@pytest.mark.severity("medium")
def test_home_cannot_be_framed_by_other_sites(home):
    """The home page refuses to be framed (clickjacking protection)"""
    xfo = home.headers.get("x-frame-options", "").upper()
    csp = home.headers.get("content-security-policy", "")
    assert xfo in ("SAMEORIGIN", "DENY") or "frame-ancestors" in csp


@pytest.mark.severity("low")
def test_robots_txt_publishes_a_sitemap(http):
    """robots.txt exists and points crawlers at sitemaps"""
    response = http.get("https://www.youtube.com/robots.txt", timeout=15)
    assert response.status_code == 200 and "Sitemap:" in response.text


@pytest.mark.severity("high")
def test_embed_player_page_loads(http):
    """The embed player page for the video is served"""
    response = http.get(f"https://www.youtube.com/embed/{VIDEO['id']}", timeout=20)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
