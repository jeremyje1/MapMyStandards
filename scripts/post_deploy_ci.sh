#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:-${MMS_BASE:-https://platform.mapmystandards.ai}}

echo "[CI] Hitting ${BASE_URL}/standards"
curl -fsSL "${BASE_URL}/standards" | grep -i '<title' >/dev/null

echo "[CI] Hitting ${BASE_URL}/evidence-mapping"
curl -fsSL "${BASE_URL}/evidence-mapping" | grep -i '<title' >/dev/null

echo "[CI] Hitting ${BASE_URL}/reports"
curl -fsSL "${BASE_URL}/reports" | grep -i '<title' >/dev/null

echo "[CI] Hitting ${BASE_URL}/org-chart"
curl -fsSL "${BASE_URL}/org-chart" | grep -i '<title' >/dev/null

echo "[CI] All pages responded with HTML titles ✅"