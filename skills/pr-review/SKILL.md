---
name: atomgit-pr-review
description: "AtomGit PR 评审示例。当用户需要\"代码审查\"、\"PR review\"、\"review pull request\"、\"审阅PR\"、\"帮我看看这个PR\"、\"检查这个PR有没有问题\"、\"检查Bug\"、\"logic check\"、\"获取完整review上下文\"、\"提交检视意见\"或分析指定 PR 的改动与已有评论时使用。只要目标是某个 AtomGit 仓库的 PR review，默认优先使用本 skill。"
license: MIT
---

# AtomGit PR Review

提取适合 review 的完整 PR 上下文，并提交代码审查评论到 AtomGit。

只要用户提到 review / 审查 / 审阅 PR，默认视为 AtomGit PR 评审流程并优先使用本 skill。

本 skill 支持对 **任意 AtomGit 仓库的 PR** 做通用代码审查：

- `--owner` / `--repo`: 显式覆盖 `config.json` 中的仓库
- `--url`: 从 AtomGit / GitCode 的 PR 链接自动解析 `owner/repo/pr_number`

当用户的目标是“**review 一个 PR / 帮我看看这个 PR 有没有问题**”时，优先使用本 skill。本 skill 的提取模式默认就会带出 PR 现有评论。

## 通用审查建议

- review 时判断本次提交是否改变了**用户可见**的使用方式（安装、部署、启动、配置、依赖、接口、命令用法等）；若应同步文档但未改，可作为有效 review issue 提出。
- 若变更只涉及内部重构、实现细节，不应强行要求改文档。
- 关注代码质量、潜在 bug、边界条件、安全性、性能与可维护性。

## 环境准备

安装 atomgit-sdk（已发布到 PyPI）：

```bash
pip install atomgit-sdk
```

并配置 `ATOMGIT_TOKEN` 环境变量，以及 `config.json`（参考 [`examples/config.example.json`](../../examples/config.example.json)）。

## 文件读取说明

**输出文件位于 `./tmp` 目录**，AI Agent 应使用 shell 命令读取：

```bash
# 读取 review 上下文
cat ./tmp/{repo}_pr_123_info.json

# 读取审查结果（提交前确认）
cat ./tmp/{repo}_pr_123_issues.json
```

### 大文件处理技巧

当 PR 包含大量文件时，JSON 文件可能很大。使用 `jq` 提取特定文件信息：

```bash
# 列出所有变更文件
jq '.pr.changed_files[].filename' ./tmp/{repo}_pr_123_info.json

# 提取特定文件的内容
jq '.pr.changed_files[] | select(.filename == "src/main.py") | .content' ./tmp/{repo}_pr_123_info.json

# 提取特定文件的 diff
jq '.pr.changed_files[] | select(.filename == "src/main.py") | .patch.diff' ./tmp/{repo}_pr_123_info.json

# 提取多个文件（支持通配符）
jq '.pr.changed_files[] | select(.filename | contains("src/")) | {filename, content}' ./tmp/{repo}_pr_123_info.json
```

## 快速使用

```bash
# 步骤1: 提取 PR 信息
python3 pr_review.py --pr 123

# 直接从链接解析目标 PR
python3 pr_review.py --url https://atomgit.com/some-org/some-repo/pull/123

# 如只关注代码 diff，可显式跳过已有评论
python3 pr_review.py --pr 123 --no-comments

# 步骤2: 你分析代码并生成 issues.json

# 步骤3: 人类确认审查结果

# 步骤4: 提交审查结果（必须指定 --ai-model）
python3 pr_review.py --pr 123 --submit-review ./tmp/{repo}_pr_123_issues.json --ai-model claude-sonnet-4
```

**重要**:
- 在步骤3，你必须将审查结果展示给人类确认后再提交
- **步骤4必须指定 `--ai-model` 参数**，使用你的真实模型名称
- 文件名格式：`./tmp/{repo}_pr_{number}_issues.json`

## API 说明

### 提取 PR 信息

```bash
python3 pr_review.py --pr 123
```

**输出**: `./tmp/{repo}_pr_{number}_info.json`

**注意**:
- 默认输出到 `./tmp` 目录
- 默认包含 `changed_files`、`commits` 和已有 `comments`
- 如果评论量太大，可追加 `--no-comments`

```json
{
  "pr": {
    "number": 123,
    "title": "...",
    "author": "...",
    "branch": "feature → main",
    "stats": {
      "files_changed": 3,
      "commits": 2,
      "comments": 5,
      "unresolved_comments": 2
    },
    "changed_files": [
      {
        "filename": "src/main.py",
        "status": "modified",
        "patch": "...",
        "content": "..."
      }
    ]
  },
  "commits": [...],
  "comments": [...]
}
```

**重要**：提取的 JSON 文件已经包含了所有 diff（`patch`）、文件内容（`content`）以及已有 PR 评论。
- **不需要** `git fetch` 或 `git diff`
- **不需要** 切换分支或修改本地代码
- 直接读取 JSON 文件中的 `changed_files`、`commits` 和 `comments` 进行审查即可
- 如果需要“回复某一条已有 review 意见”而不是提交新的审查结果，请切换到 `review-resolution`

### 提交审查结果

```bash
python3 pr_review.py --pr 123 --submit-review ./tmp/{repo}_pr_123_issues.json --ai-model claude-sonnet-4
```

**参数**：
- `--pr`: PR 编号
- `--owner`: 目标仓库 owner（可选，覆盖 `config.json`）
- `--repo`: 目标仓库 repo（可选，覆盖 `config.json`）
- `--url`: PR 链接（可选，自动解析 `owner/repo/pr_number`）
- `--no-comments`: 在提取信息模式下跳过抓取已有 PR 评论
- `--submit-review`: 审查结果 JSON 文件
- `--ai-model`: AI 模型名称（**必须指定真实模型名称**，用于签名）
- `--dry-run`: 仅显示计划

**重要**：`--ai-model` 参数**必须指定你的真实模型名称**，以便在评论中准确标识来源。

**常见模型名称**：`claude-sonnet-4`、`claude-opus-4`、`gpt-4`、`gpt-4o`、`gemini-pro`、`gemini-1.5-pro`

## 你需要生成的 issues.json 格式

**重要要求**：
1. **必须使用中文**输出所有内容
2. **必须包含修复方案**（fix_code 字段）
3. **文件保存到 ./tmp 目录**，文件名格式：`./tmp/{repo}_pr_{number}_issues.json`

```json
[
  {
    "file": "src/main.py",
    "line": 52,
    "type": "bug",
    "severity": "error",
    "confidence": 95,
    "title": "缺少异常处理",
    "description": "response.json() 可能抛出 JSONDecodeError",
    "context_code": "return response.json()",
    "fix_code": "try:\n    return response.json()\nexcept json.JSONDecodeError:\n    return {}",
    "fix_explanation": "添加异常处理避免程序崩溃"
  }
]
```

### 字段说明

| 字段 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| file | ✅ | 文件路径 | |
| line | ✅ | 行号 | |
| type | ✅ | 问题类型 | `bug`, `security`, `performance`, `maintainability` |
| severity | ✅ | 严重程度 | `error`, `warning`, `suggestion`, `info` |
| confidence | ✅ | 置信度 (0-100) | |
| title | ✅ | 问题标题（中文） | |
| description | ✅ | 详细描述（中文） | |
| context_code | ❌ | 相关代码 | |
| fix_code | ✅ | 修复代码（必须提供） | |
| fix_explanation | ✅ | 修复说明（中文） | |

## 配置

在 `config.json` 中（参考 [`examples/config.example.json`](../../examples/config.example.json)）：

```json
{
  "atomgit": {
    "token": "$ATOMGIT_TOKEN",
    "owner": "your-org",
    "repo": "your-repo",
    "baseUrl": "https://api.atomgit.com"
  }
}
```

## Related Skills

- `pr`: 创建 PR、同步标题/描述、获取 PR 管理上下文；**不负责**通用 review 判定
- `review-resolution`: 处理已有检视意见（回复/解决 discussion）
