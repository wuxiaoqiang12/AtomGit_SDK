# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-15

First public release of `atomgit-sdk`, extracted and open-sourced from the
IB_Robot project.

### Added

- Unified `AtomGitClient` with Bearer-token auth and retry on safe HTTP methods.
- `X-Api-Version: 2023-02-21` header sent on every request, as mandated by the
  official API docs.
- Rate-limit awareness: a 403/429 response with `x-ratelimit-remaining == 0`
  raises a dedicated `RateLimitError` carrying `limit`/`remaining`/`used`/`reset`.
- API endpoint catalog (`APICatalog`) expanded to cover **all 96 official
  endpoints** across the 17 documented modules, plus legacy path-transcription
  slug aliases for backward compatibility. `from_docs()` now harvests the live
  docs sitemap (docs.atomgit.com).
- 20+ typed wrappers for previously uncovered surfaces: user account, repository,
  branch, tag, commit, milestone, organization, search, check runs and commit
  statuses.
- High-level services: `PRService`, `IssueService`, `RepairService`.
- Cross-repo context resolution (`resolve_atomgit_context`) and
  `parse_atomgit_url` URL parser.
- Accurate diff line-number mapping (`calculate_diff_position`).
- Pydantic-based data models (`BaseIssue`, `CodeIssue`, `ArchitectureIssue`,
  `FixResult`).
- Typed exceptions (`AtomGitSDKError`, `AtomGitAPIError`, `ConfigurationError`,
  `DiffParseError`, `RateLimitError`, `URLError`).
- Unit-test suite covering api catalog, client retry, comment services,
  cross-repo context, diff position, issue label validation, repair service and
  official-docs compliance.

[Unreleased]: https://github.com/wuxiaoqiang12/AtomGit_SDK/compare/v0.1.0...master
[0.1.0]: https://github.com/wuxiaoqiang12/AtomGit_SDK/releases/tag/v0.1.0
