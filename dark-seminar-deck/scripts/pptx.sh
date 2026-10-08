#!/bin/bash
# usage: pptx.sh <캡처 폴더> <출력.pptx> [notes.json] [제목] [작성자]
#   슬라이드 PNG를 한 장씩 꽉 채운 PPTX(PDF와 같은 화면)를 만든다. 선택 사항.
#   notes.json: ["1쪽 노트", "2쪽 노트", ...]  — 줄바꿈은 \n 으로. 발표자 노트로 들어간다.
set -e
. "$(dirname "$0")/_env.sh"
SH="${1:?캡처 폴더}"; OUT="${2:?출력 PPTX}"
[ -d "$TOOLS/node_modules/pptxgenjs" ] || { mkdir -p "$TOOLS"; (cd "$TOOLS" && { [ -f package.json ] || npm init -y >/dev/null; } && npm install -q pptxgenjs >/dev/null 2>&1); }
TMP="$OUT.tmp.pptx"
NODE_PATH="$TOOLS/node_modules" node "$SKILL_DIR/scripts/pptx.js" "$SH" "$TMP" "${3:-}" "${4:-발표자료}" "${5:-}"
python3 "$SKILL_DIR/scripts/fixnotes.py" "$TMP" "$OUT" && rm -f "$TMP"
echo "PPTX: $OUT"
