# AtomGit SDK

统一的 AtomGit/GitCode API 封装 SDK，提供 AtomGit API 调用能力，可用于构建 Skills。

## 特性

- **统一的 API 客户端**: 封装所有 AtomGit/GitCode API 调用
- **类型安全**: 使用 Pydantic 模型进行数据验证
- **Diff 解析**: 准确的 Diff 行号映射算法
- **高级服务**: PRService、IssueService、RepairService 封装常用操作
- **轻量依赖**: 仅需 requests 和 pydantic

## 安装

```bash
pip install -e .
```

## 快速开始

### 基础使用

```python
from atomgit_sdk import AtomGitClient, AtomGitConfig

# 从配置文件创建
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

### URL 解析

```python
from atomgit_sdk.utils import parse_atomgit_url

result = parse_atomgit_url("https://atomgit.com/owner/repo/pulls/123")
# => {"owner": "owner", "repo": "repo", "pr_number": 123}
```

## 目录结构

```
atomgit_sdk/
├── src/
│   └── atomgit_sdk/
│       ├── __init__.py          # 导出常用类
│       ├── config.py            # 配置管理
│       ├── client.py            # API 客户端
│       ├── models.py            # 数据模型
│       ├── exceptions.py        # 自定义异常
│       ├── utils/               # 工具函数
│       │   ├── diff.py          # Diff 解析
│       │   ├── url.py           # URL 解析
│       │   └── content.py       # 内容处理
│       └── services/            # 业务服务
│           ├── pr_service.py    # PR 操作
│           ├── issue_service.py # Issue 操作
│           └── repair_service.py # 修复操作
├── skills/                      # 可用的 Skills
│   ├── atomgit-submit-issue/    # Issue 提交
│   ├── atomgit-submit-pr/       # PR 提交
│   ├── atomgit-code-review/     # 代码审查
│   └── atomgit-code-review-repair/ # 审查修复
├── tests/                       # 单元测试
└── scripts/                     # 辅助脚本
```

## 配置

在项目根目录的 `config.json` 中配置：

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

支持环境变量引用（如 `$ATOMGIT_TOKEN`），在运行时会自动展开。

## API 参考

### AtomGitConfig

配置管理类。

**方法:**
- `from_json(path: str)`: 从 JSON 文件加载配置（支持环境变量展开）

### AtomGitClient

API 客户端。

**方法:**
- `get_pull_request(pr_number: int)`: 获取 PR 详情
- `get_pr_files(pr_number: int)`: 获取 PR 文件列表
- `get_pr_commits(pr_number: int)`: 获取 PR 提交列表
- `get_pr_comments(pr_number: int)`: 获取 PR 评论
- `get_pr_diff(pr_number: int)`: 获取 PR Diff
- `get_file_content(path: str, ref: str)`: 获取文件内容
- `submit_inline_comment(pr_number, comment)`: 提交行内评论
- `submit_pr_comment(pr_number, body)`: 提交 PR 级评论
- `submit_batch_comments(pr_number, comments)`: 批量提交评论
- `create_pull_request(title, body, head, base, draft)`: 创建 PR
- `update_pull_request(pr_number, ...)`: 更新 PR
- `get_issues(state)`: 获取 Issue 列表
- `create_issue(title, body, labels, assignees)`: 创建 Issue
- `update_issue(issue_number, ...)`: 更新 Issue

### PRService

PR 操作服务。

**方法:**
- `get_full_pr_context(pr_number: int)`: 获取完整 PR 上下文
- `extract_pr_info(pr_number: int)`: 提取 PR 信息供审查
- `submit_issues(pr_number, issues, ...)`: 提交审查结果
- `submit_inline_comment(...)`: 提交行内评论
- `submit_batch_comments(...)`: 批量提交评论
- `create_pr(...)`: 创建 PR

### IssueService

Issue 操作服务。

### RepairService

审查评论修复服务。

**方法:**
- `get_unresolved_comments(pr_number)`: 获取未解决评论
- `reply_to_comment(pr_number, comment_id, reply_body)`: 回复评论

## 测试

```bash
pip install -e ".[dev]"
pytest tests/
```

## 许可证

MIT
