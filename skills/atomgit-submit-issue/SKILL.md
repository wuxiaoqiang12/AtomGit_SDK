---
name: atomgit-submit-issue
description: "AtomGit Issue 提交工具。当用户需要「提交Issue」「创建问题」「create issue」「submit issue」「报告Bug」「提出建议」或「记录待办事项」时调用。"
license: MIT
---

# AtomGit Issue Submit Tool

创建新 Issue 或管理现有 Issue。

## 环境准备

确保已安装 atomgit-sdk：

```bash
pip install -e /path/to/atomgit_sdk
```

## 获取仓库配置

建议通过 `git remote -v` 确认仓库的 owner 和 repo：

```bash
git remote -v
```

## 快速使用

### 创建 Issue

```bash
python3 submit_issue.py --title "发现一个 Bug" --body "在执行 build.sh 时报错..."

python3 submit_issue.py --title "功能建议: 增加单元测试" --body "为了提高代码质量..." --labels enhancement,bug --assignees someone
```

### 获取 Issue 信息

```bash
python3 submit_issue.py --issue 123 --fetch-info
```

## API 说明

### submit_issue.py

创建或更新 Issue。

**参数**:
- `--title`: Issue 标题（创建时必需）
- `--body`: Issue 描述
- `--labels`: 标签列表，逗号分隔
- `--assignees`: 指派人列表，逗号分隔
- `--issue`: Issue 编号（用于更新或获取信息）
- `--state`: Issue 状态（open 或 closed）
- `--fetch-info`: 提取 Issue 详情到 JSON
- `--dry-run`: 仅显示计划，不执行实际操作

## 注意事项

1. 确保 `ATOMGIT_TOKEN` 已正确配置在环境变量中
2. 建议在标题中使用清晰的前缀，如 `[Bug]`, `[Feature]`, `[Task]` 等
