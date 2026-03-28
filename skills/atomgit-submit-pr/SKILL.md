---
name: atomgit-submit-pr
description: "AtomGit PR 提交工具。当用户需要「提交PR」「创建合并请求」「create pull request」「submit PR」「更新PR描述」或在功能开发完成后准备合入 upstream 仓库时调用。"
license: MIT
---

# AtomGit PR Submit Tool

创建新 PR 或更新现有 PR 描述。

## 环境准备

确保已安装 atomgit-sdk：

```bash
pip install -e /path/to/atomgit_sdk
```

## 获取 Fork Owner

在创建 PR 前，通过 `git remote -v` 获取 fork owner：

```bash
git remote -v
```

输出示例：
```
origin    git@atomgit.com:YourName/your-repo.git (fetch)
origin    git@atomgit.com:YourName/your-repo.git (push)
upstream  git@atomgit.com:your-org/your-repo.git (fetch)
upstream  git@atomgit.com:your-org/your-repo.git (push)
```

## 快速使用

### 创建 PR

```bash
# 1. 获取变更信息
git diff upstream/master..HEAD

# 2. 创建 PR
python3 create_pr.py --branch feat/my-feature --fork-owner YourName --title "feat(scope): summary" --description-file pr_description.md
```

### 基础用法

```bash
python3 create_pr.py --branch feat/my-feature --fork-owner YourName --title "fix: specific issue" --body "## Background\n...\n## Changes\n...\n## Verification\n..."
```

### 生成/更新 PR 描述

**步骤 1: 提取 PR 上下文**
```bash
python3 generate_pr.py --pr 123 --fetch-info
```

**步骤 2: Agent 分析后生成 description.json，然后同步**
```bash
python3 generate_pr.py --pr 123 --update-pr description.json
```

## API 说明

### create_pr.py

创建新的 Pull Request。

**参数**:
- `--branch`: 分支名（可选，默认当前分支）
- `--fork-owner`: Fork 仓库的 owner（必需）
- `--title`: PR 标题（可选，自动生成）
- `--body`: PR 描述（可选）
- `--description-file`: 从文件读取 PR 描述
- `--base`: 目标分支（默认：master）
- `--draft`: 创建草稿 PR
- `--dry-run`: 仅显示计划
- `--ai-model`: AI 模型名称，用于签名

### generate_pr.py

管理已有 PR 的数据。

**模式**:
1. `--pr <NUM> --fetch-info`: 提取 PR 上下文
2. `--pr <NUM> --update-pr <JSON>`: 同步描述到服务器

## 注意事项

1. 建议使用 `feat/`, `fix/`, `docs/`, `refactor/` 等分支前缀
2. 确保提交信息符合规范
3. 确保 CI 通过后再合并
