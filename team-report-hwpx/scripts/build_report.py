#!/usr/bin/env python3
"""팀장 최종본 양식으로 보고서 HWPX를 만든다.

    python3 build_report.py 입력.txt 출력.hwpx [--no-fit] [--quiet]

입력 문법은 references/input-format.md 참고. 요약:

    제목: 사내 문서 검색 기능 개선 결과
    날짜: ’26. 9. 22            (생략 시 오늘)
    부서: 지능화번역팀            (생략 시 지능화번역팀)

    □ 개요
    ㅇ 본문 …
    * 부연 설명(함초롬돋움 13pt)
    - 세부 항목
    < 표 제목 >
    [표 글자=12 너비=20,30,50 정렬=c,l,c]
    | 구분 | 내용 | 비고 |
    |---|---|---|
    | A | ^ 는 위 칸과 병합, < 는 왼쪽 칸과 병합 | |
    [그림 화면.png 너비=100]
    - 이하 여백 -
    [붙임] 붙임 제목
"""
import argparse
import datetime
import html
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hwpx_style import HeaderStyles  # noqa: E402
import layout  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
BASE = SKILL / 'assets' / 'base.hwpx'

# ---------------------------------------------------------------- 양식 상수
F_HEAD = 'HY헤드라인M'
F_BODY = '휴먼명조'
F_SANS = '함초롬돋움'
F_SPACER = '휴먼명조'

SIZE_SECTION = 16       # □
SIZE_BODY = 15          # ㅇ, -
SIZE_NOTE = 13          # *, **, < 캡션 >
SIZE_TABLE = 12         # 표 안 (조밀한 표 11)
SIZE_DATE = 13
SIZE_ATTACH = 15        # 붙임 제목

CAPTION_SPACING = -7    # 팀장 최종본의 캡션 자간
TABLE_WIDTH = 45350     # ㅇ 아래 표: 'ㅇ ' 뒤 본문 시작선에 왼쪽을 맞춘 폭
TABLE_WIDTH_FULL = 48180
FIGURE_WIDTH = 45360
HEAD_FILL = '#DAEEF3'
HIGHLIGHT_FILL = '#FFF7CC'

# 머리 기호와 내어쓰기(HWPUNIT). 값은 최종본에서 잰 것.
PREFIX = {
    'o': (' ㅇ ', SIZE_BODY, -2980),
    'dash': ('  - ', SIZE_BODY, -2952),
    'note1': ('  * ', SIZE_NOTE, -2986),
    'note2': ('   * ', SIZE_NOTE, -3149),
    'note1b': (' ** ', SIZE_NOTE, -2986),
    'note2b': ('  ** ', SIZE_NOTE, -3149),
}

# 문단 사이 빈 줄(pt). 팀장 최종본 기준값.
GAP = dict(after_date=10, before_section=10, after_section=5, before_o=3, child=1,
           around_caption=1, around_table=3, after_attach=5, before_end=5)

# base.hwpx 의 제목·작성일 자리표시(make_base.py 가 넣는다)
TITLE_MARK = '{{TITLE}}'
DATE_MARK = '{{DATE}}'

MEDIA = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.bmp': 'image/bmp'}


# ------------------------------------------------------------------ 입력 파싱
def parse(text):
    meta, items = {}, []
    lines = text.splitlines()
    i = 0
    pending_table_opts = None
    while i < len(lines):
        raw = lines[i].rstrip()
        s = raw.strip()
        i += 1
        if not s or s.startswith('//'):
            continue
        m = re.match(r'^(제목|날짜|부서|표머리색|간격)\s*[:：]\s*(.*)$', s)
        if m and not items:
            meta[m.group(1)] = m.group(2).strip()
            continue
        if s.startswith('□'):
            items.append(dict(t='sec', text=s.lstrip('□').strip()))
        elif re.match(r'^\[붙임\]', s):
            items.append(dict(t='attach', text=s[len('[붙임]'):].strip()))
        elif re.match(r'^-\s*이하\s*여백\s*-$', s):
            items.append(dict(t='end'))
        elif re.match(r'^(ㅇ|o|○)\s', s):
            items.append(dict(t='o', text=re.sub(r'^(ㅇ|o|○)\s+', '', s)))
        elif s.startswith('**') and not s.startswith('***') and re.match(r'^\*\*\s', s):
            items.append(dict(t='note', level=2, text=s[2:].strip()))
        elif re.match(r'^\*\s', s):
            items.append(dict(t='note', level=1, text=s[1:].strip()))
        elif re.match(r'^-\s', s):
            items.append(dict(t='dash', text=s[1:].strip()))
        elif re.match(r'^<.+>$', s) and not s.startswith('<br'):
            items.append(dict(t='caption', text=s))
        elif s.startswith('[표'):
            pending_table_opts = parse_opts(s[2:-1] if s.endswith(']') else s[2:])
        elif s.startswith('[그림'):
            body = s[3:-1] if s.endswith(']') else s[3:]
            opts = parse_opts(body)
            items.append(dict(t='figure', path=opts.pop('_args', [''])[0], opts=opts))
        elif s.startswith('|'):
            rows = [s]
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip())
                i += 1
            items.append(dict(t='table', rows=rows, opts=pending_table_opts or {}))
            pending_table_opts = None
        else:
            # 기호 없는 줄은 앞 항목의 이어지는 문장으로 본다.
            if items and items[-1]['t'] in ('o', 'dash', 'note'):
                items[-1]['text'] += ' ' + s
            else:
                raise SystemExit(f'해석할 수 없는 줄: {s!r} (□ ㅇ - * < > | [표] [그림] [붙임] 중 하나로 시작해야 함)')
    return meta, items


def parse_opts(s):
    opts, args = {}, []
    for tok in re.findall(r'(\S+?=(?:"[^"]*"|\S+)|"[^"]*"|\S+)', s.strip()):
        if '=' in tok and not tok.startswith('"'):
            k, v = tok.split('=', 1)
            opts[k] = v.strip('"')
        else:
            args.append(tok.strip('"'))
    if args:
        opts['_args'] = [' '.join(args)]
    return opts


COLORS = {'빨강': '#FF0000', '파랑': '#0000FF'}


def inline_runs(text):
    """인라인 표시를 [(text, bold, small, color)] 로 나눈다.

    **굵게**   {{작게(2pt 작게)}}   {빨강:강조}   {파랑:수정}   — 서로 겹쳐 써도 된다.
    """
    out, bold, small, colors = [], False, False, []
    pos = 0
    for m in re.finditer(r'\*\*|\{\{|\}\}|\{(빨강|파랑):|\}', text):
        if m.start() > pos:
            out.append((text[pos:m.start()], bold, small, colors[-1] if colors else '#000000'))
        tok = m.group(0)
        if tok == '**':
            bold = not bold
        elif tok == '{{':
            small = True
        elif tok == '}}':
            small = False
        elif tok == '}':
            if colors:
                colors.pop()
            else:
                out.append(('}', bold, small, '#000000'))
        else:
            colors.append(COLORS[m.group(1)])
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], bold, small, colors[-1] if colors else '#000000'))
    return [r for r in out if r[0]]


def strip_marks(text):
    return ''.join(t for t, *_ in inline_runs(text))


# ------------------------------------------------------------------ 그림 크기
def image_size(data: bytes):
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', data[16:24])
    if data[:2] == b'\xff\xd8':
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack('>HH', data[i + 5:i + 9])
                return w, h
            seg = struct.unpack('>H', data[i + 2:i + 4])[0]
            i += 2 + seg
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return struct.unpack('<HH', data[6:10])
    if data[:2] == b'BM':
        w, h = struct.unpack('<ii', data[18:26])
        return w, abs(h)
    raise ValueError('그림 크기를 읽을 수 없음 (png/jpg/gif/bmp 만 지원)')


def blank_png(w=724, h=1024):
    raw = b''.join(b'\x00' + b'\xff' * (w * 3) for _ in range(h))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


# ------------------------------------------------------------------ 생성기
class Builder:
    def __init__(self, meta, src_dir: Path, fit=True):
        self.meta = meta
        self.src_dir = src_dir
        self.fit = fit
        z = zipfile.ZipFile(BASE)
        self.files = {n: z.read(n) for n in z.namelist()}
        self.st = HeaderStyles(self.files['Contents/header.xml'].decode('utf-8'))
        self.sec_xml = self.files['Contents/section0.xml'].decode('utf-8')
        self.body = []
        self.pid = 1000
        self.obj_id = 1500000000
        self.images = []
        self.report = []
        self.plain = []
        self.head_fill = meta.get('표머리색', HEAD_FILL)
        for k, v in re.findall(r'(\w+)\s*=\s*(\d+)', meta.get('간격', '')):
            key = {'절': 'before_section', '절후': 'after_section', 'ㅇ': 'before_o', '항목': 'child',
                   '표': 'around_table', '캡션': 'around_caption'}.get(k, k)
            GAP[key] = int(v)

    # ---------------------------------------------------------- 기본 요소
    def next_pid(self):
        self.pid += 1
        return self.pid

    def next_obj(self):
        self.obj_id += 1
        return self.obj_id

    @staticmethod
    def esc(t):
        return html.escape(t, quote=False)

    def run(self, cid, text=None):
        if text is None:
            return f'<hp:run charPrIDRef="{cid}"/>'
        return f'<hp:run charPrIDRef="{cid}"><hp:t>{self.esc(text)}</hp:t></hp:run>'

    def para(self, ppid, runs_xml, page_break=False):
        return (f'<hp:p id="{self.next_pid()}" paraPrIDRef="{ppid}" styleIDRef="0" '
                f'pageBreak="{1 if page_break else 0}" columnBreak="0" merged="0">{runs_xml}</hp:p>')

    def spacer(self, pt):
        if pt <= 0:
            return
        self.body.append(self.para(self.st.para('JUSTIFY', 0), self.run(self.st.char(F_SPACER, pt))))

    # ---------------------------------------------------------- 본문 문단
    def text_para(self, kind, text, align='JUSTIFY'):
        prefix, size, intent = PREFIX[kind]
        face = F_BODY if kind in ('o', 'dash') else F_SANS
        label = None
        if kind == 'o':
            m = re.match(r'^(\([^)]+\))\s*(.*)$', text)
            if m:
                label, text = m.group(1), m.group(2)
        pieces = []
        if label:
            pieces.append((label, True, False, '#000000'))
            pieces.append((' ', False, False, '#000000'))
        pieces += inline_runs(text)
        body_runs = [(t, size - 2 if small else size, 100) for t, b, small, _ in pieces]
        sp, n, fill, note = 0, 1, 1.0, ''
        if self.fit:
            sp, n, fill, note = layout.fit_paragraph((prefix, size, 0, 100), body_runs, intent, face=face)
        runs = [self.run(self.st.char(face, size, 0), prefix)]
        for t, bold, small, color in pieces:
            runs.append(self.run(self.st.char(face, size - 2 if small else size, sp, bold=bold, color=color), t))
        self.body.append(self.para(self.st.para(align, intent), ''.join(runs)))
        plain = prefix + (label + ' ' if label else '') + strip_marks(text)
        self.plain.append(plain)
        if note:
            self.report.append(f'{"맞춤" if sp else "확인"}  {note}  | {plain.strip()[:40]}')

    def section(self, title):
        self.body.append(self.para(self.st.para('JUSTIFY', 0), self.run(self.st.char(F_HEAD, SIZE_SECTION), f'□ {title}')))
        self.plain.append(f'□ {title}')

    def caption(self, text):
        inner = text.strip()[1:-1].strip()
        self.body.append(self.para(self.st.para('CENTER', 0),
                                   self.run(self.st.char(F_SANS, SIZE_NOTE, CAPTION_SPACING), f'< {inner} >')))
        self.plain.append(f'< {inner} >')

    def end_mark(self):
        self.body.append(self.para(self.st.para('CENTER', 0), self.run(self.st.char(F_BODY, SIZE_BODY), '- 이하 여백 -')))

    # ------------------------------------------------------------- 그림 등록
    def add_image(self, rel):
        path = (self.src_dir / rel) if not Path(rel).is_absolute() else Path(rel)
        data = path.read_bytes()
        w, h = image_size(data)
        ext = path.suffix.lower()
        if ext not in MEDIA:
            raise SystemExit(f'지원하지 않는 그림 형식: {path}')
        n = len(self.images) + 1
        bin_id = f'image{n}'
        self.images.append((bin_id, f'BinData/{bin_id}{ext}', MEDIA[ext], data))
        return bin_id, w, h

    # ------------------------------------------------------------------ 표
    def table(self, rows, opts, full_width):
        size = float(opts.get('글자', SIZE_TABLE))
        width = TABLE_WIDTH_FULL if full_width or opts.get('폭') == '전체' else TABLE_WIDTH
        if opts.get('폭', '').isdigit():
            width = int(opts['폭'])
        grid, head_rows, highlight = [], 0, set()
        for r in rows:
            if re.match(r'^\|\s*:?-{3,}', r):
                head_rows = len(grid)
                continue
            hl = r.startswith('|!')
            body = r[2:] if hl else r[1:]
            if body.endswith('|'):
                body = body[:-1]
            cells = [c.strip() for c in body.split('|')]
            if hl:
                highlight.add(len(grid))
            grid.append(cells)
        if head_rows == 0:
            head_rows = 1
        ncol = max(len(r) for r in grid)
        for r in grid:
            r += [''] * (ncol - len(r))
        nrow = len(grid)
        aligns = (opts.get('정렬', '') or '').split(',')
        aligns = [(aligns[c].strip().lower() if c < len(aligns) and aligns[c].strip() else 'c') for c in range(ncol)]

        # 병합 계산: '^' 위, '<' 왼쪽
        owner = [[(r, c) for c in range(ncol)] for r in range(nrow)]
        for r in range(nrow):
            for c in range(ncol):
                v = grid[r][c]
                if v == '^' and r > 0:
                    owner[r][c] = owner[r - 1][c]
                elif v == '<' and c > 0:
                    owner[r][c] = owner[r][c - 1]
        span = {}
        for r in range(nrow):
            for c in range(ncol):
                o = owner[r][c]
                r0, c0, r1, c1 = span.get(o, (o[0], o[1], o[0], o[1]))
                span[o] = (r0, c0, max(r1, r), max(c1, c))
        for o, (r0, c0, r1, c1) in span.items():
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if owner[r][c] != o:
                        raise SystemExit(f'표 병합이 직사각형이 아님: {r + 1}행 {c + 1}열 근처의 ^ / < 를 확인하세요\n  '
                                         + ' | '.join(grid[r]))

        # 열 너비
        if '너비' in opts:
            ratios = [float(x) for x in opts['너비'].split(',')]
            ratios += [sum(ratios) / len(ratios)] * (ncol - len(ratios))
        else:
            ratios = []
            for c in range(ncol):
                best = 0
                for r in range(nrow):
                    if owner[r][c] != (r, c) or span[(r, c)][3] != c:
                        continue
                    for line in re.split(r'<br\s*/?>', grid[r][c]):
                        best = max(best, layout.text_width(strip_marks(line), size, face=F_SANS))
                ratios.append(max(best + 900, 3000))
            if sum(ratios) > width:
                # 넓은 열부터 줄여 표 폭에 맞춘다(좁은 열은 지킨다).
                floor = [min(r, 7000) for r in ratios]
                extra = sum(ratios) - width
                shrinkable = [r - f for r, f in zip(ratios, floor)]
                tot = sum(shrinkable) or 1
                ratios = [r - extra * s / tot for r, s in zip(ratios, shrinkable)]
        tot = sum(ratios)
        colw = [int(width * r / tot) for r in ratios]
        colw[-1] += width - sum(colw)

        bf_body = self.st.border_fill()
        bf_head = self.st.border_fill(fill=self.head_fill)
        bf_hl = self.st.border_fill(fill=HIGHLIGHT_FILL)
        cell_line = 130

        # 셀 내용 만들기 + 행 높이 추정
        cells_xml = {}
        need_h = {}
        for r in range(nrow):
            for c in range(ncol):
                if owner[r][c] != (r, c):
                    continue
                r0, c0, r1, c1 = span[(r, c)]
                cw = sum(colw[c0:c1 + 1])
                inner = cw - 282
                text = grid[r][c]
                is_head = r < head_rows
                align = 'CENTER' if is_head else {'l': 'LEFT', 'r': 'RIGHT'}.get(aligns[c], 'CENTER')
                left = 300 if align == 'LEFT' else 0
                img = re.match(r'^\[그림\s+(.+?)\]$', text)
                if img:
                    bin_id, iw, ih = self.add_image(img.group(1).strip())
                    bf = self.st.border_fill(image_ref=bin_id)
                    h = int((cw - 282) * ih / iw) + 82
                    paras = self.para(self.st.para('CENTER', 0, line=cell_line, keep_word=False),
                                      self.run(self.st.char(F_SANS, 10)))
                    cells_xml[(r, c)] = (bf, paras, cw, is_head)
                    need_h[(r, c)] = h
                    continue
                lines_total = 0
                paras = []
                for line in re.split(r'<br\s*/?>', text):
                    pieces = inline_runs(line)
                    plain = strip_marks(line)
                    sp, nl = (0, 1)
                    if self.fit and plain:
                        sp, nl = layout.fit_cell(plain, size, inner - left)
                        if sp:
                            self.report.append(f'표셀  자간 {sp}로 한 줄  | {plain[:30]}')
                    lines_total += nl
                    runs = ''.join(self.run(self.st.char(F_SANS, size - 2 if small else size, sp,
                                                         bold=(bold or is_head), color=color), t)
                                   for t, bold, small, color in pieces)
                    if not runs:
                        runs = self.run(self.st.char(F_SANS, size, 0, bold=is_head))
                    paras.append(self.para(self.st.para(align, 0, left=left, line=cell_line, keep_word=False), runs))
                bf = bf_head if is_head else (bf_hl if r in highlight else bf_body)
                cells_xml[(r, c)] = (bf, ''.join(paras), cw, is_head)
                need_h[(r, c)] = int(lines_total * size * 100 * cell_line / 100 + 82 + 150)

        # 행 높이: 단일 행 셀 기준, 병합 셀은 부족분을 마지막 행에 더한다.
        row_h = [int(size * 100 * 1.3 + 82 + 150)] * nrow
        for (r, c), h in need_h.items():
            r0, c0, r1, c1 = span[(r, c)]
            if r0 == r1:
                row_h[r] = max(row_h[r], h)
        for (r, c), h in need_h.items():
            r0, c0, r1, c1 = span[(r, c)]
            if r1 > r0:
                cur = sum(row_h[r0:r1 + 1])
                if cur < h:
                    row_h[r1] += h - cur

        trs = []
        for r in range(nrow):
            tcs = []
            for c in range(ncol):
                if (r, c) not in cells_xml:
                    continue
                bf, paras, cw, is_head = cells_xml[(r, c)]
                r0, c0, r1, c1 = span[(r, c)]
                ch = sum(row_h[r0:r1 + 1])
                tcs.append(
                    f'<hp:tc name="" header="{1 if is_head else 0}" hasMargin="0" protect="0" editable="0" dirty="0" '
                    f'borderFillIDRef="{bf}"><hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" '
                    f'vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" '
                    f'hasTextRef="0" hasNumRef="0">{paras}</hp:subList><hp:cellAddr colAddr="{c}" rowAddr="{r}"/>'
                    f'<hp:cellSpan colSpan="{c1 - c0 + 1}" rowSpan="{r1 - r0 + 1}"/>'
                    f'<hp:cellSz width="{cw}" height="{ch}"/><hp:cellMargin left="141" right="141" top="41" bottom="41"/></hp:tc>')
            trs.append('<hp:tr>' + ''.join(tcs) + '</hp:tr>')
        tbl = self.tbl_xml(nrow, ncol, width, sum(row_h), bf_body, ''.join(trs), in_margin=(0, 0, 0, 0))
        self.anchor(tbl)
        self.plain.append('[표]')

    def tbl_xml(self, nrow, ncol, width, height, bf, trs, in_margin):
        l, r, t, b = in_margin
        return (f'<hp:tbl id="{self.next_obj()}" zOrder="{self.pid % 1000}" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" '
                f'textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" '
                f'rowCnt="{nrow}" colCnt="{ncol}" cellSpacing="0" borderFillIDRef="{bf}" noAdjust="0">'
                f'<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>'
                f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" '
                f'vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
                f'<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
                f'<hp:inMargin left="{l}" right="{r}" top="{t}" bottom="{b}"/>{trs}</hp:tbl>')

    def anchor(self, tbl_xml, page_break=False, align='RIGHT'):
        cid = self.st.char(F_SANS, 10)
        self.body.append(self.para(self.st.para(align, 0),
                                   f'<hp:run charPrIDRef="{cid}">{tbl_xml}<hp:t/></hp:run>', page_break=page_break))

    def figure(self, rel, opts, full_width):
        bin_id, iw, ih = self.add_image(rel)
        pct = float(opts.get('너비', 100)) / 100
        width = int((TABLE_WIDTH_FULL if full_width else FIGURE_WIDTH) * pct)
        inner_w = width - 1020
        height = int(inner_w * ih / iw) + 282
        if '높이' in opts:
            height = int(float(opts['높이']) * 283.465)  # mm → HWPUNIT
        bf_cell = self.st.border_fill(line='DASH', image_ref=bin_id)
        bf_tbl = self.st.border_fill()
        para = self.para(self.st.para('CENTER', 0), self.run(self.st.char(F_SANS, 10)))
        tc = (f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{bf_cell}">'
              f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" '
              f'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{para}</hp:subList>'
              f'<hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
              f'<hp:cellSz width="{width}" height="{height}"/><hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')
        self.anchor(self.tbl_xml(1, 1, width, height, bf_tbl, f'<hp:tr>{tc}</hp:tr>', (510, 510, 141, 141)),
                    align='CENTER' if pct < 1 else 'RIGHT')
        self.plain.append('[그림]')

    # ------------------------------------------------------------------ 붙임
    def attach_bar(self, num, title):
        hx = self.st.xml
        left_bf = re.search(r'<hh:borderFill id="(\d+)"(?:(?!</hh:borderFill>).)*faceColor="#437FC1"', hx, re.S).group(1)
        right_bf = next(m.group(1) for m in re.finditer(r'<hh:borderFill id="(\d+)"(.*?)</hh:borderFill>', hx, re.S)
                        if 'leftBorder type="SOLID" width="0.12 mm" color="#437FC1"' in m.group(2) and 'faceColor' not in m.group(2))
        outer_bf = self.st.border_fill()
        c_num = self.st.char(F_HEAD, 16, color='#FFFFFF')
        c_sp = self.st.char(F_HEAD, 16)
        c_title = self.st.char(F_HEAD, SIZE_ATTACH)
        p_num = self.para(self.st.para('CENTER', 0), self.run(c_num, f'붙임{num} '))
        p_title = self.para(self.st.para('JUSTIFY', -2277, line=200), self.run(c_sp, ' ') + self.run(c_title, title))

        def tc(col, w, bf, p):
            return (f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{bf}">'
                    f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" '
                    f'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{p}</hp:subList>'
                    f'<hp:cellAddr colAddr="{col}" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
                    f'<hp:cellSz width="{w}" height="2731"/><hp:cellMargin left="141" right="141" top="141" bottom="141"/></hp:tc>')
        trs = '<hp:tr>' + tc(0, 5700, left_bf, p_num) + tc(1, 42490, right_bf, p_title) + '</hp:tr>'
        self.anchor(self.tbl_xml(1, 2, 48190, 2731, outer_bf, trs, (141, 141, 141, 141)), page_break=True, align='JUSTIFY')
        self.plain.append(f'붙임{num} {title}')

    # ------------------------------------------------------------- 머리 부분
    def title_and_date(self):
        title = self.meta.get('제목', '').strip()
        if not title:
            raise SystemExit('입력 첫머리에 "제목: …" 줄이 필요합니다.')
        # 제목: HY헤드라인M 20pt 장평 90. 길면 자간 → 크기 순으로 줄인다.
        inner = 47341 - 282
        size, sp, overflow = 20, 0, False
        while layout.text_width(' ' + title, size, sp, 90, face=F_HEAD) > inner * layout.SAFETY:
            if sp > -10:
                sp -= 1
            elif size > 17:
                size, sp = size - 1, 0
            else:
                size, sp, overflow = 20, 0, True
                break
        cid = self.st.char(F_HEAD, size, sp, ratio=90)
        sec = self.sec_xml
        sec = re.sub(r'<hp:run charPrIDRef="\d+"><hp:t>' + re.escape(TITLE_MARK) + '</hp:t></hp:run>',
                     lambda m: f'<hp:run charPrIDRef="{cid}"><hp:t> {self.esc(title)}</hp:t></hp:run>', sec)
        date = self.meta.get('날짜') or default_date()
        dept = self.meta.get('부서') or '지능화번역팀'
        sec = sec.replace(DATE_MARK, self.esc(f'< {date}  {dept} >'))
        date_cid = self.st.char(F_SANS, SIZE_DATE)
        sec = re.sub(r'(<hp:p [^>]*paraPrIDRef="\d+"[^>]*><hp:run charPrIDRef=")\d+("><hp:t>&lt; )',
                     lambda m: m.group(1) + date_cid + m.group(2), sec)
        self.sec_xml = sec
        self.plain += [title, f'< {date}  {dept} >']
        if overflow:
            self.report.append('확인  제목이 두 줄로 넘어감 — 제목을 줄여 주세요(최종본 제목은 한 줄)')
        elif sp or size != 20:
            self.report.append(f'제목  {size}pt 자간 {sp}로 한 줄에 맞춤')

    # ------------------------------------------------------------------ 조립
    def build(self, items):
        self.title_and_date()
        self.spacer(GAP['after_date'])
        prev = None          # 직전 항목 종류
        ctx = None           # 노트 깊이 판단용: 'o' | 'dash' | 'obj'
        attach_no = 0
        after_bar = False    # 붙임 띠 바로 뒤(ㅇ 없이 표가 오면 전체 폭)
        first_section = True
        for it in items:
            t = it['t']
            if t == 'sec':
                if not first_section:
                    self.spacer(GAP['before_section'])
                first_section = False
                self.section(it['text'])
                self.spacer(GAP['after_section'])
                ctx, after_bar = None, False
            elif t == 'attach':
                attach_no += 1
                self.attach_bar(attach_no, it['text'])
                self.spacer(GAP['after_attach'])
                ctx, after_bar = None, True
            elif t == 'o':
                if prev not in ('sec', 'attach', None):
                    self.spacer(GAP['before_o'])
                self.text_para('o', it['text'])
                ctx, after_bar = 'o', False
            elif t == 'dash':
                if prev in ('table', 'figure'):
                    self.spacer(GAP['around_table'])
                elif prev not in ('sec', 'attach'):
                    self.spacer(GAP['child'])
                self.text_para('dash', it['text'])
                ctx = 'dash'
            elif t == 'note':
                if prev in ('table', 'figure'):
                    self.spacer(GAP['around_table'])
                elif prev not in ('sec', 'attach'):
                    self.spacer(GAP['child'])
                deep = ctx in ('dash', 'obj')
                kind = ('note2' if deep else 'note1') + ('b' if it['level'] == 2 else '')
                self.text_para(kind, it['text'])
            elif t == 'caption':
                self.spacer(GAP['around_caption'] if prev not in ('sec', 'attach') else 0)
                self.caption(it['text'])
                self.spacer(GAP['around_caption'])
            elif t in ('table', 'figure'):
                if prev not in ('caption', 'sec', 'attach'):
                    self.spacer(GAP['around_table'])
                if t == 'table':
                    self.table(it['rows'], it['opts'], full_width=after_bar)
                else:
                    self.figure(it['path'], it['opts'], full_width=after_bar)
                ctx = 'obj'
            elif t == 'end':
                self.spacer(GAP['before_end'])
                self.end_mark()
            prev = t
        return self

    def write(self, out: Path):
        sec = self.sec_xml.replace('</hs:sec>', ''.join(self.body) + '</hs:sec>')
        self.files['Contents/section0.xml'] = sec.encode('utf-8')
        self.files['Contents/header.xml'] = self.st.xml.encode('utf-8')
        hpf = self.files['Contents/content.hpf'].decode('utf-8')
        hpf = re.sub(r'<opf:title>[^<]*</opf:title>', f'<opf:title>{self.esc(self.meta.get("제목", ""))}</opf:title>', hpf)
        now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        hpf = re.sub(r'(<opf:meta name="ModifiedDate" content="text">)[^<]*', rf'\g<1>{now}', hpf)
        items = ''.join(f'<opf:item id="{bid}" href="{href}" media-type="{mt}" isEmbeded="1"/>' for bid, href, mt, _ in self.images)
        hpf = hpf.replace('<opf:item id="header"', items + '<opf:item id="header"', 1)
        self.files['Contents/content.hpf'] = hpf.encode('utf-8')
        for _, href, _, data in self.images:
            self.files[href] = data
        self.files['Preview/PrvText.txt'] = '\r\n'.join(self.plain)[:1024].encode('utf-8')
        self.files['Preview/PrvImage.png'] = blank_png()
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr(zipfile.ZipInfo('mimetype'), self.files['mimetype'], compress_type=zipfile.ZIP_STORED)
            for n, data in self.files.items():
                if n != 'mimetype':
                    z.writestr(n, data, compress_type=zipfile.ZIP_DEFLATED)


def default_date():
    d = datetime.date.today()
    return f'’{d.year % 100:02d}. {d.month}. {d.day}'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input')
    ap.add_argument('output')
    ap.add_argument('--no-fit', action='store_true', help='자간 자동 맞춤을 끈다')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    src = Path(a.input)
    meta, items = parse(src.read_text(encoding='utf-8'))
    b = Builder(meta, src.parent, fit=not a.no_fit).build(items)
    b.write(Path(a.output))
    if not a.quiet:
        print(f'생성: {a.output}')
        if b.report:
            print('--- 줄 맞춤 보고 (추정치, 한글에서 확인) ---')
            for line in b.report:
                print(' ', line)


if __name__ == '__main__':
    main()
