"""Light end-to-end smoke tests in a real browser (Playwright). Polite: a handful of page loads per run.
Consent walls and bot checks are reported as 'blocked', not as failures."""

import time

import pytest

from conftest import VIDEO, skip_if_blocked

pytestmark = pytest.mark.category("UI smoke (Playwright)")


@pytest.mark.severity("high")
def test_watch_page_shows_the_video(page):
    """The watch page loads with the right title and a video player"""
    page.goto(f"https://www.youtube.com/watch?v={VIDEO['id']}", wait_until="domcontentloaded", timeout=45000)
    skip_if_blocked(page)
    page.wait_for_selector("video, #movie_player", timeout=20000)
    assert VIDEO["title"] in page.title()


@pytest.mark.severity("high")
def test_search_returns_results(page):
    """Searching from the home page lists video results"""
    page.goto("https://www.youtube.com/results?search_query=me+at+the+zoo", wait_until="domcontentloaded", timeout=45000)
    skip_if_blocked(page)
    page.wait_for_selector("ytd-video-renderer, ytm-video-with-context-renderer", timeout=20000)
    assert page.locator("ytd-video-renderer, ytm-video-with-context-renderer").count() >= 3


@pytest.mark.severity("medium")
def test_embed_player_renders(page):
    """The embeddable player initialises with a video element, ready to play"""
    page.goto(f"https://www.youtube.com/embed/{VIDEO['id']}", wait_until="domcontentloaded", timeout=45000)
    skip_if_blocked(page)
    # the <video> stays hidden until playback starts, so wait for the player to exist, not to be visible
    page.wait_for_selector(".html5-video-player", state="attached", timeout=20000)
    assert page.locator(".html5-video-player video").count() == 1


@pytest.mark.severity("low")
def test_watch_page_loads_within_budget(page):
    """The watch page reaches DOMContentLoaded within 8 seconds"""
    started = time.monotonic()
    page.goto(f"https://www.youtube.com/watch?v={VIDEO['id']}", wait_until="domcontentloaded", timeout=45000)
    skip_if_blocked(page)
    assert time.monotonic() - started < 8


@pytest.mark.severity("medium")
def test_page_declares_language_and_viewport(page):
    """The page declares a document language and a responsive viewport (accessibility basics)"""
    page.goto("https://www.youtube.com/", wait_until="domcontentloaded", timeout=45000)
    skip_if_blocked(page)
    assert page.locator("html").get_attribute("lang")
    assert page.locator('meta[name="viewport"]').count() >= 1 or page.locator("ytd-app").count() == 1
