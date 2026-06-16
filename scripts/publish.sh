#!/usr/bin/env bash
# Build and publish atomgit-sdk from a clean, isolated venv.
#
# Why isolated: a project venv created with --system-site-packages, or a shell
# carrying a project PYTHONPATH, can let a stale system requests_toolbelt
# shadow the one twine needs and crash with:
#   ImportError: cannot import name 'appengine' from 'urllib3.contrib'
# This script builds a throwaway venv and strips PYTHONPATH so the build and
# upload always run against pristine dependencies.
#
# Usage:
#   scripts/publish.sh check       # build + twine check only (no upload)
#   scripts/publish.sh testpypi    # build + upload to TestPyPI
#   scripts/publish.sh pypi        # build + upload to PyPI (irreversible!)
#
# Credentials are read from ~/.pypirc, which must define [testpypi] and [pypi]
# sections with username=__token__ and password=pypi-<api_token>.
set -euo pipefail

ACTION="${1:-check}"
VENV="${PUBLISH_VENV:-.venv-publish}"

case "$ACTION" in
  check|testpypi|pypi) ;;
  *)
    echo "usage: $0 [check|testpypi|pypi]" >&2
    exit 1
    ;;
esac

# Resolve the repo root regardless of where the script is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# 1. Prepare an isolated venv (reused across runs; PYTHONPATH is stripped on
#    every invocation so host pollution can never leak in).
if [ ! -d "$VENV" ]; then
  echo "==> creating isolated publish venv at $VENV"
  python3 -m venv "$VENV"
fi
echo "==> ensuring build tools (PYTHONPATH stripped)"
env -u PYTHONPATH "$VENV/bin/pip" install --quiet --upgrade build twine

# 2. Clean build + metadata check.
echo "==> building sdist + wheel"
rm -rf dist build src/*.egg-info src/atomgit_sdk.egg-info
env -u PYTHONPATH "$VENV/bin/python" -m build
env -u PYTHONPATH "$VENV/bin/python" -m twine check dist/*

if [ "$ACTION" = "check" ]; then
  echo "==> build OK (artifacts in dist/). Run with 'testpypi' or 'pypi' to upload."
  exit 0
fi

# 3. Upload. twine reads ~/.pypirc credentials for the given repository.
echo "==> uploading to $ACTION (reading ~/.pypirc)"
env -u PYTHONPATH "$VENV/bin/python" -m twine upload --repository "$ACTION" dist/*
echo "==> uploaded to $ACTION"
