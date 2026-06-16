# Skill 示例

本目录是基于 `atomgit-sdk` 构建的**协作自动化 skill 示例**，演示如何用 SDK 把 PR / Issue / Review 工作流编排成可复用的 Agent skill。每个子目录是一个独立示例，含 `SKILL.md`（触发条件与工作流）和可执行脚本。

## 示例清单

| skill | 功能 | 用到的 SDK 能力 |
|-------|------|----------------|
| [`collaboration`](collaboration/SKILL.md) | 协作意图路由（识别请求并分流到具体 skill） | — |
| [`issue`](issue/SKILL.md) | Issue 创建 / 查询 / 更新 / 关闭 | `IssueService`、`resolve_atomgit_context` |
| [`pr`](pr/SKILL.md) | PR 创建 / 上下文提取 / 描述同步 | `create_pull_request`、`get_pr_*`、`update_pull_request` |
| [`pr-review`](pr-review/SKILL.md) | PR 代码审查（提取上下文 + 行内评论提交） | `calculate_diff_position`、`submit_batch_comments` |
| [`review-resolution`](review-resolution/SKILL.md) | 评审意见处理（回复 / 解决 / 修复） | `RepairService`（review 线程聚合、嵌套回复、解决状态） |

> 另有项目自身的发布 skill 在 [`../.agents/skills/publish-sdk/`](../.agents/skills/publish-sdk/SKILL.md)，封装 PyPI 发布流程。

## 快速开始

1. 安装 SDK：`pip install atomgit-sdk`
2. 配置 `ATOMGIT_TOKEN` 环境变量，并准备 `config.json`（参考 [`../examples/config.example.json`](../examples/config.example.json)）
3. 进入某个 skill 的 `scripts/` 目录，按其 `SKILL.md` 执行，例如：

```bash
cd pr/scripts
python3 pr_creation.py --branch feat/my-feature --fork-owner your-fork --title "feat: ..."
```

## 设计要点

- **SDK 即依赖**：所有 skill 通过 `pip install atomgit-sdk` 获取 SDK，不再依赖项目内 vendor 路径或 `PYTHONPATH` 注入。
- **任意仓库**：每个 skill 都支持 `--owner/--repo/--url` 覆盖，可对任意 AtomGit 仓库操作。
- **编排与抽象分离**：skill 脚本只做工作流编排（参数解析、JSON 上下文生成、文件修复），所有 HTTP 调用、认证、重试、URL 解析统一走 SDK。
- **Agent 友好**：上下文以 `tmp/{repo}_pr_<n>_*.json` 落盘，方便 Agent 用 `cat`/`jq` 读取后再决策。

## 自行扩展

这些示例是起点。基于 SDK 的 `AtomGitClient`、`PRService`、`IssueService`、`RepairService` 以及 catalog 里的 96 个官方 endpoint，可以方便地编排更多工作流（如里程碑管理、提交状态、组织成员、讨论等）。
