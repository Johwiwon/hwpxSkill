#!/bin/bash
# usage: new_deck.sh <덱 폴더>
#   <덱 폴더>/index.html(빌드 결과), fonts/, _build/src.html(원본), _build/build.mjs 를 만든다.
#   아이콘 패키지(lucide-static)는 ~/.cache/dark-seminar-deck 에 한 번만 설치한다.
set -e
. "$(dirname "$0")/_env.sh"
DECK="${1:?덱 폴더를 지정하세요}"
if [ -e "$DECK/_build/src.html" ]; then echo "이미 덱이 있습니다: $DECK/_build/src.html (덮어쓰지 않음)" >&2; exit 1; fi
mkdir -p "$DECK"
cp -r "$SKILL_DIR/assets/template/." "$DECK/"
if [ ! -d "$TOOLS/node_modules/lucide-static/icons" ]; then
  mkdir -p "$TOOLS"; (cd "$TOOLS" && { [ -f package.json ] || npm init -y >/dev/null; } && npm install -q lucide-static >/dev/null 2>&1)
fi
node "$DECK/_build/build.mjs"
echo "덱을 만들었습니다: $DECK  (원본은 $DECK/_build/src.html)"
