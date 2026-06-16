---
name: atomgit-collaboration
description: "AtomGit 协作路由示例。当用户在 AtomGit 仓库中提到\"PR\"、\"merge request\"、\"Issue\"、\"review\"、\"comment\"、\"discussion\"等泛化协作请求，但没有明确动作类型时调用。此 skill 不直接执行业务动作，而是先识别用户真实意图，再路由到 pr、issue、pr-review 或 review-resolution。"
license: MIT
---

# AtomGit Collaboration Router

这是一个**薄路由 skill**示例，只负责识别 AtomGit 协作语义并分流到更具体的 skill。

当用户提到 PR / merge request / Issue / review / comments / discussions，但**没有明确动作类型**时，优先触发本 skill 做意图识别与路由。

## 适用场景

以下请求优先触发本 skill：

- “帮我看看 PR #123”
- “这个 merge request 你处理一下”
- “AtomGit 上这个评论怎么回”
- “帮我跟进一下 #456”

以下请求**不必**经过本 skill，可直接进入更具体的 skill：

- 明确说“创建 PR / 更新 PR 描述” → `pr`
- 明确说“创建 Issue / 关闭 Issue” → `issue`
- 明确说“代码审查 / review PR” → `pr-review`
- 明确说“修复 review comments / 回复评论” → `review-resolution`

## 路由规则

收到泛化协作请求时，Agent 按以下顺序判断：

1. **先判断资源类型**
   - 提到 PR / merge request / review / comment / discussion → 进入 PR 协作域
   - 提到 Issue / bug / feature request / task → 进入 Issue 协作域

2. **再判断动作类型**
   - 创建、读取详情、更新标题/描述 → `pr` 或 `issue`
   - 审查代码质量、检查逻辑问题 → `pr-review`
   - 回复评论、应用修复、处理 unresolved comments → `review-resolution`

3. **如果动作仍不明确**
   - PR 协作域如果表达里带有“看看 / 检查 / 审查 / review / 评估”，默认先路由到 `pr-review`
   - PR 协作域如果目标更像创建、更新描述，再路由到 `pr`
   - Issue 协作域默认先路由到 `issue`

## 路由对照表

| 用户表达 | 目标 skill |
| :--- | :--- |
| “帮我看看 PR #123” | `pr-review` |
| “帮我更新这个 PR 描述” | `pr` |
| “帮我看下 Issue #456” | `issue` |
| “帮我审查这个 PR” | `pr-review` |
| “修复一下 review comments” | `review-resolution` |
