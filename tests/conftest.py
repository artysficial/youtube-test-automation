"""Shared fixtures: HTTP session, test data, optional Data API key, and a Playwright browser."""

from __future__ import annotations

import os

import pytest
import requests

pytest_plugins = ["results_plugin"]

# stable public test data: the first video ever uploaded, and Google for Developers' channel
VIDEO = {"id": "jNQXAC9IVRw", "title": "Me at the zoo", "channel": "jawed"}
CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw"
MISSING_VIDEO = "xxxxxxxxxx0"
BLOCK_SIGNS = ("before you continue", "unusual traffic", "confirm you're not a bot", "sign in to confirm")


@pytest.fixture(scope="session")
def http():
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (portfolio test automation; +https://artysficial.github.io/)"
    yield session
    session.close()


@pytest.fixture(scope="session")
def api_key():
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        pytest.skip("YOUTUBE_API_KEY not configured (add it as a repository secret to run Data API tests)")
    return key


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # CI uses Playwright's Chromium; locally BROWSER_CHANNEL=msedge or chrome reuses an installed browser
        channel = os.environ.get("BROWSER_CHANNEL") or None
        instance = p.chromium.launch(channel=channel, headless=True)
        yield instance
        instance.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(locale="en-US", viewport={"width": 1366, "height": 900})
    tab = context.new_page()
    yield tab
    context.close()


def skip_if_blocked(page) -> None:
    """YouTube sometimes shows a consent wall or bot check to automated browsers in CI.
    That is an environment limitation, not a product defect: report it as blocked."""
    text = page.content().lower()
    if any(sign in text for sign in BLOCK_SIGNS) or "consent.youtube.com" in page.url:
        pytest.skip("blocked: consent or bot check shown to the automated browser")
