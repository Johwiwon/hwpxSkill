# -*- coding: utf-8 -*-
"""HWPX 최소 조작 유틸 (표준 라이브러리만 사용)"""
import zipfile, re, os

def read_part(path, part='Contents/section0.xml'):
    with zipfile.ZipFile(path) as z:
        return z.read(part).decode('utf-8')

def parts(path):
    with zipfile.ZipFile(path) as z:
        return z.namelist()

def split_paras(xml):
    """최상위 <hp:p> 만 (start, end, xml) 로 분할 (표 안 중첩 문단은 제외)"""
    out=[]; depth=0; start=None
    for m in re.finditer(r'<hp:p(?:\s[^>]*?)?(/?)>|</hp:p>', xml):
        tag=m.group(0)
        if tag.startswith('</'):
            depth-=1
            if depth==0:
                out.append((start, m.end(), xml[start:m.end()])); start=None
        else:
            if m.group(1)=='/':
                if depth==0: out.append((m.start(), m.end(), tag))
                continue
            if depth==0: start=m.start()
            depth+=1
    return out

def ptext(p):
    t=''.join(re.sub(r'<[^>]+>','',x) for x in re.findall(r'<hp:t>(.*?)</hp:t>', p, flags=re.S))
    return (t.replace('&lt;','<').replace('&gt;','>')
             .replace('&amp;','&').replace('&quot;','"'))

def zip_swap(src, dst, newparts):
    """newparts: {부품이름: 새 텍스트}. mimetype 은 반드시 무압축으로 보존."""
    tmp=str(dst)+'.tmp'
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            data=zin.read(it.filename)
            if it.filename in newparts:
                data=newparts[it.filename].encode('utf-8')
            if it.filename=='mimetype':
                zout.writestr(it, data, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(it, data)
    os.replace(tmp, dst)

def preview_text(xml, limit=1500):
    """Preview/PrvText.txt 재생성용"""
    out=[]
    for (_,_,pp) in split_paras(xml):
        if '<hp:tbl' in pp:
            cells=[' '.join(ptext(m.group()).split())
                   for m in re.finditer(r'<hp:tc\b.*?</hp:tc>', pp, re.S)]
            out.append(''.join('<%s>'%c for c in cells))
        else:
            out.append(' '.join(ptext(pp).split()))
    return '\r\n'.join(out)[:limit]
