"""Builds site/index.html from reports/results.json."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from automation_dashboard import build  # noqa: E402

build(
    ROOT,
    title="YouTube Test Automation",
    eyebrow="SDET · API & UI automation",
    summary="End-to-end checks of YouTube's public surfaces: oEmbed, channel feeds, the thumbnail CDN, the Data API v3 and a polite browser smoke suite, run every week in CI.",
    repo="youtube-test-automation",
    layers={
        "oEmbed API": "Embed metadata contract, error handling, response time",
        "Channel RSS feed": "Atom validity, ordering, media metadata",
        "Thumbnail CDN": "Image formats, caching headers",
        "Data API v3": "Auth errors (keyless), video details, pagination, limits, cross-source consistency",
        "Web platform": "HTTPS, HSTS, clickjacking protection, robots.txt, embed page",
        "UI smoke (Playwright)": "Watch page, search, embed player, load budget, accessibility basics",
    },
    notes=[
        "Blocked means YouTube showed a consent wall or bot check to the CI browser. That is an environment limit, not a product defect, so it is reported separately instead of failing the build.",
        "Not configured means the check needs a YouTube Data API key; add YOUTUBE_API_KEY as a repository secret to run them.",
        "The suite only reads public data and keeps UI traffic to a few page loads a week.",
    ],
)
