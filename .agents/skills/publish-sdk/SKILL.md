---
name: publish-sdk
description: "发布 atomgit-sdk 到 PyPI 的工作流。当用户需要\"发布到pypi\"、\"publish\"、\"上传新版本\"、\"发版\"、\"build and upload\"、\"twine upload\"时使用。封装隔离 venv 构建与上传，绕过宿主环境污染。"
license: MIT
---

# Publish atomgit-sdk to PyPI

构建并发布 atomgit-sdk 到 PyPI / TestPyPI。

## 为什么必须用隔离 venv

宿主环境的 venv 如果是 `--system-site-packages` 创建的，或 shell 里带有项目 `PYTHONPATH`，会让**系统旧版 `requests_toolbelt`** 被优先加载，与新版 `urllib3` 不兼容，直接崩溃：

```
ImportError: cannot import name 'appengine' from 'urllib3.contrib'
```

[`scripts/publish.sh`](../../scripts/publish.sh) 会自动创建一个隔离的干净 venv，并在每次调用时清除 `PYTHONPATH`，从根上绕开此问题。**不要**直接在项目 venv 里跑 `twine`。

## 工作流

```bash
# 1. 仅构建 + twine check（不上传）
scripts/publish.sh check

# 2. 先发 TestPyPI 验证安装（强烈推荐）
scripts/publish.sh testpypi

# 3. 正式发 PyPI（不可逆！）
scripts/publish.sh pypi
```

## 凭据配置

twine 从 `~/.pypirc` 读取凭据，需配置：

```ini
[distutils]
index-servers = pypi testpypi

[pypi]
username = __token__
password = pypi-<正式PyPI_token>

[testpypi]
username = __token__
password = pypi-<TestPyPI_token>
```

token 在 pypi.org / test.pypi.org 的 **Account settings → API tokens** 生成，scope 选 "Entire account"。

## TestPyPI 验证安装

TestPyPI 不含全部第三方依赖，安装时需从正式 PyPI 补 `requests`/`pydantic`：

```bash
python3 -m venv /tmp/verify
/tmp/verify/bin/pip install -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ atomgit-sdk
/tmp/verify/bin/python -c "import atomgit_sdk; print(atomgit_sdk.__version__)"
```

## 版本迭代流程

发新版本：

1. 改 `pyproject.toml` 的 `version`（语义化版本）
2. 补 `CHANGELOG.md` 的对应版本段
3. 提交并打 tag（可选）
4. `scripts/publish.sh pypi`

## 重要约束

- PyPI 版本号一经上传**不可删除、不可覆盖同名**（只能 yank 或发更高版本号）。
- 首次发布或重大变更**务必先 `testpypi` 验证**安装与导入。
- 环境变量方式传 token（`TWINE_USERNAME=__token__ TWINE_PASSWORD=...`）比写进 `~/.pypirc` 更安全，不落盘。
