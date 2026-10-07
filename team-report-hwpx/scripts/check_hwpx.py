#!/usr/bin/env python3
"""HWPX 배포 전 구조 검사 — 한글이 '손상된 파일'로 여길 만한 문제를 찾는다.

    python3 check_hwpx.py 보고서.hwpx

검사 항목
  1. 패키지: 첫 항목 mimetype(무압축, application/hwp+zip), 필수 파트 존재
  2. XML: 모든 XML 파트가 문법적으로 올바른지
  3. 목록: content.hpf 에 적힌 파일이 실제로 있는지, 그림 참조(binaryItemIDRef)가 목록에 있는지
  4. 개수: header.xml 의 itemCnt·fontCnt 가 실제 항목 수와 같은지
  5. 참조: 본문의 charPr/paraPr/borderFill/style id, 글자모양의 글꼴 id 가 모두 정의되어 있는지
  6. 표: 행·열 수와 셀 주소·병합이 겹치거나 빈칸 없이 맞는지
표준 라이브러리만 쓴다. 문제가 없으면 종료 코드 0, 있으면 1.
"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
      'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
      'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
      'opf': 'http://www.idpf.org/2007/opf/'}
HP = '{%s}' % NS['hp']


def check(path):
    errors, warns = [], []
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return ['ZIP 파일이 아님'], []
    names = z.namelist()

    # 1. 패키지
    first = z.infolist()[0]
    if first.filename != 'mimetype':
        errors.append(f'첫 항목이 mimetype 이 아님({first.filename})')
    elif first.compress_type != zipfile.ZIP_STORED:
        errors.append('mimetype 이 압축되어 있음(무압축이어야 함)')
    elif z.read('mimetype').decode('ascii', 'ignore').strip() != 'application/hwp+zip':
        errors.append('mimetype 내용이 application/hwp+zip 이 아님')
    for need in ('version.xml', 'Contents/header.xml', 'Contents/content.hpf', 'META-INF/container.xml'):
        if need not in names:
            errors.append(f'필수 파트 없음: {need}')

    # 2. XML
    trees = {}
    xml_bad = False
    for n in names:
        if n.endswith(('.xml', '.hpf', '.rdf')):
            try:
                trees[n] = ET.fromstring(z.read(n))
            except ET.ParseError as e:
                errors.append(f'XML 문법 오류: {n} — {e}')
                xml_bad = True
    if xml_bad or 'Contents/header.xml' not in trees or 'Contents/content.hpf' not in trees:
        return errors, warns

    # 3. 목록
    hpf = trees['Contents/content.hpf']
    items = {it.get('id'): it.get('href') for it in hpf.iter('{%s}item' % NS['opf'])}
    for iid, href in items.items():
        if href not in names:
            errors.append(f'content.hpf 의 {iid} → {href} 파일 없음')
    sections = sorted(n for n in names if re.match(r'Contents/section\d+\.xml$', n))
    if not sections:
        errors.append('본문 section 파트 없음')
    for s in sections:
        if s not in items.values():
            warns.append(f'{s} 가 content.hpf 목록에 없음')
    raw_all = b''.join(z.read(n) for n in ['Contents/header.xml'] + sections)
    for ref in set(re.findall(rb'binaryItemIDRef="([^"]+)"', raw_all)):
        if ref.decode() not in items:
            errors.append(f'그림 참조 {ref.decode()} 가 content.hpf 목록에 없음')

    # 4. 개수
    H = trees['Contents/header.xml']
    for cont, item in (('fontfaces', 'fontface'), ('borderFills', 'borderFill'), ('charProperties', 'charPr'),
                       ('tabProperties', 'tabPr'), ('numberings', 'numbering'), ('bullets', 'bullet'),
                       ('paraProperties', 'paraPr'), ('styles', 'style')):
        c = H.find('.//hh:%s' % cont, NS)
        if c is None:
            continue
        real = len(c.findall('hh:%s' % item, NS))
        if c.get('itemCnt') is not None and int(c.get('itemCnt')) != real:
            errors.append(f'header {cont} itemCnt={c.get("itemCnt")} 인데 실제 {real}개')
    fonts = {}
    for ff in H.iter('{%s}fontface' % NS['hh']):
        ids = {f.get('id') for f in ff.findall('hh:font', NS)}
        fonts[ff.get('lang')] = ids
        if ff.get('fontCnt') is not None and int(ff.get('fontCnt')) != len(ids):
            errors.append(f'fontface {ff.get("lang")} fontCnt={ff.get("fontCnt")} 인데 실제 {len(ids)}개')

    # 5. 참조
    def ids(tag):
        return {e.get('id') for e in H.iter('{%s}%s' % (NS['hh'], tag))}
    charpr, parapr, bf, style = ids('charPr'), ids('paraPr'), ids('borderFill'), ids('style')
    lang_map = {'hangul': 'HANGUL', 'latin': 'LATIN', 'hanja': 'HANJA', 'japanese': 'JAPANESE',
                'other': 'OTHER', 'symbol': 'SYMBOL', 'user': 'USER'}
    for c in H.iter('{%s}charPr' % NS['hh']):
        fr = c.find('hh:fontRef', NS)
        for attr, lang in lang_map.items():
            if fr is not None and fr.get(attr) not in fonts.get(lang, set()):
                errors.append(f'charPr {c.get("id")} 의 {attr} 글꼴 id {fr.get(attr)} 없음')
        if c.get('borderFillIDRef') and c.get('borderFillIDRef') not in bf:
            errors.append(f'charPr {c.get("id")} 의 borderFill {c.get("borderFillIDRef")} 없음')
    missing = {}
    for s in sections:
        for e in trees[s].iter():
            for attr, pool in (('charPrIDRef', charpr), ('paraPrIDRef', parapr),
                               ('borderFillIDRef', bf), ('styleIDRef', style)):
                v = e.get(attr)
                if v is not None and v not in pool:
                    missing.setdefault((attr, v), 0)
                    missing[(attr, v)] += 1
    for (attr, v), n in missing.items():
        errors.append(f'본문의 {attr}="{v}" 정의 없음({n}곳)')

    # 6. 표
    for s in sections:
        for k, tbl in enumerate(trees[s].iter(HP + 'tbl'), 1):
            rows, cols = int(tbl.get('rowCnt')), int(tbl.get('colCnt'))
            grid = [[0] * cols for _ in range(rows)]
            trs = tbl.findall('hp:tr', NS)
            if len(trs) != rows:
                errors.append(f'{s} 표{k}: rowCnt={rows} 인데 행 {len(trs)}개')
            for tr in trs:
                for tc in tr.findall('hp:tc', NS):
                    a, sp = tc.find('hp:cellAddr', NS), tc.find('hp:cellSpan', NS)
                    r, c = int(a.get('rowAddr')), int(a.get('colAddr'))
                    rs, cs = int(sp.get('rowSpan')), int(sp.get('colSpan'))
                    if r + rs > rows or c + cs > cols:
                        errors.append(f'{s} 표{k}: 셀({r},{c}) 병합이 표 밖으로 나감')
                        continue
                    for rr in range(r, r + rs):
                        for cc in range(c, c + cs):
                            grid[rr][cc] += 1
            over = sum(1 for row in grid for v in row if v > 1)
            empty = sum(1 for row in grid for v in row if v == 0)
            if over:
                errors.append(f'{s} 표{k}: 겹치는 칸 {over}개')
            if empty:
                errors.append(f'{s} 표{k}: 비어 있는 칸 {empty}개')

    if any(b'<hp:linesegarray' in z.read(s) for s in sections):
        warns.append('레이아웃 캐시(linesegarray)가 있음 — 본문을 고친 뒤라면 지워야 함')
    return errors, warns


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    errors, warns = check(sys.argv[1])
    for w in warns:
        print('[주의]', w)
    if errors:
        print(f'[실패] {len(errors)}건')
        for e in errors:
            print('  -', e)
        return 1
    print('[통과] 구조 검사 이상 없음')
    return 0


if __name__ == '__main__':
    sys.exit(main())
