#!/usr/bin/env python3
"""src.html 의 슬라이드(<section class="slide ...">)를 보고, 고르고, 순서를 바꾼다.

usage:
  slides.py <src.html> list                 # 번호 · 클래스 · 장 제목
  slides.py <src.html> keep 1,2,4,4,8,13    # 적은 순서대로 남긴다(같은 번호를 두 번 쓰면 복제)
  slides.py <src.html> drop 5,6             # 빼고 나머지는 그대로
  slides.py <src.html> check                # 견본 자리표시(발표 제목, 부서 이름 등)가 남은 장을 찾는다

keep/drop 전에 <src.html>.bak 으로 백업한다. 장 앞의 <!-- ... --> 주석은 그 장과 함께 움직인다.
"""
import html
import re
import shutil
import sys

# 견본 덱에만 있는 문구. 실제 덱에 남아 있으면 채우지 않은 자리표시다.
PLACEHOLDERS = ['발표 제목', '강조할 두 번째 줄', '부서 이름', '<b>발표자</b>이름', '부제는 두 줄 이내로',
                '장 제목은 결론을', '첫 번째 사례', '방식 이름', '단계 이름', '원칙 이름', '지표 이름',
                '판정 한 줄', '현상 1', '첫 번째 묶음', '질문에 대한 답', '옆 카드 제목', '근거 한 줄',
                '모델 이름', '약 000원', '0.0%']

SECTION = re.compile(r'(?:<!--[^\n]*-->\n)?<section class="slide[^"]*">.*?</section>\n*', re.S)


def split(src):
    blocks = list(SECTION.finditer(src))
    if not blocks:
        sys.exit('슬라이드를 찾지 못했습니다.')
    head, tail = src[:blocks[0].start()], src[blocks[-1].end():]
    return head, [b.group(0) for b in blocks], tail


def title(block):
    m = re.search(r'<h2>(.*?)</h2>', block, re.S) or re.search(r'<h1>(.*?)</h1>', block, re.S) \
        or re.search(r'class="big[^"]*">(.*?)</div>', block, re.S)
    text = re.sub(r'<[^>]+>', ' ', m.group(1)) if m else ''
    return html.unescape(re.sub(r'\s+', ' ', text)).strip()


def nums(arg, total):
    out = [int(x) for x in arg.split(',') if x.strip()]
    bad = [n for n in out if not 1 <= n <= total]
    if bad:
        sys.exit(f'없는 번호: {bad} (1~{total})')
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    path, cmd = sys.argv[1], sys.argv[2]
    src = open(path, encoding='utf8').read()
    head, blocks, tail = split(src)
    if cmd == 'list':
        for i, b in enumerate(blocks, 1):
            cls = re.search(r'<section class="slide([^"]*)"', b).group(1).strip() or '-'
            print(f'{i:>2}  [{cls}]  {title(b)}')
        return
    if cmd == 'check':
        found = 0
        m = re.search(r'<title>(.*?)</title>', head)
        if m and m.group(1).strip() in ('발표 제목', ''):
            print('  <title>: 견본 그대로(발표 제목을 넣지 않음)'); found += 1
        for i, b in enumerate(blocks, 1):
            hits = [p for p in PLACEHOLDERS if p in b]
            if hits:
                found += 1
                print(f'{i:>2}  {title(b)}\n    남은 자리표시: {", ".join(hits)}')
        print('자리표시 없음' if not found else f'자리표시가 남은 곳 {found}곳')
        sys.exit(1 if found else 0)
    if cmd not in ('keep', 'drop') or len(sys.argv) < 4:
        sys.exit(__doc__)
    picked = nums(sys.argv[3], len(blocks))
    order = picked if cmd == 'keep' else [i for i in range(1, len(blocks) + 1) if i not in picked]
    shutil.copy(path, path + '.bak')
    body = ''.join(blocks[i - 1].rstrip('\n') + '\n\n' for i in order)
    open(path, 'w', encoding='utf8').write(head + body + tail.lstrip('\n'))
    print(f'{len(order)}장 남김 (백업: {path}.bak). 장 번호 배지를 다시 확인하세요.')


if __name__ == '__main__':
    main()
