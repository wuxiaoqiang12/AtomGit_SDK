---
name: atomgit-code-review-repair
description: "AtomGit PR 检视意见修复工具。当用户收到评审意见并需要「修复PR」「修复检视意见」「fix review comments」「apply fixes」「回复评论」或自动化闭环评审流程时使用。"
license: MIT
---

# AtomGit Code Review Repair

响应代码审查意见，自动修复并回复评论。

## 环境准备

确保已安装 atomgit-sdk：

```bash
pip install -e /path/to/atomgit_sdk
```

## 文件读取说明

输出文件位于项目 `./tmp` 目录：

```bash
cat ./tmp/pr_123_unresolved_comments.json
cat ./tmp/pr_123_fix_results.json
```

## 快速使用

```bash
# 步骤1: 获取未解决的评论
python3 repair_pr.py --pr 123

# 步骤2: 分析评论并生成修复方案

# 步骤3: 人类确认修复方案

# 步骤4: 提交修复（必须指定 --ai-model）
python3 repair_pr.py --pr 123 --submit-repair ./tmp/pr_123_fix_results.json --ai-model your-model-name
```

## API 说明

### 获取未解决评论

```bash
python3 repair_pr.py --pr 123
```

**输出**: `./tmp/pr_{number}_unresolved_comments.json`

### 提交修复

```bash
python3 repair_pr.py --pr 123 --submit-repair ./tmp/pr_123_fix_results.json --ai-model your-model-name
```

## 修复类型

1. **代码修复**: 提供具体的代码修改建议
2. **回复说明**: 仅需要回复解释
3. **回退文件**: 建议回退整个文件
4. **删除行**: 建议删除特定行

## 输入格式

```json
[
  {
    "comment_id": 12345,
    "file_path": "src/main.py",
    "line_number": 10,
    "has_fix": true,
    "fix_description": "修复说明",
    "original_code": "old code",
    "fixed_code": "new code",
    "reason": "修复原因"
  }
]
```
