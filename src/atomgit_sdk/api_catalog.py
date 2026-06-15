"""AtomGit API endpoint catalog.

The official AtomGit OpenAPI documentation (https://docs.atomgit.com/openAPI/api_versioned)
covers 96 endpoints across 17 modules.  This module makes them discoverable and
callable from the SDK.

Confidence tiers for the built-in paths:

* **verified** – taken from the previously shipped catalog that has been
  exercising the live AtomGit API inside the IB_Robot project.
* **standard** – Gitea/GitHub-compatible REST paths for core resources
  (user/org/repo/branch/tag/commit/issue/label/milestone/pull) which AtomGit
  follows; corroborated by the example URLs shown in the docs.
* **inferred** – paths for AtomGit-specific surfaces derived from documented
  slug semantics.  These were smoke-tested against the live API on
  2026-06-15; see SMOKE_RESULTS below for the verified/unverified split.
"""

# Smoke-test results (2026-06-15, openEuler/IB_Robot, ATOMGIT_TOKEN):
#   ✓ verified   — discuss GET surface (list / categories / get-by-id) → 200/400,
#                  so those entries are treated as verified despite the tier name.
#   ~ partial    — discuss write (create/update/delete) → HTTP 405: the
#                  ``/discuss`` route exists but rejects POST/PATCH/DELETE; the
#                  real write path is a sub-route that is not yet pinned down.
#   ✗ unverified — check-runs / security / enterprise / remind / private / apps
#                  returned 404 on every probed path variant. The doc pages do
#                  not expose path templates, so these entries keep a best-guess
#                  path only for discoverability — always consult the endpoint's
#                  ``doc_url`` before calling ``call_api``.

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from html import unescape
from urllib.request import urlopen

from atomgit_sdk.exceptions import ConfigurationError

API_DOCS_BASE_URL = "https://docs.atomgit.com/openAPI/api_versioned"
API_DOCS_SITEMAP_URL = "https://docs.atomgit.com/sitemap.xml"
API_HOST = "api.atomgit.com"
SMOKE_TESTED_AT = "2026-06-15"
_PATH_PARAM_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")

# Module index pages on the docs site – excluded when harvesting endpoint slugs.
_MODULE_PAGES = frozenset(
    {
        "atomgit-openapi",
        "user",
        "activity",
        "org",
        "apps",
        "branches",
        "tags",
        "commits",
        "commit-statuses",
        "repositories",
        "repository-contents",
        "change-requests",
        "check-runs",
        "issues",
        "issues-comment",
        "milestones",
        "labels",
        "security",
        "discuss",
    }
)


@dataclass(frozen=True)
class APIEndpoint:
    """One documented AtomGit API endpoint."""

    slug: str
    method: str
    path: str
    title: str = ""
    doc_url: str = ""

    @property
    def path_params(self) -> list[str]:
        """Return path parameter names required by this endpoint."""
        return _PATH_PARAM_RE.findall(self.path)

    def render(self, path_params: Mapping[str, object] | None = None) -> str:
        """Render this endpoint path by replacing ``:name`` placeholders."""
        values = dict(path_params or {})
        missing = [name for name in self.path_params if name not in values]
        if missing:
            raise ConfigurationError(f"Missing path parameters for {self.slug}: {', '.join(missing)}")

        rendered = self.path
        for name, value in values.items():
            rendered = rendered.replace(f":{name}", str(value))
        return rendered


class APICatalog:
    """Searchable collection of documented AtomGit API endpoints."""

    def __init__(self, endpoints: Iterable[APIEndpoint]):
        self._endpoints = tuple(endpoints)
        self._by_slug: dict[str, APIEndpoint] = {endpoint.slug: endpoint for endpoint in self._endpoints}

    def __len__(self) -> int:
        return len(self._endpoints)

    def all(self) -> Sequence[APIEndpoint]:
        """Return all endpoints in this catalog."""
        return self._endpoints

    def get(self, slug: str) -> APIEndpoint:
        """Get an endpoint by documentation slug."""
        try:
            return self._by_slug[slug]
        except KeyError as exc:
            raise ConfigurationError(f"Unknown AtomGit API endpoint: {slug}") from exc

    def find(
        self,
        *,
        method: str | None = None,
        path_contains: str | None = None,
        title_contains: str | None = None,
    ) -> list[APIEndpoint]:
        """Find endpoints by method, path substring, or title substring."""
        method = method.upper() if method else None
        results = list(self._endpoints)
        if method:
            results = [endpoint for endpoint in results if endpoint.method == method]
        if path_contains:
            results = [endpoint for endpoint in results if path_contains in endpoint.path]
        if title_contains:
            results = [endpoint for endpoint in results if title_contains in endpoint.title]
        return results

    @classmethod
    def from_entries(cls, entries: Iterable[tuple[str, str, str, str]]) -> APICatalog:
        """Build a catalog from ``(slug, method, path, title)`` entries."""
        return cls(
            APIEndpoint(
                slug=slug,
                method=method.upper(),
                path=path,
                title=title,
                doc_url=f"{API_DOCS_BASE_URL}/{slug}",
            )
            for slug, method, path, title in entries
        )

    @classmethod
    def from_docs(
        cls,
        sitemap_url: str = API_DOCS_SITEMAP_URL,
        *,
        timeout: int = 20,
    ) -> APICatalog:
        """Load the full endpoint catalog from the official AtomGit docs.

        Harvests every endpoint page linked from the docs sitemap and extracts
        the HTTP ``method`` (reliable – taken from the sidebar ``api-method``
        marker) and ``path`` (best-effort – recovered from example URLs since
        the doc pages do not render a path template).  Use this when you need
        the live, complete official endpoint list; for everyday use prefer the
        curated :data:`DEFAULT_API_CATALOG`.
        """
        sitemap = urlopen(sitemap_url, timeout=timeout).read().decode("utf-8")
        slugs = re.findall(r"https://docs\.atomgit\.com/openAPI/api_versioned/([^<\s\"']+)", sitemap)
        endpoint_slugs = [slug for slug in dict.fromkeys(slugs) if slug not in _MODULE_PAGES]

        endpoints: list[APIEndpoint] = []
        for slug in endpoint_slugs:
            page_url = f"{API_DOCS_BASE_URL}/{slug}"
            try:
                page = urlopen(page_url, timeout=timeout).read().decode("utf-8", "replace")
            except Exception:
                continue
            endpoints.append(_parse_endpoint_page(slug, page, page_url))
        return cls(endpoints)


def _infer_method_from_slug(slug: str) -> str:
    """Best-effort HTTP method from a documented slug's verb prefix."""
    for prefix, method in (
        ("get-", "GET"),
        ("list-", "GET"),
        ("has-", "GET"),
        ("check-", "GET"),
        ("create-", "POST"),
        ("add-", "POST"),
        ("save-", "POST"),
        ("set-", "POST"),
        ("lock-", "PUT"),
        ("delete-", "DELETE"),
        ("del-", "DELETE"),
        ("remove-", "DELETE"),
        ("un-lock-", "DELETE"),
        ("update-", "PATCH"),
        ("patch-", "PATCH"),
        ("clear-", "DELETE"),
    ):
        if slug.startswith(prefix):
            return method
    return "GET"


def _parse_endpoint_page(slug: str, html: str, page_url: str) -> APIEndpoint:
    """Extract one endpoint from its documentation page."""
    method = ""
    for chunk in re.split(r"<li", html):
        if f'href="/openAPI/api_versioned/{slug}"' in chunk:
            match = re.search(r"api-method\s+(get|post|put|patch|delete)\b", chunk)
            if match:
                method = match.group(1).upper()
                break
    if not method:
        method = _infer_method_from_slug(slug)

    paths = re.findall(r"/api/v5/[A-Za-z0-9_:/{}.\-]+", html)
    if not paths:
        paths = re.findall(r"api\.atomgit\.com(/[A-Za-z0-9_:/{}.\-]+)", html)
    path = min(set(paths), key=len) if paths else ""

    title = ""
    match = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', html)
    if match:
        title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
    if not title:
        match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
        if match:
            title = unescape(match.group(1).split("|")[0].strip())

    if not method:
        raise ConfigurationError(f"Could not parse AtomGit API doc page: {page_url}")

    return APIEndpoint(slug=slug, method=method, path=path, title=title, doc_url=page_url)


# ---------------------------------------------------------------------------
# Built-in catalog – aligned with the official AtomGit OpenAPI docs.
# ---------------------------------------------------------------------------
# 96 documented endpoint slugs grouped by module.  Paths are filled per the
# confidence tiers documented at the top of this file.

_USER_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-the-authenticated-user", "GET", "/api/v5/user", "获取授权用户的资料"),
    ("get-user-by-username", "GET", "/api/v5/users/:username", "获取一个用户"),
    ("get-user-space-repo-list", "GET", "/api/v5/user/repos", "获取个人空间下代码库列表"),
    ("get-user-issues-list", "GET", "/api/v5/issues", "获取授权用户的Issue列表"),
    ("get-user-followers", "GET", "/api/v5/user/followers", "获取授权用户的粉丝"),
    ("get-user-followers-by-username", "GET", "/api/v5/users/:username/followers", "获取指定用户的粉丝"),
    ("get-user-following", "GET", "/api/v5/user/following", "获取授权用户关注的人"),
    ("get-the-following", "GET", "/api/v5/users/:username/following", "获取指定用户关注的人"),
    ("has-the-fans", "GET", "/api/v5/user/following/:username", "检查授权用户是否关注某用户"),
    ("has-this-fans", "GET", "/api/v5/users/:username/following/:target", "检查某用户是否关注目标用户"),
    ("add-fans", "PUT", "/api/v5/user/following/:username", "关注用户"),
    ("del-fans", "DELETE", "/api/v5/user/following/:username", "取消关注用户"),
    ("list-email", "GET", "/api/v5/user/emails", "获取授权用户邮箱列表"),
    ("list-key", "GET", "/api/v5/user/keys", "获取授权用户公钥列表"),
    ("add-key", "POST", "/api/v5/user/keys", "添加公钥"),
    ("del-key", "DELETE", "/api/v5/user/keys/:id", "删除公钥"),
    ("user-event", "GET", "/api/v5/users/:username/events", "获取用户动态"),
    ("user-receive-event", "GET", "/api/v5/users/:username/received_events", "获取用户接收的动态"),
    ("user-org-page-list", "GET", "/api/v5/user/orgs", "获取授权用户的组织列表"),
)

_ORG_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("create-org", "POST", "/api/v5/orgs", "创建组织"),
    ("org-detail", "GET", "/api/v5/orgs/:org", "获取组织详情"),
    ("update-org", "PATCH", "/api/v5/orgs/:org", "更新组织"),
    ("get-org-repo-list", "GET", "/api/v5/orgs/:org/repos", "获取组织下代码库列表"),
    ("org-page-list", "GET", "/api/v5/orgs", "获取组织列表"),
    ("org-followers", "GET", "/api/v5/orgs/:org/followers", "获取组织粉丝"),
    ("org-members", "GET", "/api/v5/orgs/:org/members", "获取组织成员"),
    ("org-member-check", "GET", "/api/v5/orgs/:org/members/:username", "检查用户是否为组织成员"),
    ("org-member-delete", "DELETE", "/api/v5/orgs/:org/members/:username", "移除组织成员"),
    ("org-member-role", "GET", "/api/v5/orgs/:org/memberships/:username", "获取组织成员角色"),
    ("set-org-member-role", "PUT", "/api/v5/orgs/:org/memberships/:username", "设置组织成员角色"),
    ("user-org-invitation", "POST", "/api/v5/orgs/:org/invitations", "邀请用户加入组织"),
    ("create-org-discuss", "POST", "/api/v5/orgs/:org/discuss", "创建组织讨论"),
    ("get-org-discuss", "GET", "/api/v5/orgs/:org/discuss/:id", "获取组织讨论"),
    ("get-org-discuss-list", "GET", "/api/v5/orgs/:org/discuss", "获取组织讨论列表"),
    ("get-org-discuss-category-list", "GET", "/api/v5/orgs/:org/discuss/categories", "获取组织讨论分类"),
    ("update-org-discuss", "PATCH", "/api/v5/orgs/:org/discuss/:id", "更新组织讨论"),
    ("delete-org-discuss", "DELETE", "/api/v5/orgs/:org/discuss/:id", "删除组织讨论"),
)

_REPO_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-repository", "GET", "/api/v5/repos/:owner/:repo", "获取代码库信息"),
    ("get-repo-assignees", "GET", "/api/v5/repos/:owner/:repo/assignees", "获取仓库可指派人列表"),
    ("check-repo-assignee", "GET", "/api/v5/repos/:owner/:repo/assignees/:username", "检查用户是否可指派"),
)

_REPO_CONTENT_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-repo-conent", "GET", "/api/v5/repos/:owner/:repo/contents/:path", "获取仓库具体路径下的内容"),
    ("save-repo-conent", "PUT", "/api/v5/repos/:owner/:repo/contents/:path", "新建/更新文件"),
    ("delete-repo-conent", "DELETE", "/api/v5/repos/:owner/:repo/contents/:path", "删除文件"),
    ("get-repo-trees", "GET", "/api/v5/repos/:owner/:repo/git/trees/:sha", "获取仓库目录树"),
    ("get-repo-file-blame", "GET", "/api/v5/repos/:owner/:repo/blame/:path", "获取文件blame信息"),
)

_BRANCH_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-branch-list", "GET", "/api/v5/repos/:owner/:repo/branches", "获取仓库分支列表"),
    ("get-branch", "GET", "/api/v5/repos/:owner/:repo/branches/:branch", "获取单个分支"),
)

_TAG_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-tag-list", "GET", "/api/v5/repos/:owner/:repo/tags", "获取仓库标签列表"),
)

_COMMIT_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-ref-commit", "GET", "/api/v5/repos/:owner/:repo/commits/:ref", "获取ref对应的提交"),
)

_COMMIT_STATUS_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("create-commit-statuses", "POST", "/api/v5/repos/:owner/:repo/statuses/:sha", "创建提交状态"),
    ("get-combined-commit-statuses", "GET", "/api/v5/repos/:owner/:repo/commits/:ref/status", "获取聚合提交状态"),
)

_PR_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("create-change-request", "POST", "/api/v5/repos/:owner/:repo/pulls", "创建Pull Request"),
    ("get-change-request", "GET", "/api/v5/repos/:owner/:repo/pulls/:number", "获取某个Pull Request"),
    ("create-change-request-comment", "POST", "/api/v5/repos/:owner/:repo/pulls/:number/comments", "提交Pull Request评论"),
    ("create-change-request-reply", "POST", "/api/v5/repos/:owner/:repo/pulls/:number/discussions/:discussion_id/comments", "回复Pull Request评论"),
    ("get-change-reques-comment-list", "GET", "/api/v5/repos/:owner/:repo/pulls/:number/comments", "获取Pull Request评论列表"),
    ("get-change-request-comment", "GET", "/api/v5/repos/:owner/:repo/pulls/comments/:id", "获取Pull Request某条评论"),
)

_CHECK_RUN_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("create-check-run", "POST", "/api/v5/repos/:owner/:repo/check-runs", "创建检查"),
    ("get-check-run", "GET", "/api/v5/repos/:owner/:repo/check-runs/:id", "获取检查"),
    ("update-check-run", "PATCH", "/api/v5/repos/:owner/:repo/check-runs/:id", "更新检查"),
)

_ISSUE_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("create-repo-issue", "POST", "/api/v5/repos/:owner/:repo/issues", "创建Issue"),
    ("get-repo-issues-list", "GET", "/api/v5/repos/:owner/:repo/issues", "仓库Issue列表"),
    ("get-repo-issue-info", "GET", "/api/v5/repos/:owner/:repo/issues/:number", "获取仓库某个Issue"),
    ("patch-repo-issue-info", "PATCH", "/api/v5/repos/:owner/:repo/issues/:number", "更新Issue"),
    ("lock-repo-issue", "PUT", "/api/v5/repos/:owner/:repo/issues/:number/lock", "锁定Issue"),
    ("un-lock-repo-issue", "DELETE", "/api/v5/repos/:owner/:repo/issues/:number/lock", "解锁Issue"),
    ("set-issue-assignee", "POST", "/api/v5/repos/:owner/:repo/issues/:number/assignees", "设置Issue指派人"),
    ("clear-issue-assignee", "DELETE", "/api/v5/repos/:owner/:repo/issues/:number/assignees", "清除Issue指派人"),
    ("get-all-tag-of-issue", "GET", "/api/v5/repos/:owner/:repo/issues/:number/labels", "获取Issue的所有标签"),
)

_ISSUE_COMMENT_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("create-issue-comment", "POST", "/api/v5/repos/:owner/:repo/issues/:number/comments", "创建Issue评论"),
    ("get-issue-comments-list", "GET", "/api/v5/repos/:owner/:repo/issues/:number/comments", "获取Issue评论列表"),
    ("get-issue-comment-info", "GET", "/api/v5/repos/:owner/:repo/issues/comments/:id", "获取Issue某条评论"),
    ("update-issue-comment", "PATCH", "/api/v5/repos/:owner/:repo/issues/comments/:id", "编辑Issue评论"),
    ("delete-issue-comment", "DELETE", "/api/v5/repos/:owner/:repo/issues/comments/:id", "删除Issue评论"),
)

_MILESTONE_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-repo-milestones", "GET", "/api/v5/repos/:owner/:repo/milestones", "获取仓库里程碑列表"),
    ("get-repo-milestones-by-number", "GET", "/api/v5/repos/:owner/:repo/milestones/:number", "获取仓库某个里程碑"),
)

_LABEL_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("create-repo-labels", "POST", "/api/v5/repos/:owner/:repo/labels", "创建标签"),
    ("get-repo-labels", "GET", "/api/v5/repos/:owner/:repo/labels", "获取仓库标签"),
    ("get-label-by-name", "GET", "/api/v5/repos/:owner/:repo/labels/:name", "根据名称获取标签"),
    ("create-issue-labels", "POST", "/api/v5/repos/:owner/:repo/issues/:number/labels", "添加Issue标签"),
    ("delete-issue-labels", "DELETE", "/api/v5/repos/:owner/:repo/issues/:number/labels", "删除Issue标签"),
)

# discuss: GET surface (list/categories/get) verified by smoke test → 200/400.
# Write ops (create/update/delete) returned 405 on /discuss — the real write
# path is a sub-route that is not yet pinned down; keep these for discoverability.
_DISCUSS_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("create-repo-discuss", "POST", "/api/v5/repos/:owner/:repo/discuss", "创建仓库讨论"),
    ("get-repo-discuss", "GET", "/api/v5/repos/:owner/:repo/discuss/:id", "获取仓库讨论"),
    ("get-repo-discuss-list", "GET", "/api/v5/repos/:owner/:repo/discuss", "获取仓库讨论列表"),
    ("get-repo-discuss-category-list", "GET", "/api/v5/repos/:owner/:repo/discuss/categories", "获取仓库讨论分类"),
    ("update-repo-discuss", "PATCH", "/api/v5/repos/:owner/:repo/discuss/:id", "更新仓库讨论"),
    ("delete-repo-discuss", "DELETE", "/api/v5/repos/:owner/:repo/discuss/:id", "删除仓库讨论"),
)

# AtomGit-specific surfaces – paths inferred from slug semantics (tier 3).
_APPS_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-o-auth-atu-token", "POST", "/api/v5/applications/:client_id/tokens", "获取OAuth应用Token"),
)

_SECURITY_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("save-scan-status", "POST", "/api/v5/repos/:owner/:repo/scan-status", "保存扫描状态"),
    ("save-security-results", "POST", "/api/v5/repos/:owner/:repo/security-results", "保存安全结果"),
)

_ENTERPRISE_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("enterprise-info-by-credit-code", "GET", "/api/v5/enterprises/credit-code/:code", "按信用代码获取企业信息"),
    ("enterprise-info-by-org-code", "GET", "/api/v5/enterprises/org-code/:code", "按组织代码获取企业信息"),
)

_SOCIAL_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("remind-page-list", "GET", "/api/v5/reminds", "获取提醒列表"),
    ("remind-by-id", "GET", "/api/v5/reminds/:id", "获取提醒详情"),
    ("private-page-list", "GET", "/api/v5/privates", "获取私信列表"),
    ("private-by-id", "GET", "/api/v5/privates/:id", "获取私信详情"),
)

_SEARCH_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("search-repositories", "GET", "/api/v5/search/repositories", "搜索仓库"),
    ("search-issues", "GET", "/api/v5/search/issues", "搜索Issue"),
    ("search-users", "GET", "/api/v5/search/users", "搜索用户"),
)

_OFFICIAL_ENTRIES = (
    _USER_ENTRIES
    + _ORG_ENTRIES
    + _REPO_ENTRIES
    + _REPO_CONTENT_ENTRIES
    + _BRANCH_ENTRIES
    + _TAG_ENTRIES
    + _COMMIT_ENTRIES
    + _COMMIT_STATUS_ENTRIES
    + _PR_ENTRIES
    + _CHECK_RUN_ENTRIES
    + _ISSUE_ENTRIES
    + _ISSUE_COMMENT_ENTRIES
    + _MILESTONE_ENTRIES
    + _LABEL_ENTRIES
    + _DISCUSS_ENTRIES
    + _APPS_ENTRIES
    + _SECURITY_ENTRIES
    + _ENTERPRISE_ENTRIES
    + _SOCIAL_ENTRIES
)

# Gitea-standard search endpoints supported by AtomGit but not enumerated as
# standalone pages in the official docs sitemap; kept for completeness.
_STANDARD_EXTRA_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("search-repositories", "GET", "/api/v5/search/repositories", "搜索仓库"),
    ("search-issues", "GET", "/api/v5/search/issues", "搜索Issue"),
    ("search-users", "GET", "/api/v5/search/users", "搜索用户"),
)

# Legacy path-transcription slugs kept as aliases so existing call_api()
# callers keep working.  These point at the same paths as their official
# counterparts but use the old ``<method>-api-v-5-...`` naming.
_LEGACY_ENTRIES: tuple[tuple[str, str, str, str], ...] = (
    ("get-api-v-5-user", "GET", "/api/v5/user", "获取授权用户的资料"),
    ("get-api-v-5-users-username", "GET", "/api/v5/users/:username", "获取一个用户"),
    ("get-api-v-5-repos-owner-repo", "GET", "/api/v5/repos/:owner/:repo", "获取一个仓库"),
    ("patch-api-v-5-repos-owner-repo", "PATCH", "/api/v5/repos/:owner/:repo", "更新仓库设置"),
    ("delete-api-v-5-repos-owner-repo", "DELETE", "/api/v5/repos/:owner/:repo", "删除一个仓库"),
    ("get-api-v-5-repos-owner-repo-contents-path", "GET", "/api/v5/repos/:owner/:repo/contents/:path", "获取仓库具体路径下的内容"),
    ("post-api-v-5-repos-owner-repo-contents-path", "POST", "/api/v5/repos/:owner/:repo/contents/:path", "新建文件"),
    ("put-api-v-5-repos-owner-repo-contents-path", "PUT", "/api/v5/repos/:owner/:repo/contents/:path", "更新文件"),
    ("delete-api-v-5-repos-owner-repo-contents-path", "DELETE", "/api/v5/repos/:owner/:repo/contents/:path", "删除文件"),
    ("get-api-v-5-repos-owner-repo-branches", "GET", "/api/v5/repos/:owner/:repo/branches", "获取仓库分支列表"),
    ("get-api-v-5-repos-owner-repo-branches-branch", "GET", "/api/v5/repos/:owner/:repo/branches/:branch", "获取单个分支"),
    ("post-api-v-5-repos-owner-repo-branches", "POST", "/api/v5/repos/:owner/:repo/branches", "创建分支"),
    ("delete-api-v-5-repos-owner-repo-branches-name", "DELETE", "/api/v5/repos/:owner/:repo/branches/:name", "删除分支"),
    ("get-api-v-5-repos-owner-repo-commits", "GET", "/api/v5/repos/:owner/:repo/commits", "获取仓库所有提交"),
    ("get-api-v-5-repos-owner-repo-commits-sha", "GET", "/api/v5/repos/:owner/:repo/commits/:sha", "获取仓库某个提交"),
    ("get-api-v-5-repos-owner-repo-commits-sha-diff", "GET", "/api/v5/repos/:owner/:repo/commits/:sha/diff", "获取提交差异"),
    ("get-api-v-5-repos-owner-repo-compare-base-head", "GET", "/api/v5/repos/:owner/:repo/compare/:base...:head", "比较两个提交"),
    ("get-api-v-5-repos-owner-repo-labels", "GET", "/api/v5/repos/:owner/:repo/labels", "获取仓库标签"),
    ("post-api-v-5-repos-owner-repo-labels", "POST", "/api/v5/repos/:owner/:repo/labels", "创建标签"),
    ("patch-api-v-5-repos-owner-repo-labels-original-name", "PATCH", "/api/v5/repos/:owner/:repo/labels/:original_name", "更新标签"),
    ("delete-api-v-5-repos-owner-repo-labels-name", "DELETE", "/api/v5/repos/:owner/:repo/labels/:name", "删除标签"),
    ("get-api-v-5-repos-owner-repo-issues", "GET", "/api/v5/repos/:owner/:repo/issues", "仓库Issue列表"),
    ("get-api-v-5-repos-owner-repo-issues-number", "GET", "/api/v5/repos/:owner/:repo/issues/:number", "获取仓库某个Issue"),
    ("post-api-v-5-repos-owner-issues", "POST", "/api/v5/repos/:owner/issues", "创建Issue"),
    ("patch-api-v-5-repos-owner-issues-number", "PATCH", "/api/v5/repos/:owner/issues/:number", "更新Issue"),
    ("get-api-v-5-repos-owner-repo-issues-number-comments", "GET", "/api/v5/repos/:owner/:repo/issues/:number/comments", "获取Issue评论"),
    ("post-api-v-5-repos-owner-repo-issues-number-comments", "POST", "/api/v5/repos/:owner/:repo/issues/:number/comments", "创建Issue评论"),
    ("get-api-v-5-repos-owner-repo-issues-comments-id", "GET", "/api/v5/repos/:owner/:repo/issues/comments/:id", "获取Issue某条评论"),
    ("patch-api-v-5-repos-owner-repo-issues-comments-id", "PATCH", "/api/v5/repos/:owner/:repo/issues/comments/:id", "编辑Issue评论"),
    ("delete-api-v-5-repos-owner-repo-issues-comments-id", "DELETE", "/api/v5/repos/:owner/:repo/issues/comments/:id", "删除Issue评论"),
    ("get-api-v-5-repos-owner-repo-pulls", "GET", "/api/v5/repos/:owner/:repo/pulls", "Pull Request列表"),
    ("post-api-v-5-repos-owner-repo-pulls", "POST", "/api/v5/repos/:owner/:repo/pulls", "创建Pull Request"),
    ("get-api-v-5-repos-owner-repo-pulls-number", "GET", "/api/v5/repos/:owner/:repo/pulls/:number", "获取某个Pull Request"),
    ("patch-api-v-5-repos-owner-repo-pulls-number", "PATCH", "/api/v5/repos/:owner/:repo/pulls/:number", "更新Pull Request"),
    ("get-api-v-5-repos-owner-repo-pulls-number-files", "GET", "/api/v5/repos/:owner/:repo/pulls/:number/files", "Pull Request文件列表"),
    ("get-api-v-5-repos-owner-repo-pulls-number-files-json", "GET", "/api/v5/repos/:owner/:repo/pulls/:number/files.json", "Pull Request Commit文件列表"),
    ("get-api-v-5-repos-owner-repo-pulls-number-commits", "GET", "/api/v5/repos/:owner/:repo/pulls/:number/commits", "Pull Request提交列表"),
    ("get-api-v-5-repos-owner-repo-pulls-number-comments", "GET", "/api/v5/repos/:owner/:repo/pulls/:number/comments", "获取某个Pull Request的所有评论"),
    ("post-api-v-5-repos-owner-repo-pulls-number-comments", "POST", "/api/v5/repos/:owner/:repo/pulls/:number/comments", "提交pull request 评论"),
    ("get-api-v-5-repos-owner-repo-pulls-comments-id", "GET", "/api/v5/repos/:owner/:repo/pulls/comments/:id", "获取Pull Request某条评论"),
    ("patch-api-v-5-repos-owner-repo-pulls-comments-id", "PATCH", "/api/v5/repos/:owner/:repo/pulls/comments/:id", "编辑评论"),
    ("delete-api-v-5-repos-owner-repo-pulls-comments-id", "DELETE", "/api/v5/repos/:owner/:repo/pulls/comments/:id", "删除评论"),
    ("post-api-v-5-repos-owner-repo-pulls-number-discussions-discussions-id-comments", "POST", "/api/v5/repos/:owner/:repo/pulls/:number/discussions/:discussion_id/comments", "回复Pull Request评论"),
    ("put-api-v-5-repos-owner-repo-pulls-number-comments-discussions-id", "PUT", "/api/v5/repos/:owner/:repo/pulls/:number/comments/:discussion_id", "修改检视意见解决状态"),
    ("post-api-v-5-repos-owner-repo-pulls-number-review", "POST", "/api/v5/repos/:owner/:repo/pulls/:number/review", "提交Pull Request Review"),
    ("get-api-v-5-repos-owner-repo-pulls-comment-comment-id-modify-history", "GET", "/api/v5/repos/:owner/:repo/pulls/comment/:comment_id/modify_history", "获取Pull Request评论的修改历史"),
    ("get-api-v-5-repos-owner-repo-pulls-comment-comment-id-user-reactions", "GET", "/api/v5/repos/:owner/:repo/pulls/comment/:comment_id/user_reactions", "获取Pull Request评论的表态列表"),
    ("get-api-v-5-repos-owner-repo-pulls-number-user-reactions", "GET", "/api/v5/repos/:owner/:repo/pulls/:number/user_reactions", "获取Pull Request的表态列表"),
)

DEFAULT_API_CATALOG = APICatalog.from_entries(
    _OFFICIAL_ENTRIES + _STANDARD_EXTRA_ENTRIES + _LEGACY_ENTRIES
)
