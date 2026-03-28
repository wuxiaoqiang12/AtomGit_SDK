---
name: atomgit-code-review
description: "AtomGit 代码审查工具。当用户需要「代码审查」「代码评审」「code review」「PR review」「审阅代码」「检查Bug」或提交检视意见到 AtomGit 时使用。"
license: MIT
---

# AtomGit Code Review

提取 PR 信息并提交代码审查评论到 AtomGit。

## 环境准备

确保已安装 atomgit-sdk：

```bash
pip install -e /path/to/atomgit_sdk
```

## 文件读取说明

输出文件位于项目 `./tmp` 目录：

```bash
# 读取 PR 信息
cat ./tmp/pr_123_info.json

# 读取审查结果
cat ./tmp/pr_123_issues.json
```

使用 `jq` 提取特定文件信息：

```bash
jq '.pr.changed_files[].filename' ./tmp/pr_123_info.json
jq '.pr.changed_files[] | select(.filename == "lib/api.py") | .content' ./tmp/pr_123_info.json
```

## 快速使用

```bash
# 步骤1: 提取 PR 信息
python3 atomgit_reviewer.py --pr 123

# 步骤2: 分析代码并生成 issues.json

# 步骤3: 人类确认审查结果

# 步骤4: 提交审查结果（必须指定 --ai-model）
python3 atomgit_reviewer.py --pr 123 --submit-review ./tmp/pr_123_issues.json --ai-model your-model-name
```

## API 说明

### 提取 PR 信息

```bash
python3 atomgit_reviewer.py --pr 123
```

**输出**: `./tmp/pr_{number}_info.json`

```json
{
  "pr": {
    "number": 123,
    "title": "...",
    "author": "...",
    "branch": "feature -> main",
    "changed_files": [
      {
        "filename": "lib/api.py",
        "status": "modified",
        "patch": "...",
        "content": "..."
      }
    ]
  }
}
```

### 提交审查结果

```bash
python3 atomgit_reviewer.py --pr 123 --submit-review ./tmp/pr_123_issues.json --ai-model your-model-name
```

**参数**：
- `--pr`: PR 编号
- `--submit-review`: 审查结果 JSON 文件
- `--ai-model`: AI 模型名称（用于签名）
- `--dry-run`: 仅显示计划

## issues.json 格式

```json
[
  {
    "file": "lib/api.py",
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

| 字段 | 必填 | 说明 |
|------|------|------|
| file | Yes | 文件路径 |
| line | Yes | 行号 |
| type | Yes | 问题类型: `bug`, `security`, `performance`, `maintainability` |
| severity | Yes | 严重程度: `error`, `warning`, `suggestion`, `info` |
| confidence | Yes | 置信度 (0-100) |
| title | Yes | 问题标题 |
| description | Yes | 详细描述 |
| context_code | No | 相关代码 |
| fix_code | Yes | 修复代码 |
| fix_explanation | Yes | 修复说明 |

## 配置

在项目根目录的 `config.json` 中：

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

- `atomgit-code-review-repair`: 修复检视意见
