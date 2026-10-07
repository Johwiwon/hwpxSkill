# -*- coding: utf-8 -*-
"""부서 글꼴 규칙을 기존 HWPX에 적용한다.

  □ 절 제목        HY헤드라인M
  ㅇ · - 본문      휴먼명조
  * 표 하단 설명   함초롬돋움   (팀장 최종본 2026-09-22 기준. 이전 규칙의 휴먼고딕은 폐기)
  표 안 내용       함초롬돋움

글꼴만 바꾼다. 크기(표 12pt·주석 13pt)와 • → * 기호 교체는
inspect_report.py 로 점검한 뒤 고친다.

charPr 의 fontRef 만 바꾸므로 본문 텍스트는 건드리지 않는다.

    python3 apply_fonts.py 보고서.hwpx                 # 제자리 수정
    python3 apply_fonts.py 보고서.hwpx -o 새파일.hwpx
    python3 apply_fonts.py 보고서.hwpx --dry-run       # 어떤 charPr 이 바뀔지만 출력
"""
import sys, os, re, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hwpxlib as H

FONTS={'HY헤드라인M':'FCAT_GOTHIC', '휴먼명조':'FCAT_MYUNGJO', '함초롬돋움':'FCAT_GOTHIC'}
ROLE_FONT={'sec':'HY헤드라인M', 'body':'휴먼명조', 'note':'함초롬돋움', 'cell':'함초롬돋움'}

def ensure_fonts(hdr):
    """모든 언어 그룹에 글꼴을 등록하고 {글꼴이름: id} 반환"""
    groups=list(re.finditer(r'<hh:fontface\b[^>]*>.*?</hh:fontface>', hdr, re.S))
    if not groups: raise SystemExit('fontface 그룹을 찾지 못했습니다')
    ids={}
    # 기존에 이미 있으면 그 id 사용
    for name in FONTS:
        m=re.search(r'<hh:font id="(\d+)" face="%s"'%re.escape(name), hdr)
        if m: ids[name]=m.group(1)
    need=[n for n in FONTS if n not in ids]
    if not need: return hdr, ids
    maxid=max(int(m.group(1)) for m in re.finditer(r'<hh:font id="(\d+)"', hdr))
    for i,name in enumerate(need): ids[name]=str(maxid+1+i)
    # 뒤쪽 그룹부터 삽입해야 앞 그룹의 오프셋이 밀리지 않는다
    for g in reversed(groups):
        blk=g.group(0)
        cnt=int(re.search(r'itemCnt="(\d+)"', blk).group(1))
        add=''.join(
            f'<hh:font id="{ids[n]}" face="{n}" type="TTF" isEmbedded="0">'
            f'<hh:typeInfo familyType="{FONTS[n]}" weight="0" proportion="0" contrast="0" '
            f'strokeVariation="0" armStyle="0" letterform="0" midline="0" xHeight="0"/></hh:font>'
            for n in need)
        nb=blk.replace('</hh:fontface>', add+'</hh:fontface>', 1)
        nb=re.sub(r'itemCnt="\d+"', 'itemCnt="%d"'%(cnt+len(need)), nb, count=1)
        hdr=hdr[:g.start()]+nb+hdr[g.end():]
    return hdr, ids

def charpr_roles(path):
    """본문을 훑어 charPr id 마다 어떤 역할로 쓰이는지 판정"""
    xml=H.read_part(path); roles={}
    def note(cid, role):
        roles.setdefault(cid, set()).add(role)
    for (_,_,p) in H.split_paras(xml):
        if '<hp:tbl' in p:
            for tc in re.finditer(r'<hp:tc\b.*?</hp:tc>', p, re.S):
                for m in re.finditer(r'charPrIDRef="(\d+)"', tc.group(0)): note(m.group(1),'cell')
            continue
        t=' '.join(H.ptext(p).split())
        if not t: continue
        role='sec' if t.startswith('□') else 'note' if t.startswith(('*','•')) else \
             'body' if (t.startswith('ㅇ') or t.startswith('-')) else None
        if role is None: continue
        for m in re.finditer(r'<hp:run charPrIDRef="(\d+)"', p): note(m.group(1), role)
    return roles

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('-o','--output')
    ap.add_argument('--dry-run', action='store_true')
    a=ap.parse_args()
    dst=a.output or a.file
    hdr=H.read_part(a.file,'Contents/header.xml')
    roles=charpr_roles(a.file)

    plan=[]
    for cid, rs in sorted(roles.items(), key=lambda x:int(x[0])):
        if len(rs)>1:
            plan.append((cid, None, f'역할 혼용 {sorted(rs)} — 수동 확인 필요'))
            continue
        r=next(iter(rs)); plan.append((cid, ROLE_FONT[r], r))

    if a.dry_run:
        for cid,f,r in plan: print(f'  charPr {cid:>3} → {f or "(건너뜀)":10} [{r}]')
        return 0

    hdr, ids = ensure_fonts(hdr)
    changed=0
    for cid,f,r in plan:
        if not f: continue
        fid=ids[f]
        m=re.search(r'<hh:charPr id="%s" .*?</hh:charPr>'%cid, hdr, re.S)
        if not m: continue
        blk=m.group(0)
        nb=re.sub(r'<hh:fontRef\b[^>]*/>',
                  f'<hh:fontRef hangul="{fid}" latin="{fid}" hanja="{fid}" japanese="{fid}" '
                  f'other="{fid}" symbol="{fid}" user="{fid}"/>', blk, count=1)
        if nb!=blk: hdr=hdr[:m.start()]+nb+hdr[m.end():]; changed+=1
    H.zip_swap(a.file, dst, {'Contents/header.xml':hdr})
    print(f'글꼴 적용 완료: charPr {changed}개 변경 → {dst}')
    skipped=[c for c,f,_ in plan if not f]
    if skipped: print('  역할이 섞여 건너뛴 charPr:', ', '.join(skipped))
    print('  ※ 적용 후 한글에서 열어 글꼴이 실제로 설치되어 있는지 확인하세요.')
    return 0

if __name__=='__main__':
    sys.exit(main())
