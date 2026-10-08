#!/bin/bash
# usage: shots.sh <덱 폴더> <출력 폴더> [슬라이드 번호...]     (번호를 안 주면 전체)
#   SCALE=1.5 (기본) → 2880x1620 PNG. 화면 확인만 할 때는 SCALE=1 로 빠르게.
#   결과: <출력 폴더>/s1.png, s2.png ...  (번호를 안 주면 기존 s*.png 를 지우고 전체를 다시 찍는다)
set -e
. "$(dirname "$0")/_env.sh"
DECK="${1:?덱 폴더}"; OUT="${2:?출력 폴더}"; shift 2
HTML="$DECK/index.html"
[ -f "$HTML" ] || { echo "$HTML 이 없습니다. 먼저 build.mjs 를 실행하세요." >&2; exit 1; }
TOTAL=$(grep -c '<section class="slide' "$HTML")
mkdir -p "$OUT"
# 전체 캡처(번호 미지정)면 이전 덱의 sN.png 가 남지 않게 먼저 지운다
[ $# -eq 0 ] && rm -f "$OUT"/s*.png
URL=$(to_file_url "$HTML")
OUTP=$(to_chrome_path "$OUT")
SEP=/; [ "$WINCHROME" = 1 ] && SEP='\'
for n in ${@:-$(seq 1 $TOTAL)}; do
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1920,1080 \
    --force-device-scale-factor=${SCALE:-1.5} --virtual-time-budget=4000 \
    --screenshot="$OUTP${SEP}s$n.png" "$URL?s=$n" >/dev/null 2>&1 </dev/null &
  (( n % 6 == 0 )) && wait
done
wait
echo "캡처: $OUT ($(ls "$OUT"/s*.png | wc -l)장)"
