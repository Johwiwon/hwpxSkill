# -*- coding: utf-8 -*-
"""문제점 ↔ 추진내용 ↔ 기대효과 대응표 뼈대를 출력한다.

본문을 쓰기 전에 이 표를 채워 사용자와 합의한다.
    python3 plan_flow.py --problems 3
    python3 plan_flow.py --problems 3 --actions 4    # 추진내용을 더 두는 경우
"""
import argparse, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--problems', type=int, required=True, help='문제점 개수')
    ap.add_argument('--actions', type=int, default=None, help='추진내용 개수(기본: 문제점과 동일)')
    ap.add_argument('--style', choices=['A','B'], default='B', help='A=전형적, B=간소화')
    a=ap.parse_args()
    n=a.problems; m=a.actions or n
    if m<n:
        print(f'[오류] 추진내용({m})이 문제점({n})보다 적습니다.', file=sys.stderr)
        print('       답하지 않은 문제가 남습니다. 추진내용을 늘리거나,', file=sys.stderr)
        print('       해당 문제점을 향후계획으로 옮기고 그 사실을 밝히세요.', file=sys.stderr)
        return 2
    mark='①②③④⑤⑥⑦⑧⑨⑩'
    print(f'# 흐름 설계 (양식 {a.style}, 문제점 {n} → 추진내용 {m})\n')
    print('| # | 문제점 | 추진내용 | 기대효과 | 근거 데이터 |')
    print('|---|---|---|---|---|')
    for i in range(m):
        k=mark[i] if i<len(mark) else str(i+1)
        prob='(작성)' if i<n else '(추가 항목 — 대응 문제점 없음)'
        print(f'| {k} | {prob} | (작성) | (작성) | (수치·출처) |')
    print()
    print('점검 사항')
    print('  - 기대효과에 숫자가 없는 행이 있으면 「얼마나 좋아졌나」에 답할 수 없습니다.')
    print('  - 근거 데이터 열이 비어 있으면 검토 자리에서 출처를 대지 못합니다.')
    if a.style=='B':
        print('  - 양식 B: 기대효과를 추진내용 항목의 마지막 하위 항목으로 녹여도 됩니다.')
    else:
        print('  - 양식 A: 현황(사실)과 문제점(판단)을 다른 절로 나눠 쓰세요.')
    return 0

if __name__=='__main__':
    sys.exit(main())
