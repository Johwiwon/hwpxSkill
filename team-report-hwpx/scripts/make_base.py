#!/usr/bin/env python3
"""팀장 최종본에서 본문을 비운 기본 양식(assets/base.hwpx)을 만든다.

    python3 make_base.py [reference.hwpx] [out.hwpx]

기준 보고서 원본(로컬 전용)이 있을 때만 쓴다. 생성·점검에는 필요 없다.

남기는 것: header.xml(글꼴·글자모양·문단모양·테두리 전체), 용지·여백·쪽번호,
제목 상자(3행 표), 작성일·부서 줄. 본문 문단과 그림(BinData)은 지운다.
그림 배경을 쓰던 테두리(imgBrush)는 그림만 떼고 점선 테두리로 남긴다.
제목·작성일 문구는 자리표시(TITLE_MARK, DATE_MARK)로, 미리보기 그림은 흰 그림으로
바꿔 원본 보고서 내용이 base 에 남지 않게 한다.
"""
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_report import TITLE_MARK, DATE_MARK, blank_png  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else SKILL / 'assets/reference/final_monitoring.hwpx'
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else SKILL / 'assets/base.hwpx'


def top_level_paragraphs(sec: str):
    """<hs:sec> 바로 아래 <hp:p> 들의 (start, end) 위치."""
    body_start = sec.index('>', sec.index('<hs:sec')) + 1
    spans, depth, i = [], 0, body_start
    tag = re.compile(r'<(/?)hp:p[ >/]')
    start = None
    for m in tag.finditer(sec, body_start):
        if m.group(1) == '':
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                end = sec.index('>', m.start()) + 1
                spans.append((start, end))
    return body_start, spans


def main():
    zin = zipfile.ZipFile(SRC)
    files = {n: zin.read(n) for n in zin.namelist()}

    header = files['Contents/header.xml'].decode('utf-8')
    header = re.sub(r'<hc:fillBrush><hc:imgBrush.*?</hc:imgBrush></hc:fillBrush>', '', header, flags=re.S)
    files['Contents/header.xml'] = header.encode('utf-8')

    sec = files['Contents/section0.xml'].decode('utf-8')
    body_start, spans = top_level_paragraphs(sec)
    keep_end = spans[1][1]  # 0: secPr+제목 상자, 1: 작성일 줄
    sec = sec[:keep_end] + '</hs:sec>'
    sec = re.sub(r'<hp:linesegarray>.*?</hp:linesegarray>', '', sec, flags=re.S)
    # 제목 상자 가운데 행의 제목, 작성일 줄을 자리표시로 바꾼다.
    sec = re.sub(r'(<hp:run charPrIDRef="\d+"><hp:t>)[^<]*(</hp:t></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="0" rowAddr="1"/>)',
                 lambda m: m.group(1) + TITLE_MARK + m.group(2), sec, count=1)
    sec = re.sub(r'<hp:t>&lt; [^<]*&gt;</hp:t>', '<hp:t>' + DATE_MARK + '</hp:t>', sec, count=1)
    assert TITLE_MARK in sec and DATE_MARK in sec, '제목/작성일 자리표시 치환 실패'
    files['Contents/section0.xml'] = sec.encode('utf-8')
    files['Preview/PrvImage.png'] = blank_png()

    for n in [n for n in files if n.startswith('BinData/')]:
        del files[n]
    hpf = files['Contents/content.hpf'].decode('utf-8')
    hpf = re.sub(r'<opf:item id="image\d+"[^>]*/>', '', hpf)
    hpf = re.sub(r'(<opf:meta name="lastsaveby" content="text">)[^<]*', r'\1', hpf)
    hpf = re.sub(r'<opf:title>[^<]*</opf:title>', '<opf:title></opf:title>', hpf)
    files['Contents/content.hpf'] = hpf.encode('utf-8')
    files['Preview/PrvText.txt'] = b''

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), files.pop('mimetype'), compress_type=zipfile.ZIP_STORED)
        for n, data in files.items():
            z.writestr(n, data, compress_type=zipfile.ZIP_DEFLATED)
    print(f'base written: {OUT} ({OUT.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
