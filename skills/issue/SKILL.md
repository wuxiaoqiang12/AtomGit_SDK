---
name: atomgit-issue
description: "AtomGit Issue 工作流示例。当用户需要\"创建Issue\"、\"查看Issue详情\"、\"更新Issue\"、\"关闭/重开Issue\"、\"create issue\"、\"fetch issue info\"、\"update issue\"、\"report bug\"、\"feature request\"或围绕 Issue 做任何创建/读取/更新动作时调用。只要目标是某个 AtomGit 仓库的 Issue，默认优先使用本 skill。"
license: MIT
---

# AtomGit Issue Workflow Tool

创建、读取、更新或关闭 Issue。

只要用户提到 Issue / bug / feature request，默认视为 AtomGit 工作流并优先使用本 skill。

本 skill 支持对 **任意 AtomGit 仓库** 指定目标：

- `--owner` / `--repo`: 显式覆盖 `config.json` 中的仓库
- `--url`: 从 AtomGit / GitCode 的 Issue 或仓库链接自动解析 `owner/repo/issue_number`

## 环境准备

安装 atomgit-sdk（已发布到 PyPI）：

```bash
pip install atomgit-sdk
```

并配置 `ATOMGIT_TOKEN` 环境变量，以及 `config.json`（参考 [`examples/config.example.json`](../../examples/config.example.json)）。

## 确认目标仓库

建议通过 `git remote -v` 确认仓库的 owner 和 repo：

```bash
git remote -v
```

脚本会自动从环境变量或 `git remote` 中推断，也可以通过参数指定。

## 快速使用

### 创建 Issue

```bash
# 提交一个简单的 Issue
python3 issue_management.py --title "发现一个 Bug" --body "在执行 build.sh 时报错..."

# 指定标签和指派人
python3 issue_management.py --title "功能建议: 增加单元测试" --body "为了提高代码质量..." --labels enhancement,bug --assignees your-name

# 跨仓库：直接指定 owner/repo
python3 issue_management.py --owner some-org --repo some-repo --title "[Bug] xxx"
```

### 获取 Issue 信息 (Agent 驱动)

当需要分析已有 Issue 时，Agent 可以调用：

```bash
python3 issue_management.py --issue 123 --fetch-info

# 直接从链接解析
python3 issue_management.py --url https://atomgit.com/some-org/some-repo/issues/123 --fetch-info

# 如只需要 Issue 主体，显式关闭评论抓取
python3 issue_management.py --issue 123 --fetch-info --no-comments
```
默认会一并抓取 Issue 评论并写入 `comments_detail` 字段。Agent 会读取生成的 `tmp/{repo}_issue_123_context.json`。

## API 说明

### issue_management.py

创建或更新 Issue。

**参数**:
- `--title`: Issue 标题（创建时**必需**）
- `--body`: Issue 描述
- `--labels`: 标签列表，逗号分隔（如: bug,high-priority）
- `--assignees`: 指派人列表，逗号分隔
- `--issue`: Issue 编号（用于更新或获取信息，可由 `--url` 自动解析）
- `--state`: Issue 状态（open 或 closed，用于更新）
- `--fetch-info`: 提取 Issue 详情到 JSON 文件
- `--no-comments`: 在 `--fetch-info` 模式下跳过评论抓取
- `--config`: 配置文件路径（默认 `config.json`）
- `--owner`: 目标仓库 owner（可选，覆盖 `config.json`）
- `--repo`: 目标仓库 repo（可选，覆盖 `config.json`）
- `--url`: Issue 或仓库链接（可选，自动解析 `owner/repo/issue_number`）
- `--dry-run`: 仅显示计划，不执行实际操作

**示例**:
```bash
# 更新 Issue 状态
python3 issue_management.py --issue 123 --state closed

# 修改 Issue 标题和内容
python3 issue_management.py --issue 123 --title "已修正: 编译错误" --body "通过更新依赖已解决。"
```

## 注意事项

1. **环境配置**: 确保 `ATOMGIT_TOKEN` 已正确配置在环境变量中。
2. **Issue 规范**: 建议在标题中使用清晰的前缀，如 `[Bug]`, `[Feature]`, `[Task]` 等。
3. **标签管理**: 使用仓库已有的标签，或者在提交时创建清晰的新标签。
