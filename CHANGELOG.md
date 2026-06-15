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
- API endpoint catalog (`APICatalog`) with built-in collaboration endpoints and
  `from_docs()` sync (247 official endpoints sampled as of 2026-04).
- High-level services: `PRService`, `IssueService`, `RepairService`.
- Cross-repo context resolution (`resolve_atomgit_context`) and
  `parse_atomgit_url` URL parser.
- Accurate diff line-number mapping (`calculate_diff_position`).
- Pydantic-based data models (`BaseIssue`, `CodeIssue`, `ArchitectureIssue`,
  `FixResult`).
- Typed exceptions (`AtomGitSDKError`, `AtomGitAPIError`, `ConfigurationError`,
  `DiffParseError`, `URLError`).
- Unit-test suite covering api catalog, client retry, comment services,
  cross-repo context, diff position, issue label validation, repair service.

[Unreleased]: https://github.com/wuxiaoqiang12/AtomGit_SDK/compare/v0.1.0...master
[0.1.0]: https://github.com/wuxiaoqiang12/AtomGit_SDK/releases/tag/v0.1.0
