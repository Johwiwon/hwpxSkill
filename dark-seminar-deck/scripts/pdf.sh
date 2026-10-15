#!/bin/bash
# usage: pdf.sh <캡처 폴더> <출력.pdf> [문서 제목]
#   문서 제목을 안 주면 shots.sh 가 남긴 덱 제목(<캡처 폴더>/_title.txt)을 쓴다.
#   캡처한 PNG를 한 장씩 담은 "이미지 PDF"를 만든다.
#   HTML을 바로 PDF로 인쇄하면 그라데이션 글자(background-clip:text) 둘레에 가는 사각선이 생겨서 이 방식을 쓴다.
set -e
. "$(dirname "$0")/_env.sh"
SH="${1:?캡처 폴더}"; OUTPDF="${2:?출력 PDF}"
N=$(ls "$SH"/s*.png | wc -l)
[ "$N" -gt 0 ] || { echo "$SH 에 s*.png 가 없습니다." >&2; exit 1; }
TITLE="${3:-$(cat "$SH/_title.txt" 2>/dev/null)}"
[ -n "$TITLE" ] || echo "주의: 문서 제목이 없어 PDF 제목이 파일 이름(_pages.html)으로 나옵니다. 세 번째 인자로 제목을 주세요." >&2
TITLE_HTML=$(python3 -c "import html,sys;print(html.escape(sys.argv[1]))" "$TITLE")
PAGE="$SH/_pages.html"
{ echo "<!doctype html><meta charset=\"utf-8\"><title>$TITLE_HTML</title>"
  echo '<style>@page{size:1920px 1080px;margin:0}html,body{margin:0;background:#090E1B}img{display:block;width:1920px;height:1080px;break-after:page}img:last-child{break-after:auto}</style>'
  for i in $(seq 1 $N); do echo "<img src=\"s$i.png\">"; done; } > "$PAGE"
mkdir -p "$(dirname "$OUTPDF")"; touch "$OUTPDF"
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=8000 \
  --print-to-pdf="$(to_chrome_path "$OUTPDF")" "$(to_file_url "$PAGE")" >/dev/null 2>&1 </dev/null
rm -f "$PAGE"
PAGES=$(python3 -c "import re,sys;d=open(sys.argv[1],'rb').read();print(len(re.findall(rb'/Type\s*/Page[^s]',d)))" "$OUTPDF")
if [ "$PAGES" = "$N" ]; then echo "PDF: $OUTPDF (${PAGES}쪽, 캡처 수와 같음)"; else echo "확인 필요: PDF ${PAGES}쪽, 캡처 ${N}장 → $OUTPDF" >&2; exit 2; fi
