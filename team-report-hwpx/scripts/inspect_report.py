#!/usr/bin/env python3
"""HWPX 보고서가 팀장 최종본 양식을 지키는지 점검한다.

    python3 inspect_report.py 보고서.hwpx [--summary]

검사 항목
  - 위치별 글꼴·크기: 제목, □, ㅇ/-, * 주석, < 캡션 >, 표 머리행/본문, 붙임 띠, 작성일 줄
  - 기호: 주석에 • 대신 * 를 쓰는지, ㅇ/- 앞 공백 수
  - 줄 채움: 두 줄 이상 문단의 마지막 줄이 절반에 못 미치는지
    (한글로 저장한 파일은 저장된 줄바꿈 정보를, 생성 직후 파일은 폭 추정을 쓴다)
--summary 를 주면 위치별 글꼴 분포표도 출력한다.
"""
import argparse
import collections
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout  # noqa: E402

NS = {'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
      'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
      'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
      'hs': 'http://www.hancom.co.kr/hwpml/2011/section'}

# 위치별 허용값: (글꼴, {크기}) — 팀장 최종본 두 편에서 실제로 쓴 값
SPEC = {
    'TITLE': ('HY헤드라인M', {17, 18, 19, 20}),
    '□': ('HY헤드라인M', {16}),
    'ㅇ': ('휴먼명조', {15, 13}),        # 13pt 는 괄호 속 보충(예: (1만 건))
    '-': ('휴먼명조', {15, 13}),
    '*': ('함초롬돋움', {12, 13, 11}),
    'CAPTION': ('함초롬돋움', {13}),
    'DATE': ('함초롬돋움', {12, 13}),
    'TBL-HEAD': ('함초롬돋움', {11, 12}),
    'TBL-BODY': ('함초롬돋움', {7, 8, 9, 10, 11, 12}),
    'ATTACH': ('HY헤드라인M', {15, 16}),
}


def load(path):
    z = zipfile.ZipFile(path)
    H = ET.fromstring(z.read('Contents/header.xml'))
    S = ET.fromstring(z.read('Contents/section0.xml'))
    fonts = {ff.get('lang'): {f.get('id'): f.get('face') for f in ff.findall('hh:font', NS)}
             for ff in H.iter('{%s}fontface' % NS['hh'])}
    cp = {}
    for c in H.iter('{%s}charPr' % NS['hh']):
        fr = c.find('hh:fontRef', NS)
        cp[c.get('id')] = dict(face=fonts['HANGUL'][fr.get('hangul')], size=int(c.get('height')) / 100,
                               sp=int(c.find('hh:spacing', NS).get('hangul')),
                               ratio=int(c.find('hh:ratio', NS).get('hangul')),
                               bold=c.find('hh:bold', NS) is not None)
    pp = {}
    for p in H.iter('{%s}paraPr' % NS['hh']):
        case = p.find('.//hp:case', NS)
        m = (case if case is not None else p).find('.//hh:margin', NS)
        it = m.find('hc:intent', NS) if m is not None else None
        intent = int(it.get('value')) if it is not None else 0
        pp[p.get('id')] = dict(align=p.find('hh:align', NS).get('horizontal'), intent=intent)
    return S, cp, pp


def ptext(p):
    return ''.join(t.text or '' for r in p.findall('hp:run', NS) for t in r.findall('hp:t', NS))


def runs_of(p, cp):
    out = []
    for r in p.findall('hp:run', NS):
        t = ''.join(x.text or '' for x in r.findall('hp:t', NS))
        if t:
            out.append((t, cp[r.get('charPrIDRef')]))
    return out


def role_of(text):
    s = text.lstrip()
    if not s:
        return None
    if s.startswith('□'):
        return '□'
    if s.startswith(('ㅇ', '○', 'o ')):
        return 'ㅇ'
    if s.startswith('- 이하'):
        return 'END'
    if s.startswith('-'):
        return '-'
    if s.startswith(('*', '•', '※')):
        return '*'
    if s.startswith('<') and s.rstrip().endswith('>'):
        return 'DATE' if ('’' in s or "'" in s) and re.search(r'\d+\.\s*\d+\.', s) else 'CAPTION'
    return 'OTHER'


def inspect(path, summary=False):
    S, cp, pp = load(path)
    issues, stats = [], collections.defaultdict(collections.Counter)

    table_bad = collections.OrderedDict()   # where → Counter(잘못된 글꼴)

    def check(role, runs, where, table=False):
        face, sizes = SPEC[role]
        for t, c in runs:
            if not t.strip():
                continue
            stats[role][f"{c['face']} {c['size']:g}pt"] += 1
            if c['face'] != face or round(c['size']) not in sizes:
                got = f"{c['face']} {c['size']:g}pt"
                if table:
                    table_bad.setdefault((where, role), collections.Counter())[got] += 1
                else:
                    issues.append(f"[글꼴] {where}: {role} 는 {face} {'/'.join(str(s) for s in sorted(sizes))}pt 여야 함 "
                                  f"→ {got}  «{t.strip()[:24]}»")
                break

    def body_para(p, where):
        text = ptext(p)
        role = role_of(text)
        if role in (None, 'END'):
            return
        runs = runs_of(p, cp)
        if role == 'OTHER':
            return
        check(role, runs, where)
        s = text.lstrip()
        if s.startswith('•'):
            issues.append(f"[기호] {where}: 주석 기호는 • 대신 * 를 씀  «{s[:24]}»")
        if role == 'ㅇ' and not text.startswith(' ㅇ '):
            issues.append(f"[기호] {where}: ㅇ 앞뒤 공백은 ' ㅇ ' 형식  «{text[:16]!r}»")
        if role == '-' and not re.match(r'^ {2,3}- ', text):
            issues.append(f"[기호] {where}: - 앞은 공백 2칸(연구 과제 3단은 3칸)  «{text[:16]!r}»")
        # 줄 채움 추정
        if role in ('ㅇ', '-', '*'):
            intent = pp[p.get('paraPrIDRef')]['intent']
            cont = layout.BODY_WIDTH - abs(intent)
            lsa = p.find('hp:linesegarray', NS)
            if lsa is not None and len(lsa):
                # 한글이 저장한 실제 줄바꿈: 마지막 줄 텍스트 폭만 추정한다.
                n = len(lsa)
                start = int(lsa[n - 1].get('textpos'))
                chars = [(ch, c) for t, c in runs for ch in t]
                tail = chars[start:]
                fill = sum(layout.text_width(ch, c['size'], c['sp'], c['ratio'], c['face']) for ch, c in tail) / cont
                basis = ''
            else:
                lines = layout.wrap_lines([(t, c['size'], c['sp'], c['ratio'], c['face']) for t, c in runs],
                                          layout.BODY_WIDTH, cont)
                n, fill, basis = len(lines), lines[-1][0] / cont, '(추정)'
            if n >= 2 and fill < 0.5:
                issues.append(f"[줄채움] {where}: {n}째 줄이 약 {fill:.0%}{basis} — 자간을 좁혀 한 줄 줄이거나 "
                              f"문장을 보강  «{s[:28]}»")

    sec = S if S.tag.endswith('sec') else S.find('hs:sec', NS)
    pno = 0
    title_seen = False
    for p in sec.findall('hp:p', NS):
        pno += 1
        where = f'문단{pno}'
        body_para(p, where)
        for run in p.findall('hp:run', NS):
            for tbl in run.findall('hp:tbl', NS):
                rows = tbl.findall('hp:tr', NS)
                ncol, nrow = int(tbl.get('colCnt')), int(tbl.get('rowCnt'))
                all_text = ''.join(tbl.itertext())
                if ncol == 1 and nrow == 3 and pno <= 3 and not title_seen:
                    title_seen = True
                    for tc in tbl.iter('{%s}tc' % NS['hp']):
                        for cp_ in tc.iter('{%s}p' % NS['hp']):
                            check('TITLE', runs_of(cp_, cp), '제목')
                    continue
                if ncol == 2 and nrow == 1 and '붙임' in all_text:
                    tcs = tbl.findall('.//hp:tc', NS)
                    for cp_ in tcs[1].iter('{%s}p' % NS['hp']):
                        check('ATTACH', runs_of(cp_, cp), '붙임 띠')
                    continue
                for ri, tr in enumerate(rows):
                    for tc in tr.findall('hp:tc', NS):
                        head = tc.get('header') == '1' or ri == 0
                        for cp_ in tc.find('hp:subList', NS).findall('hp:p', NS):
                            runs = runs_of(cp_, cp)
                            if runs:
                                check('TBL-HEAD' if head else 'TBL-BODY', runs, f'{where} 표', table=True)
    for (where, role), bad in table_bad.items():
        face, sizes = SPEC[role]
        got = ', '.join(f'{k}×{n}' for k, n in bad.most_common())
        issues.append(f"[글꼴] {where}: {'머리행' if role == 'TBL-HEAD' else '본문 셀'}은 {face} "
                      f"{'/'.join(str(x) for x in sorted(sizes))}pt 여야 함 → {got}")
    if summary:
        print('--- 위치별 글꼴 분포 ---')
        for k in sorted(stats):
            print(f'  {k}: ' + ', '.join(f'{v}×{n}' for v, n in stats[k].most_common()))
    if issues:
        print(f'--- 점검 결과: {len(issues)}건 ---')
        for i in issues:
            print('  ' + i)
    else:
        print('--- 점검 결과: 양식 위반 없음 ---')
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('hwpx')
    ap.add_argument('--summary', action='store_true')
    a = ap.parse_args()
    inspect(a.hwpx, a.summary)


if __name__ == '__main__':
    main()
