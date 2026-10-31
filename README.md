# YouTube Test Automation

[![Tests and dashboard](https://github.com/artysficial/youtube-test-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/artysficial/youtube-test-automation/actions/workflows/tests.yml)
[![Dashboard](https://img.shields.io/badge/dashboard-live-0071e3)](https://artysficial.github.io/youtube-test-automation/)

Automated checks of YouTube's public surfaces, from API contracts to a real browser, with a dashboard published on
every run.

**[View the live dashboard →](https://artysficial.github.io/youtube-test-automation/)**

## Layers

| Layer | What is checked | Needs a key? |
| --- | --- | --- |
| oEmbed API | documented fields, metadata accuracy, safe iframe HTML, `maxwidth`, error handling, response time | No |
| Channel RSS feed | valid Atom, 1–15 entries, newest first, media metadata | No |
| Thumbnail CDN | JPEG formats per size, cache headers | No |
| Data API v3 | invalid/missing key errors (keyless); video details, ISO-8601 duration, pagination without duplicates, `maxResults` cap, oEmbed vs API consistency | Partly |
| Data API contract | the public Discovery document: `videos.list` shape, required `part`, `maxResults` caps, `order=date` and token paging, Video schema (ISO-8601 duration, uint64 view count), key and read-only scope | No |
| Web platform | HTTP→HTTPS, HSTS, clickjacking protection, robots.txt, embed page | No |
| UI smoke (Playwright) | watch page title and player, search results, embed player, load-time budget, accessibility basics | No |

## Design choices

- **Official and public surfaces first.** Most coverage comes from the oEmbed API, feeds, CDN and the Data API,
  which are stable and allowed for automated use. The browser suite is a small smoke layer.
- **Blocked is not failed.** YouTube may show automated browsers a consent wall or bot check in CI. Those checks
  are reported as *blocked* on the dashboard instead of turning the build red, so real regressions stay visible.
- **Retries for the network, not for bugs.** Each check is retried once (`pytest-rerunfailures`) to absorb a
  network blip; a second failure is reported.
- **Polite.** Read-only, public data, a few page loads per weekly run.

## Run it

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium      # or set BROWSER_CHANNEL=msedge / chrome to reuse an installed browser
export YOUTUBE_API_KEY=...                 # optional: enables the Data API checks
python -m pytest && python tools/build_dashboard.py
```

In CI, add `YOUTUBE_API_KEY` as a repository secret to run the keyed Data API checks. Without it, the Data API
contract layer still verifies the API's published methods, limits and schema on every run.

Built by [Rahmadani Tyas Ningrum](https://artysficial.github.io/) · MIT licence
