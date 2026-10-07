# -*- coding: utf-8 -*-
"""보고서 구조·문장 점검 — 절 구성, 항목 개수 대응, 개요 충실도,
   줄 채움, 항목 라벨, 문단 간격

    python3 check_report.py 보고서.hwpx
    python3 check_report.py 보고서.hwpx --style B --json
"""
import sys, os, re, json, argparse, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hwpxlib as H

SEC_A=['배경','목적','현황','필요성','문제점','개선방안','추진','기대효과','향후계획','붙임']
SEC_B=['개요','현황','문제점','개선방안','추진','기대효과','향후계획','붙임']
PROBLEM_KEY=['문제점','필요성']
ACTION_KEY =['개선방안','추진내용','추진 내용','추진현황','추진 현황']
EFFECT_KEY =['기대효과','기대 효과']

def outline(path):
    """(종류, 텍스트) 목록. 종류: sec(□) / item(ㅇ) / sub(-) / note(* · **, 옛 문서의 •) / tbl"""
    xml=H.read_part(path)
    out=[]
    for (_,_,p) in H.split_paras(xml):
        t=' '.join(H.ptext(p).split())
        if '<hp:tbl' in p: out.append(('tbl', t[:40])); continue
        if not t: continue
        if t.startswith('□'):   out.append(('sec',  t.lstrip('□ ').strip()))
        elif t.startswith('ㅇ'): out.append(('item', t.lstrip('ㅇ ').strip()))
        elif t.startswith('-'):  out.append(('sub',  t.lstrip('- ').strip()))
        elif t.startswith(('*','•')):  out.append(('note', t.lstrip('*• ').strip()))
        else:                    out.append(('text', t))
    return out

def blank_sizes(path):
    """빈 문단의 vertsize 분포 — 3pt(300) 관례 확인용"""
    xml=H.read_part(path); sizes={}
    for (_,_,p) in H.split_paras(xml):
        if H.ptext(p).strip() or '<hp:tbl' in p: continue
        m=re.search(r'vertsize="(\d+)"', p)
        if m: sizes[int(m.group(1))]=sizes.get(int(m.group(1)),0)+1
    return sizes

def W(s):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)

def line_fill(path):
    """문단별 줄 채움 상태 — (텍스트, 줄수, 마지막 줄 채움률)"""
    xml=H.read_part(path); out=[]
    for (_,_,p) in H.split_paras(xml):
        if '<hp:tbl' in p: continue
        t=H.ptext(p)
        if not t.strip(): continue
        i=p.rfind('<hp:linesegarray>')
        if i<0: continue
        j=p.find('</hp:linesegarray>', i)
        segs=re.findall(r'textpos="(\d+)"', p[i:j])
        n=len(segs)
        if n<2: continue
        pos=[int(x) for x in segs]+[len(t)]
        widths=[W(t[pos[k]:pos[k+1]]) for k in range(n)]
        full=max(widths[:-1]) if n>1 else widths[0]
        if full<=0: continue
        out.append((' '.join(t.split()), n, widths[-1]/full))
    return out

def unlabeled(ol):
    """추진내용 절의 라벨 문제 — 팀장 최종본(2026-09-22) 기준

    - ㅇ 항목은 (라벨)로 시작해야 한다.
    - - 항목은 한 ㅇ 아래에서 모두 라벨을 붙이거나 모두 떼야 한다(섞이면 문제).
      최종본은 ㅇ 에 따라 - 라벨을 붙이기도(실험 구성) 떼기도(짧은 풀이) 했다.
    개요·현황 절은 서술이 이어지므로 라벨 없이 쓰는 것이 정상이다.
    """
    out=[]; inside=False; group=[]
    def flush():
        if group:
            has=[t for t in group if t.lstrip(' -').strip().startswith('(')]
            if has and len(has)!=len(group):
                out.extend(('sub', t) for t in group if t not in has)
        group.clear()
    for kind, t in ol:
        if kind=='sec':
            flush(); inside = match(t, ACTION_KEY); continue
        if not inside: continue
        if kind=='item':
            flush()
            body=t.lstrip(' \u3147\u25cb\u3007-\u2022').strip()
            if body and not body.startswith('('): out.append((kind, t))
        elif kind=='sub':
            group.append(t)
    flush()
    return out

def section_items(ol):
    """절 이름 -> 그 절에 속한 ㅇ 항목 목록"""
    cur=None; d={}
    for kind,t in ol:
        if kind=='sec': cur=t; d.setdefault(cur, [])
        elif kind=='item' and cur is not None: d[cur].append(t)
    return d

def match(name, keys): return any(k in name for k in keys)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('--style', choices=['A','B'], default=None)
    ap.add_argument('--json', action='store_true')
    a=ap.parse_args()
    ol=outline(a.file); si=section_items(ol)
    secs=[t for k,t in ol if k=='sec']
    findings=[]

    # 1) 양식 추정
    style=a.style
    if style is None:
        style='A' if any('목차' in s for s in secs) else 'B'

    # 2) 절 구성
    need = SEC_A if style=='A' else SEC_B
    missing=[k for k in ('기대효과','향후계획') if not any(k in s for s in secs)]
    if missing and style=='A':
        findings.append(('warn','절 누락', f"양식 A인데 {', '.join(missing)} 절이 보이지 않습니다"))
    elif missing and style=='B':
        findings.append(('info','절 통합', f"{', '.join(missing)}가 별도 절로 없습니다 — 추진내용에 녹였다면 정상"))

    # 3) 문제점 ↔ 추진내용 ↔ 기대효과 개수
    def count(keys):
        n=0
        for s,items in si.items():
            if match(s, keys): n+=len(items)
        return n
    np_, na, ne = count(PROBLEM_KEY), count(ACTION_KEY), count(EFFECT_KEY)
    # 문제점 절이 따로 없으면 '현황 및 문제점' 절의 항목으로 본다
    if np_==0:
        for s,items in si.items():
            if '현황' in s and '문제' in s: np_=len(items)
    if np_ and na and na < np_:
        findings.append(('error','개수 역전',
            f"문제점 {np_}개 > 추진내용 {na}개 — 답하지 않은 문제가 남습니다"))
    elif np_ and na:
        findings.append(('ok','개수 대응', f"문제점 {np_} → 추진내용 {na}"))

    # 4) 개요 충실도
    ov=None
    for s,items in si.items():
        if '개요' in s or '배경' in s: ov=(s,items); break
    if ov is None:
        findings.append(('error','개요 없음','개요(또는 배경) 절을 찾지 못했습니다'))
    else:
        s,items=ov
        if len(items)<2:
            findings.append(('warn','개요 빈약',
                f"「{s}」 항목이 {len(items)}개 — 배경과 목적이 모두 담겼는지 확인하세요"))
        else:
            findings.append(('ok','개요', f"「{s}」 항목 {len(items)}개"))

    # 5) 줄 채움 (Alt+Shift+N 자간 조정 / 문장 보강 대상)
    short=[]; nearly=[]
    for t,n,fill in line_fill(a.file):
        if fill < 0.15: nearly.append((t,n,fill))
        elif fill < 0.5: short.append((t,n,fill))
    if nearly:
        findings.append(('warn','한 줄로 줄일 여지',
            f"{len(nearly)}개 문단의 마지막 줄이 15% 미만 — 자간(Alt+Shift+N)으로 한 줄에 넣을 수 있습니다"))
    if short:
        findings.append(('warn','줄 채움 부족',
            f"{len(short)}개 문단의 마지막 줄이 절반 미만 — 문장을 보강해 줄을 채우세요"))
    if not nearly and not short:
        findings.append(('ok','줄 채움','마지막 줄이 절반 미만인 문단 없음'))

    # 6) 라벨 없는 항목
    ul=unlabeled(ol)
    if ul:
        findings.append(('warn','라벨 없는 항목',
            f"추진내용 절의 {len(ul)}개 항목 — ㅇ 에 (라벨)이 없거나, 한 ㅇ 아래 - 라벨이 섞여 있습니다"))
    else:
        findings.append(('ok','항목 라벨','추진내용 절의 ㅇ 라벨과 - 라벨 통일 상태 양호'))

    # 7) 문단 간격
    bs=blank_sizes(a.file)
    if bs:
        top=sorted(bs.items(), key=lambda x:-x[1])[0]
        if top[0]!=300:
            findings.append(('warn','문단 간격',
                f"가장 많은 빈 문단이 {top[0]}({top[0]/100:.0f}pt) — 관례는 300(3pt)"))
        else:
            findings.append(('ok','문단 간격', f"3pt 빈 문단 {top[1]}개"))

    if a.json:
        print(json.dumps({'style':style,'sections':secs,
                          'counts':{'problem':np_,'action':na,'effect':ne},
                          'blank_sizes':bs,
                          'unlabeled':[t for _,t in ul],
                          'line_fill':{'nearly_one_line':[{'text':t,'fill':round(f,3)} for t,_,f in nearly],
                                       'underfilled':[{'text':t,'fill':round(f,3)} for t,_,f in short]},
                          'findings':[{'level':l,'title':t,'detail':d} for l,t,d in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print(f"양식 추정: {style}   절 {len(secs)}개")
        for s in secs: print(f"  □ {s}")
        print()
        sym={'ok':'OK  ','info':'INFO','warn':'주의','error':'오류'}
        for l,t,d in findings: print(f"[{sym[l]}] {t}: {d}")
        if nearly or short:
            print()
            for t,n,f in nearly[:8]: print(f"  [한 줄 가능 {f*100:4.0f}%] {t[:62]}")
            for t,n,f in short[:8]:  print(f"  [채움 부족  {f*100:4.0f}%] {t[:62]}")
        if ul:
            print()
            for k,t in ul[:8]: print(f"  [라벨 없음] {t[:64]}")
    return 2 if any(l=='error' for l,_,_ in findings) else 0

if __name__=='__main__':
    sys.exit(main())
