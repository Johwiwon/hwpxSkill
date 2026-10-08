#!/bin/bash
# 공통 환경: 크롬 위치, 파일 경로 → 크롬이 읽는 URL/경로 변환, 도구 캐시 위치
# source 해서 쓴다:  . "$(dirname "$0")/_env.sh"

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="${DECK_TOOLS:-$HOME/.cache/dark-seminar-deck}"   # npm 패키지 캐시 (임시 폴더가 비워져도 남는 곳)

# 크롬 찾기: CHROME 환경변수 > WSL의 윈도 크롬 > 리눅스/맥 크롬
if [ -z "$CHROME" ]; then
  for c in "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" \
           "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
           "$(command -v google-chrome 2>/dev/null)" "$(command -v google-chrome-stable 2>/dev/null)" \
           "$(command -v chromium 2>/dev/null)" "$(command -v chromium-browser 2>/dev/null)" \
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
    [ -n "$c" ] && [ -x "$c" ] && { CHROME="$c"; break; }
  done
fi
[ -z "$CHROME" ] && { echo "크롬을 찾지 못했습니다. CHROME=<경로> 로 지정하세요." >&2; exit 1; }

# 윈도 크롬(WSL)이면 경로를 윈도 형식으로 바꿔 넘겨야 한다
case "$CHROME" in *.exe) WINCHROME=1 ;; *) WINCHROME=0 ;; esac
to_chrome_path() {   # 파일/폴더 경로 → 크롬 인자용 경로
  if [ "$WINCHROME" = 1 ]; then wslpath -w "$1"; else readlink -f "$1"; fi
}
to_file_url() {      # 파일 경로 → file:// URL
  if [ "$WINCHROME" = 1 ]; then echo "file:///$(wslpath -w "$1" | sed 's#\\#/#g')"; else echo "file://$(readlink -f "$1")"; fi
}
