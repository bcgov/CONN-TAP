#!/usr/bin/env bash

set -euo pipefail

VERSION="8.30.0"
ARCHIVE="gitleaks_${VERSION}_linux_x64.tar.gz"
URL="https://github.com/gitleaks/gitleaks/releases/download/v${VERSION}/${ARCHIVE}"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

curl -sSL "${URL}" -o "${tmp_dir}/${ARCHIVE}"
tar -xzf "${tmp_dir}/${ARCHIVE}" -C "${tmp_dir}"
install -m 0755 "${tmp_dir}/gitleaks" ./gitleaks
