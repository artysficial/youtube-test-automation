"""Data API v3 contract, read from Google's public Discovery document. Keyless, so it runs on every build and
pins down the methods, limits and schema the keyed Data API tests rely on."""

import pytest

pytestmark = pytest.mark.category("Data API contract")
DISCOVERY = "https://www.googleapis.com/discovery/v1/apis/youtube/v3/rest"


@pytest.fixture(scope="module")
def spec(http):
    response = http.get(DISCOVERY, timeout=15)
    assert response.status_code == 200, f"discovery document returned {response.status_code}"
    return response.json()


def method(spec, resource, name="list"):
    return spec["resources"][resource]["methods"][name]


@pytest.mark.severity("high")
def test_discovery_document_is_public(http):
    """The API description is served without a key as JSON for youtube v3 over REST"""
    response = http.get(DISCOVERY, timeout=15)
    assert response.status_code == 200 and response.headers["Content-Type"].startswith("application/json")
    body = response.json()
    assert (body["name"], body["version"], body["protocol"]) == ("youtube", "v3", "rest")


@pytest.mark.severity("high")
def test_videos_list_is_a_get_that_requires_part(spec):
    """videos.list is GET youtube/v3/videos, needs part and returns a VideoListResponse"""
    videos = method(spec, "videos")
    assert videos["httpMethod"] == "GET" and videos["path"] == "youtube/v3/videos"
    assert videos["parameters"]["part"]["required"] is True
    assert videos["parameters"]["id"]["repeated"] is True
    assert videos["response"]["$ref"] == "VideoListResponse"


@pytest.mark.severity("high")
def test_core_list_methods_require_part(spec):
    """videos, search, channels, playlistItems and commentThreads all require part and page with pageToken"""
    for resource in ("videos", "search", "channels", "playlistItems", "commentThreads"):
        params = method(spec, resource)["parameters"]
        assert params["part"]["required"] is True and params["part"]["repeated"] is True, resource
        assert params["pageToken"]["type"] == "string", resource


@pytest.mark.severity("medium")
def test_max_results_caps_are_documented(spec):
    """search, videos, channels and playlistItems cap maxResults at 50 (the limit the keyed test exercises)"""
    for resource in ("search", "videos", "channels", "playlistItems"):
        limit = method(spec, resource)["parameters"]["maxResults"]
        assert limit["type"] == "integer" and limit["maximum"] == "50", resource
        assert int(limit["default"]) == 5, resource


@pytest.mark.severity("medium")
def test_search_supports_date_order_and_token_paging(spec):
    """search.list offers order=date and pageToken, and its response carries nextPageToken and pageInfo"""
    params = method(spec, "search")["parameters"]
    assert "date" in params["order"]["enum"] and params["order"]["default"] == "relevance"
    assert params["pageToken"]["type"] == "string"
    assert {"nextPageToken", "prevPageToken", "pageInfo", "items"} <= set(spec["schemas"]["SearchListResponse"]["properties"])
    assert {"videoId", "channelId", "playlistId"} <= set(spec["schemas"]["ResourceId"]["properties"])


@pytest.mark.severity("medium")
def test_video_schema_documents_the_fields_under_test(spec):
    """A Video has snippet, contentDetails and statistics; duration is ISO 8601 and viewCount a uint64 string"""
    schemas = spec["schemas"]
    assert {"id", "kind", "etag", "snippet", "contentDetails", "statistics"} <= set(schemas["Video"]["properties"])
    assert "ISO 8601" in schemas["VideoContentDetails"]["properties"]["duration"]["description"]
    views = schemas["VideoStatistics"]["properties"]["viewCount"]
    assert (views["type"], views["format"]) == ("string", "uint64")
    assert {"resultsPerPage", "totalResults"} <= set(schemas["PageInfo"]["properties"])


@pytest.mark.severity("low")
def test_key_and_read_only_scope_are_offered(spec):
    """Callers can authenticate with an API key or the read-only OAuth scope"""
    assert spec["parameters"]["key"]["location"] == "query"
    assert "https://www.googleapis.com/auth/youtube.readonly" in spec["auth"]["oauth2"]["scopes"]
