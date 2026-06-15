#!/usr/bin/env python3
"""Tests for official-docs alignment: X-Api-Version, rate limiting, catalog
coverage, new typed wrappers and the docs page parser."""

from unittest.mock import Mock

import pytest

from atomgit_sdk import DEFAULT_API_CATALOG, AtomGitClient, AtomGitConfig
from atomgit_sdk.api_catalog import _OFFICIAL_ENTRIES, _parse_endpoint_page
from atomgit_sdk.exceptions import AtomGitAPIError, RateLimitError


def make_client(**kwargs):
    config = AtomGitConfig(
        token="test-token",
        owner="example-org",
        repo="example-repo",
        base_url="https://api.atomgit.com",
    )
    return AtomGitClient(config, **kwargs)


# --------------------------------------------------------------------------
# X-Api-Version header (official docs mandate it)
# --------------------------------------------------------------------------
def test_default_api_version_header():
    client = make_client()
    assert client.session.headers["X-Api-Version"] == "2023-02-21"


def test_custom_api_version_header():
    client = make_client(api_version="2099-01-01")
    assert client.session.headers["X-Api-Version"] == "2099-01-01"


# --------------------------------------------------------------------------
# Rate limiting (x-ratelimit-remaining == 0 → RateLimitError)
# --------------------------------------------------------------------------
def _rate_limited_response(status=403, remaining="0"):
    resp = Mock(status_code=status)
    resp.headers = {
        "x-ratelimit-remaining": remaining,
        "x-ratelimit-limit": "5000",
        "x-ratelimit-used": "5000",
        "x-ratelimit-reset": "1700000000",
    }
    resp.text = '{"message": "API rate limit exceeded"}'
    return resp


def test_rate_limit_raises_rate_limit_error(monkeypatch):
    client = make_client()
    monkeypatch.setattr(client.session, "request", Mock(return_value=_rate_limited_response()))

    with pytest.raises(RateLimitError) as exc:
        client.request("GET", "/api/v5/user")

    assert exc.value.status_code == 403
    assert exc.value.remaining == 0
    assert exc.value.limit == 5000
    assert exc.value.reset == 1700000000
    assert "remaining=0" in str(exc.value)


def test_403_without_rate_limit_header_raises_plain_api_error(monkeypatch):
    client = make_client()
    resp = Mock(status_code=403)
    resp.headers = {}
    resp.text = "forbidden"
    monkeypatch.setattr(client.session, "request", Mock(return_value=resp))

    with pytest.raises(AtomGitAPIError) as exc:
        client.request("GET", "/api/v5/user")
    assert not isinstance(exc.value, RateLimitError)


def test_429_with_remaining_zero_also_rate_limit(monkeypatch):
    client = make_client()
    monkeypatch.setattr(client.session, "request", Mock(return_value=_rate_limited_response(status=429)))
    with pytest.raises(RateLimitError):
        client.request("GET", "/api/v5/user")


# --------------------------------------------------------------------------
# Catalog coverage – aligned with the official AtomGit docs sitemap (96 endpoints)
# --------------------------------------------------------------------------
def test_catalog_covers_all_official_endpoint_slugs():
    catalog_slugs = {ep.slug for ep in DEFAULT_API_CATALOG.all()}
    missing = [slug for slug, _, _, _ in _OFFICIAL_ENTRIES if slug not in catalog_slugs]
    assert not missing, f"official slugs missing from catalog: {missing}"


@pytest.mark.parametrize(
    "slug,method,path",
    [
        ("create-org", "POST", "/api/v5/orgs"),
        ("get-branch-list", "GET", "/api/v5/repos/:owner/:repo/branches"),
        ("get-tag-list", "GET", "/api/v5/repos/:owner/:repo/tags"),
        ("get-repo-milestones", "GET", "/api/v5/repos/:owner/:repo/milestones"),
        ("create-check-run", "POST", "/api/v5/repos/:owner/:repo/check-runs"),
        ("create-commit-statuses", "POST", "/api/v5/repos/:owner/:repo/statuses/:sha"),
        ("get-repository", "GET", "/api/v5/repos/:owner/:repo"),
        ("get-the-authenticated-user", "GET", "/api/v5/user"),
        ("create-repo-discuss", "POST", "/api/v5/repos/:owner/:repo/discuss"),
    ],
)
def test_official_endpoint_path(slug, method, path):
    ep = DEFAULT_API_CATALOG.get(slug)
    assert ep.method == method
    assert ep.path == path
    assert ep.doc_url.startswith("https://docs.atomgit.com/openAPI/api_versioned/")


def test_official_and_legacy_alias_resolve_same_path():
    official = DEFAULT_API_CATALOG.get("get-the-authenticated-user")
    legacy = DEFAULT_API_CATALOG.get("get-api-v-5-user")
    assert official.path == legacy.path == "/api/v5/user"


def test_catalog_find_by_method_returns_expected_counts():
    posts = DEFAULT_API_CATALOG.find(method="POST")
    assert len(posts) >= 20
    deletes = DEFAULT_API_CATALOG.find(method="DELETE")
    assert len(deletes) >= 10


# --------------------------------------------------------------------------
# New typed wrappers render the expected paths
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "call,expected_url_suffix",
    [
        (lambda c: c.get_user("octocat"), "/api/v5/users/octocat"),
        (lambda c: c.get_repository(), "/api/v5/repos/example-org/example-repo"),
        (lambda c: c.get_repository("o", "r"), "/api/v5/repos/o/r"),
        (lambda c: c.list_branches(), "/api/v5/repos/example-org/example-repo/branches"),
        (lambda c: c.get_branch("dev"), "/api/v5/repos/example-org/example-repo/branches/dev"),
        (lambda c: c.list_tags(), "/api/v5/repos/example-org/example-repo/tags"),
        (lambda c: c.get_commit("abc123"), "/api/v5/repos/example-org/example-repo/commits/abc123"),
        (lambda c: c.list_milestones(), "/api/v5/repos/example-org/example-repo/milestones"),
        (lambda c: c.get_org("csdn"), "/api/v5/orgs/csdn"),
        (lambda c: c.list_org_repos("csdn"), "/api/v5/orgs/csdn/repos"),
        (lambda c: c.search_repositories("robot"), "/api/v5/search/repositories"),
        (lambda c: c.create_check_run({}), "/api/v5/repos/example-org/example-repo/check-runs"),
        (lambda c: c.create_commit_status("sha1", "success"), "/api/v5/repos/example-org/example-repo/statuses/sha1"),
        (lambda c: c.get_combined_status("main"), "/api/v5/repos/example-org/example-repo/commits/main/status"),
    ],
)
def test_new_wrappers_render_paths(monkeypatch, call, expected_url_suffix):
    client = make_client()
    response = Mock(status_code=200)
    response.json.return_value = {}
    request_mock = Mock(return_value=response)
    monkeypatch.setattr(client.session, "request", request_mock)

    call(client)

    assert request_mock.call_args.kwargs["url"].endswith(expected_url_suffix)


def test_create_branch_payload(monkeypatch):
    client = make_client()
    response = Mock(status_code=200)
    response.json.return_value = {}
    request_mock = Mock(return_value=response)
    monkeypatch.setattr(client.session, "request", request_mock)

    client.create_branch("feature", "main")

    assert request_mock.call_args.kwargs["json"] == {"branch": "feature", "ref": "main"}


# --------------------------------------------------------------------------
# from_docs page parser (sidebar method + best-effort path)
# --------------------------------------------------------------------------
def test_parse_endpoint_page_extracts_method_from_sidebar():
    slug = "create-org"
    html = (
        f'<li class="menu__list-item api-method post">'
        f'<a href="/openAPI/api_versioned/{slug}">create-org</a></li>'
        f'<p>example: https://api.atomgit.com/orgs/csdn</p>'
        f'<h1 class="theme-doc-markdown-header-title">创建组织</h1>'
    )
    ep = _parse_endpoint_page(slug, html, f"https://docs.atomgit.com/openAPI/api_versioned/{slug}")
    assert ep.method == "POST"
    assert ep.path == "/orgs/csdn"
    assert ep.title == "创建组织"


def test_parse_endpoint_page_infers_method_from_slug_when_sidebar_missing():
    slug = "delete-repo-discuss"
    html = '<html><body><h1>delete discuss</h1></body></html>'
    ep = _parse_endpoint_page(slug, html, "https://docs.atomgit.com/x")
    assert ep.method == "DELETE"
