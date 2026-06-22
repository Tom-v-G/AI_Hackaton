#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_DIR="/home/tom/Projects/AI_Hackaton/artifacts/e2e/exploratory/de_lekbak/2026-06-22T000000Z/01-viral-dashboard"
APP_URL="http://127.0.0.1:18082"

log() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$ARTIFACT_DIR/scenario.log"
}

run_browser() {
  log "npx --yes agent-browser $*"
  npx --yes agent-browser "$@" 2>&1 | tee -a "$ARTIFACT_DIR/agent-browser.log"
}

log "Open de_lekbak dashboard"
run_browser open "$APP_URL"
run_browser wait --load networkidle
run_browser snapshot -i
run_browser screenshot --full "$ARTIFACT_DIR/page-assertion.png"

log "Click manual refresh"
run_browser find role button click --name "Manual refresh"
run_browser wait --load networkidle
run_browser snapshot -i
run_browser screenshot --full "$ARTIFACT_DIR/after-refresh.png"

log "Capture visible page text"
run_browser get text body
