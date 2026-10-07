"""글자 폭 추정과 줄 나눔 시뮬레이션.

팀장 최종본·직전본 4개 파일의 한글 레이아웃 캐시(linesegarray)에서 뽑은
실제 줄바꿈 78줄(제약 156개)로 맞춘 폭 모델이다. 156개 중 153개가 일치한다.
폭은 글자 크기(em) 대비 비율이며, 자간 s% 는 글자마다 em*s/100 이 더해진다.

  한글·□·ㅇ 1.00 / 공백 0.45 / 숫자 0.50 / 영대문자 0.60 / 영소문자 0.45 / 기타 0.50
  함초롬돋움은 한글 외 글자가 약 15% 좁다(주석·표 49줄로 보정, 1건 불일치).

추정치이므로 경계(±2%)에 걸린 문단은 한글에서 눈으로 확인해야 한다.
"""

BODY_WIDTH = 48190          # A4 210mm - 좌우 여백 20mm*2 = 170mm (HWPUNIT)
SAFETY = 0.97               # 한 줄에 넣을 때 남겨 두는 여유(영문 대문자가 많은 줄은 실제보다 좁게 추정되는 경향)

W = dict(H=1.0, S=0.45, D=0.5, U=0.6, L=0.45, P=0.5)
SPECIAL = {'-': 0.6, '*': 0.62, '→': 1.0}


def char_em(ch: str) -> float:
    if ch in SPECIAL:
        return SPECIAL[ch]
    if '가' <= ch <= '힣' or 'ㄱ' <= ch <= 'ㆎ' or ch in '□○●■◇◆※':
        return W['H']
    if ch == ' ':
        return W['S']
    if ch.isdigit():
        return W['D']
    if 'A' <= ch <= 'Z':
        return W['U']
    if 'a' <= ch <= 'z':
        return W['L']
    if '一' <= ch <= '鿿':
        return W['H']
    return W['P']


FACE_NON_HANGUL = {'함초롬돋움': 0.85, '휴먼고딕': 0.85}


def text_width(text: str, size_pt: float, spacing: int = 0, ratio: int = 100, face: str = '휴먼명조') -> float:
    """HWPUNIT 폭. spacing 은 자간(%), ratio 는 장평(%)."""
    em = size_pt * 100
    k = FACE_NON_HANGUL.get(face, 1.0)
    total = 0.0
    for c in text:
        w = char_em(c)
        if k != 1.0 and not ('\uac00' <= c <= '\ud7a3'):
            w *= k
        total += em * (w * ratio / 100 + spacing / 100)
    return total


def runs_width(runs):
    """runs: [(text, size_pt, spacing, ratio[, face])]"""
    return sum(text_width(*r) for r in runs)


def wrap_lines(runs, first_width, cont_width, keep_word=True):
    """어절(공백) 단위 줄 나눔. 각 줄의 (폭, 텍스트)를 돌려준다."""
    # 글자 단위로 (문자, 폭) 펼치기
    chars = []
    for run in runs:
        t, rest = run[0], run[1:]
        for c in t:
            chars.append((c, text_width(c, *rest)))
    tokens = []  # (텍스트, 폭, 뒤 공백 폭)
    if keep_word:
        cur, cw = '', 0.0
        for c, w in chars:
            if c == ' ':
                tokens.append([cur, cw, w])
                cur, cw = '', 0.0
            else:
                cur += c
                cw += w
        tokens.append([cur, cw, 0.0])
    else:
        tokens = [[c, w, 0.0] if c != ' ' else ['', 0.0, w] for c, w in chars]
    lines, line_txt, line_w, avail = [], '', 0.0, first_width
    pending_space = 0.0
    for txt, w, sp_after in tokens:
        if line_txt and line_w + pending_space + w > avail:
            lines.append((line_w, line_txt))
            line_txt, line_w, avail = txt, w, cont_width
        else:
            line_w += pending_space + w
            line_txt += (' ' if pending_space and line_txt else '') + txt
        pending_space = sp_after
    lines.append((line_w, line_txt))
    return lines


def fit_paragraph(prefix_run, body_runs, intent, max_tighten=15, width=BODY_WIDTH, face='휴먼명조'):
    """본문 문단의 자간을 정한다.

    prefix_run: (text, size, spacing, ratio) — ' ㅇ ' 같은 머리 기호(자간 고정)
    face      : 글꼴(폭 보정용) — ㅇ/- 는 휴먼명조, * 는 함초롬돋움
    body_runs : [(text, size, ratio)] — 자간을 함께 조정할 본문 런들
    반환: (spacing, lines, last_fill, note)
      - 두 줄 이상인데 마지막 줄이 절반에 못 미치면 자간을 좁혀 한 줄 줄이기를 시도한다.
      - 줄일 수 없으면 spacing 0 으로 두고 note 에 보강 권장을 남긴다.
    """
    first = width * SAFETY
    cont = (width - abs(intent)) * SAFETY

    def layout(sp):
        runs = [tuple(prefix_run) + (face,)] + [(t, s, sp, r, face) for t, s, r in body_runs]
        return wrap_lines(runs, first, cont)

    base = layout(0)
    n = len(base)
    last_fill = base[-1][0] / (cont if n > 1 else first)
    if n == 1:
        return 0, 1, last_fill, ''
    if last_fill >= 0.5:
        return 0, n, last_fill, ''
    for sp in range(-1, -max_tighten - 1, -1):
        trial = layout(sp)
        if len(trial) < n:
            fill = trial[-1][0] / (cont if len(trial) > 1 else first)
            return sp, len(trial), fill, f'자간 {sp}로 {n}줄→{len(trial)}줄'
    return 0, n, last_fill, f'{n}째 줄이 {last_fill:.0%}만 참 — 문장을 보강하거나 줄여 주세요'


def fit_cell(text, size_pt, inner_width, max_tighten=15, ratio=100, face='함초롬돋움'):
    """표 셀: 한 줄을 조금 넘치면 자간을 좁혀 한 줄로, 많이 넘치면 줄바꿈.

    영문 문장이 주인 셀은 좁히지 않고 줄바꿈한다(영문 자간을 좁히면 읽기 어렵다).
    """
    w0 = text_width(text, size_pt, 0, ratio, face)
    if w0 <= inner_width * SAFETY:
        return 0, 1
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    hangul = sum(1 for c in text if '\uac00' <= c <= '\ud7a3')
    for sp in ([] if latin > hangul else range(-1, -max_tighten - 1, -1)):
        if text_width(text, size_pt, sp, ratio, face) <= inner_width * SAFETY:
            return sp, 1
    lines = wrap_lines([(text, size_pt, 0, ratio, face)], inner_width * SAFETY, inner_width * SAFETY, keep_word=False)
    return 0, len(lines)
