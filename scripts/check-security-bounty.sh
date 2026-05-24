#!/usr/bin/env bash
set -euo pipefail

contract="${1:-contracts/security_bounty.py}"
version="${GENVM_VERSION:-v0.2.16}"
linter="${GENVM_LINT:-genvm-lint}"

if ! command -v "$linter" >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/genvm-lint" ]; then
    linter="$HOME/.local/bin/genvm-lint"
  else
    echo "genvm-lint not found on PATH or at \$HOME/.local/bin/genvm-lint" >&2
    exit 1
  fi
fi

"$linter" download --version "$version" >/dev/null

sdk_root="$(
  GENVM_VERSION="$version" python3 - <<'PY'
import os
from genvm_linter.validate.artifacts import (
    download_artifacts,
    extract_runner,
    find_latest_runner,
    parse_runner_manifest,
)

version = os.environ["GENVM_VERSION"]
tarball = download_artifacts(version)
runner_hash = find_latest_runner(tarball, "py-genlayer")
runner_path = extract_runner(tarball, "py-genlayer", runner_hash)
std_hash = parse_runner_manifest(runner_path)["py-lib-genlayer-std"]
std_path = extract_runner(tarball, "py-lib-genlayer-std", std_hash)
print(std_path)
PY
)"

mkdir -p .genvmroot/runners/py-lib-genlayer-std
ln -sfn "$sdk_root" .genvmroot/runners/py-lib-genlayer-std/src

GENVMROOT="$PWD/.genvmroot" "$linter" check "$contract"
python3 -m pytest test/direct/test_security_bounty.py -q -s
