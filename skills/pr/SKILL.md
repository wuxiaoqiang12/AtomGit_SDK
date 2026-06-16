---
name: atomgit-pr
description: "AtomGit PR 工作流示例。当用户需要\"创建PR\"、\"更新PR描述\"、\"同步PR标题/正文\"、\"生成PR摘要\"、\"create pull request\"、\"open merge request\"、\"update PR description\"、\"generate PR summary\"或围绕 PR 管理动作工作时调用。它负责 PR 资源的创建和维护，不负责通用代码 review；只要目标是某个 AtomGit 仓库的 PR / merge request 管理，默认优先使用本 skill。"
license: MIT
---

# AtomGit PR Workflow Tool

创建新 PR、提取 PR 管理上下文或更新现有 PR 描述。

如果用户的目标是“**review 一个 PR / 帮我看看这个 PR 有没有问题 / 分析已有评论**”，不要使用本 skill，改用 `pr-review`。

只要用户提到 PR / merge request，默认视为 AtomGit 工作流并优先使用本 skill。

本 skill 支持对 **任意 AtomGit 仓库** 指定目标：

- `--owner` / `--repo`: 显式覆盖 `config.json` 中的仓库
- `--url`: 从 AtomGit / GitCode 的仓库或 PR 链接自动解析 `owner/repo`

## 环境准备

安装 atomgit-sdk（已发布到 PyPI）：

```bash
pip install atomgit-sdk
```

并配置 `ATOMGIT_TOKEN` 环境变量，以及 `config.json`（参考 [`examples/config.example.json`](../../examples/config.example.json)）。

## 获取 Fork Owner（必需）

在创建 PR 前，**必须**先通过 `git remote -v` 获取 fork owner：

```bash
git remote -v
```

输出示例：
```
origin    git@atomgit.com:YourName/your-repo.git (fetch)
origin    git@atomgit.com:YourName/your-repo.git (push)
upstream  git@atomgit.com:upstream-org/your-repo.git (fetch)
upstream  git@atomgit.com:upstream-org/your-repo.git (push)
```

从中提取 fork owner（即个人仓库的用户名，如 `YourName`），然后通过 `--fork-owner` 参数传递给脚本。

## 快速使用

### 创建 PR (推荐 Agent 方式)

Agent 在创建 PR 时，描述文件应围绕本次提交真正的审阅重点组织内容；复杂流程或架构变化优先使用 **Mermaid 图表**，简单或纯文档类变更不要机械套用重型模板。

**PR 描述建议：**

1.  **默认使用中文撰写**：PR 标题和正文描述均默认使用中文。仅在用户明确要求时切换为英文（标题可保留英文以符合 commit 规范）。
2.  **超链接使用**: 对相关的 Issue、PR、技术规范或设计文档，使用 Markdown 超链接进行关联，方便审阅者查阅背景。
3.  **深度结构化内容**:
    *   **按提交内容动态组织**: 不要机械要求每个 PR 都包含同一组标题。围绕 commit 真正的变化点组织内容。
    *   **背景与动机**: 说明问题根源、业务痛点或需求背景；简单修复可简写。
    *   **方案概述**: 描述解决思路、关键设计决策。只有在流程、状态转换或架构关系较复杂时，才使用 Mermaid 流程图或时序图。
    *   **技术细节**: 按模块拆解代码、配置、脚本或文档层面的关键变更，解释为什么这样改。
    *   **文档联动**: 如果提交改变了用户可见的安装、构建、运行、依赖、接口、配置或使用方式，应同步更新对应文档。
    *   **影响范围**: 仅在确有影响时说明对系统行为、接口、依赖、性能、部署或使用方式的影响。
    *   **验证结果（条件性章节）**:
        *   只有当本次 PR 做过**真实验证**且该验证对审阅结论有价值时才写。
        *   必须写清楚 **Scenario（什么场景下验证）**、**Method（如何验证，可含命令）**、**Result（验证结果是什么）**。
        *   禁止把 `git diff`、`git status`、文件列表这类仅用于查看变更的命令当作 Verification。
        *   对纯文档、注释、gitignore、纯元数据等**不涉及运行时行为**的提交，可以省略 Verification。

```bash
# 1. 获取变更信息（仅用于分析变更，不可直接当作 Verification）
git diff upstream/master..HEAD

# 2. Agent 深度分析并生成专业描述文件 pr_description.md
#    根据 commit 内容选择合适章节；仅在做过真实验证时包含 Verification。

# 3. 创建 PR
python3 pr_creation.py --branch feat/my-feature --fork-owner your-fork --title "feat(scope): technical summary" --description-file pr_description.md
```

### 基础用法

```bash
# 步骤1: 获取 fork owner
git remote -v

# 步骤2: 创建 PR
python3 pr_creation.py --branch feat/my-feature --fork-owner your-fork --title "fix: specific issue" --body "## Background\n...\n## Changes\n...\n## Impact\n..."

# 跨仓库：直接指定目标仓库
python3 pr_creation.py --branch feat/my-feature --fork-owner your-fork --owner some-org --repo some-repo --body "..."

# 跨仓库：从链接自动解析 owner/repo
python3 pr_creation.py --branch feat/my-feature --fork-owner your-fork --url https://atomgit.com/some-org/some-repo --body "..."
```

### 生成/更新 PR 描述 (Agent 驱动)

当需要为已有 PR 生成高质量描述时，遵循以下 Agent 工作流：

**步骤 1: 提取 PR 上下文**
```bash
python3 pr_management.py --pr 123 --fetch-info

# 默认会包含 PR 评论；如只看提交和 Diff，可显式关闭
python3 pr_management.py --pr 123 --fetch-info --no-comments
```
Agent 会读取生成的 `tmp/{repo}_pr_123_context.json`，其中默认包含提交记录、修改文件、代码 Diff (patch) 以及 PR 评论。

**步骤 2: Agent 分析与同步**
Agent 分析完 Diff 后，会生成一份 `description.json`:
```json
{
  "title": "feat: 新功能标题",
  "description": "详细的变更逻辑说明..."
}
```
然后运行同步命令：
```bash
python3 pr_management.py --pr 123 --update-pr description.json
```

## API 说明

### pr_creation.py

创建新的 Pull Request。

**参数**:
- `--branch`: 分支名（可选，默认当前分支）
- `--fork-owner`: Fork 仓库的 owner（**必需**，通过 `git remote -v` 获取）
- `--title`: PR 标题（可选，自动生成）
- `--body`: PR 描述（可选，自动生成）
- `--description-file`: 从文件读取 PR 描述
- `--base`: 目标分支（默认：master）
- `--owner`: 目标仓库 owner（可选，覆盖 `config.json`）
- `--repo`: 目标仓库 repo（可选，覆盖 `config.json`）
- `--url`: AtomGit / GitCode 仓库或 PR 链接（可选，自动解析 `owner/repo`）
- `--draft`: 创建草稿 PR（可选）
- `--dry-run`: 仅显示计划，不创建

**示例**:
```bash
# 完整示例
python3 pr_creation.py --branch feat/new-feature --fork-owner your-fork

# 指定标题
python3 pr_creation.py --branch feat/new-feature --fork-owner your-fork --title "feat: add new feature"
```

### pr_management.py

管理和维护已有 PR 的数据。

**模式**:
1. `--pr <NUM> --fetch-info`: 提取 PR 的完整上下文 (提交、文件、Diff)，Agent 学习用。
2. `--pr <NUM> --update-pr <JSON>`: 将 Agent 生成的描述同步到服务器。

**参数**:
- `--pr`: PR 编号（可由 `--url` 自动解析）
- `--owner`: 目标仓库 owner（可选，覆盖 `config.json`）
- `--repo`: 目标仓库 repo（可选，覆盖 `config.json`）
- `--url`: PR 链接（可选，自动解析 `owner/repo/pr_number`）
- `--output-dir`: JSON 输出目录 (默认: ./tmp)
- `--no-comments`: 在 `--fetch-info` 模式下跳过 PR 评论抓取
- `--ai-model`: 签名使用的 AI 名称 (默认: agent)
- `--dry-run`: 预览生成的描述但不执行更新

## PR 描述格式

PR 描述**默认使用中文**撰写（标题可用英文以符合 commit 规范，正文描述用中文）。如果用户明确要求英文，则切换为英文。

PR 描述通常应包含与本次提交最相关的内容，而不是固定模板。常见章节包括：

- **背景与动机**：为什么要改
- **方案概述 / 技术细节**：改了什么、为什么这样改
- **文档联动**：用户可见使用方式变更时，说明同步更新了哪些文档
- **影响范围**：影响范围与风险
- **验证结果（可选）**：仅在存在真实验证时写清场景、方法与结果

对于纯文档、注释、`.gitignore`、说明文字等不涉及运行时行为的 PR，可以不写 Verification。

## 注意事项

1. **分支命名**: 建议使用 `feat/`, `fix/`, `docs/`, `refactor/` 等前缀
2. **提交信息**: 确保提交信息符合规范
3. **代码审查**: 创建 PR 后等待代码审查
4. **CI 检查**: 确保 CI 通过后再合并
5. **跨仓库前提**: 创建 PR 时当前本地 worktree 仍需与目标仓库代码相匹配；`--owner/--repo/--url` 只负责切换 AtomGit API 目标，不会替你切换本地 Git 工作区
