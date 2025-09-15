SHELL := /usr/bin/env bash
install: ; @bash install.sh
start: ; @bash start.sh
baseline: ; @bash integrity_checker.sh
reason: ; @DATAROOT="$$HOME" LOGICROOT="$$HOME/autonomous_logic" bash autonomous_reasoner.sh --json
snapshots: ; @bash web_snapshot.sh web_sources.txt || true; @SNAPDIR="$$HOME/web_snapshots" OUTDIR="$$HOME/web_diffs" bash html_diff_report.sh || true
quarantine-on: ; @bash network_quarantine.sh hard-on || true
quarantine-off: ; @bash network_quarantine.sh hard-off || true

reason-home: ; @DATAROOT="$$PWD/external_user_drop/user_home_zip" LOGICROOT="$$HOME/autonomous_logic" bash autonomous_reasoner.sh --json
