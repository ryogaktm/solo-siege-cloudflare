#!/bin/sh
# 全テストを順に実行する（1つでも失敗したら終了コード1）。使い方: sh tests/run_all.sh
cd "$(dirname "$0")/.." || exit 1
rc=0
for t in tests/rules.py tests/card_conservation.py; do echo "== $t"; python3 "$t" || rc=1; done
exit $rc
