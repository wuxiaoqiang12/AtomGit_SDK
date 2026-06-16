# AtomGit SDK

> Unified Python SDK for the AtomGit / GitCode API — PR management, issues, code review and discussion repair workflows.

统一的 AtomGit API 封装 SDK，可用于 AtomGit / GitCode 上的 PR、Issue、Review 与评论修复流程。

## Skill 示例

本仓库的 [`skills/`](skills/) 目录提供 **5 个基于 SDK 的协作自动化 skill 示例**，演示如何把 PR / Issue / Review 工作流编排成可复用的 Agent skill：

| 示例 | 功能 | 用到的 SDK 能力 |
|------|------|----------------|
| [collaboration](skills/collaboration/SKILL.md) | 协作意图路由（识别请求并分流） | — |
| [issue](skills/issue/SKILL.md) | Issue 创建 / 查询 / 更新 / 关闭 | `IssueService` |
| [pr](skills/pr/SKILL.md) | PR 创建 / 上下文提取 / 描述同步 | `create_pull_request`、`get_pr_*` |
| [pr-review](skills/pr-review/SKILL.md) | PR 代码审查（行内评论提交） | `calculate_diff_position`、`submit_batch_comments` |
| [review-resolution](skills/review-resolution/SKILL.md) | 评审意见处理（回复 / 解决 / 修复） | `RepairService` |

每个示例都支持 `--owner/--repo/--url` 指定任意 AtomGit 仓库，脚本只做工作流编排，HTTP 统一走 SDK。详见 [skills/README.md](skills/README.md)。

## 特性

- **统一的 API 客户端**: 封装所有 AtomGit API 调用，自带 Bearer 鉴权与安全方法重试
- **API 合规**: 每个请求携带官方要求的 `X-Api-Version` 头；403/429 限流时抛 `RateLimitError`
- **完整 API 覆盖**: 内置 catalog 覆盖官方文档全部 96 个 endpoint（17 模块），`from_docs()` 可从官方文档站同步
- **20+ typed wrapper**: user / org / repo / branch / tag / commit / milestone / search / check-run / commit-status
- **高级服务**: `PRService`、`IssueService`、`RepairService` 封装常用操作
- **类型安全**: Pydantic 模型 + 完整异常体系
- **Diff 解析**: 准确的 Diff 行号映射算法
- **轻量依赖**: 仅依赖 `requests` 和 `pydantic`

## 安装

```bash
pip install atomgit-sdk
```

如需开发/测试可选依赖：

```bash
pip install "atomgit-sdk[dev]"
```

## 快速开始

### 基础使用

```python
from atomgit_sdk import AtomGitClient, AtomGitConfig

# 从配置文件创建（参考 examples/config.example.json）
config = AtomGitConfig.from_json("config.json")
client = AtomGitClient(config)

# 获取 PR 信息
pr = client.get_pull_request(123)
print(f"PR Title: {pr['title']}")
```

### 使用 PRService

```python
from atomgit_sdk.services import PRService

service = PRService(client)

# 获取完整的 PR 上下文
context = service.get_full_pr_context(123)
print(f"Files changed: {len(context['files'])}")

# 提交评论
service.submit_inline_comment(123, {
    "path": "src/main.py",
    "position": 10,
    "body": "建议优化这段代码"
})
```

### 回复单条 PR review 意见

官方 API 为 review discussion 提供了独立的回复与解决状态接口。优先使用这些封装，而不是在业务代码里直接拼 HTTP：

```python
from atomgit_sdk.services import RepairService

repair = RepairService(client)

# 按评论 ID 回复；SDK 会先读取该评论并找到 discussion_id
repair.reply_to_comment(123, comment_id=456, reply_body="已按建议修复。")

# 按评论 ID 标记其 discussion 已解决
repair.resolve_comment(123, comment_id=456, resolved=True)

# 已知 discussion_id 时也可以直接调用
client.reply_to_pr_discussion(123, "discussion-id", "补充说明...")
client.set_pr_discussion_resolved(123, "discussion-id", True)
```

### 调用官方 API catalog

官方 API 文档大多只公开标题、HTTP 方法和路径。SDK 采用 “catalog + typed wrapper” 的方式：常用协作流程使用显式方法，长尾 API 通过 catalog 调用。

```python
from atomgit_sdk import APICatalog

# 内置常用协作 endpoint
matches = client.find_api_endpoints(path_contains="/pulls/comments")

# 调用内置 catalog 中的 endpoint
comment = client.call_api(
    "get-api-v-5-repos-owner-repo-pulls-comments-id",
    path_params={"owner": "your-org", "repo": "your-repo", "id": 456},
)

# 需要完整官方 endpoint 列表时，可从文档同步
full_catalog = APICatalog.from_docs()
```

### Diff 位置计算

```python
from atomgit_sdk.utils import calculate_diff_position

patch = """@@ -10,5 +10,6 @@
 context line
-old line
+new line
 another line"""

position = calculate_diff_position(patch, line_number=11)
print(f"Position in diff: {position}")
```

## 配置

参考 [`examples/config.example.json`](examples/config.example.json) 创建你的 `config.json`：

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

`token` 字段支持以 `$ATOMGIT_TOKEN` 作为占位符，SDK 会在运行时从同名环境变量解析，避免把凭据写入文件：

```bash
export ATOMGIT_TOKEN="your-personal-access-token"
```

## 目录结构

```
atomgit_sdk/
├── src/atomgit_sdk/          # SDK 源码
│   ├── __init__.py           # 导出常用类
│   ├── api_catalog.py        # 官方 API 端点目录（96 endpoint）
│   ├── client.py             # API 客户端 + typed wrapper
│   ├── config.py             # 配置管理
│   ├── models.py             # 数据模型
│   ├── exceptions.py         # 自定义异常
│   ├── utils/                # diff / url / content 工具
│   └── services/             # PRService / IssueService / RepairService
├── skills/                   # atomgit 协作 skill 示例（5 个）
├── .agents/skills/           # 项目自身 skill（publish-sdk 等）
├── scripts/                  # publish.sh 等工具脚本
├── examples/                 # 配置与用法示例
└── tests/                    # 单元测试
```

## API 参考

### AtomGitConfig

配置管理类。**方法:** `from_json(path)` 从 JSON 文件加载配置。

### AtomGitClient

API 客户端。除下列方法外，还提供 user / org / repo / branch / tag / commit / milestone / search / check-run / commit-status 等 20+ typed wrapper。

**PR 相关:** `get_pull_request`、`get_pr_files`、`get_pr_files_json`、`get_pr_commits`、`get_pr_comments`、`get_pr_comment`、`reply_to_pr_discussion`、`set_pr_discussion_resolved`、`get_file_content`、`call_api`

### PRService

`get_full_pr_context`、`submit_inline_comment`、`submit_batch_comments`、`reply_to_pr_discussion`、`set_pr_discussion_resolved`

### RepairService

`get_unresolved_comments`、`reply_to_comment`、`resolve_comment`、`resolve_discussion`

## 测试

```bash
pytest tests/
```

## 开发

本地开发：

```bash
pip install -e ".[dev]"
pytest tests/
```

**发布到 PyPI** 见 [`.agents/skills/publish-sdk/SKILL.md`](.agents/skills/publish-sdk/SKILL.md)——它封装了隔离 venv 构建与上传流程，用 `scripts/publish.sh` 一键执行，规避宿主环境的 `requests_toolbelt`/`PYTHONPATH` 污染问题。

## 贡献

欢迎提交 Issue 与 Pull Request。提交代码请签署 DCO（`git commit -s`）。也欢迎参考 [`skills/`](skills/) 的示例，基于 SDK 编排新的协作工作流。

## 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

[Apache License 2.0](LICENSE)
