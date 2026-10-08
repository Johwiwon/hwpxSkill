# pptxgenjs가 발표자 노트의 줄바꿈을 한 문단 안에 그대로 넣는 문제를 고친다: 줄마다 <a:p> 문단으로 나눈다.
# usage: python3 fixnotes.py <in.pptx> <out.pptx>
import re
import sys
import zipfile
from xml.sax.saxutils import escape, unescape

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
zout = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
pat = re.compile(r'<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>(.*?)</a:t></a:r><a:endParaRPr lang="en-US" dirty="0"/></a:p>', re.S)


def split(m):
    out = []
    for ln in re.split(r'\r?\n', unescape(m.group(1))):
        if ln.strip():
            out.append(f'<a:p><a:r><a:rPr lang="ko-KR" altLang="en-US" dirty="0"/><a:t>{escape(ln)}</a:t></a:r></a:p>')
        else:
            out.append('<a:p><a:endParaRPr lang="ko-KR" altLang="en-US" dirty="0"/></a:p>')
    return ''.join(out)


for item in zin.infolist():
    data = zin.read(item.filename)
    if re.match(r'ppt/notesSlides/notesSlide\d+\.xml', item.filename):
        data = pat.sub(split, data.decode('utf8'), count=1).encode('utf8')
    zout.writestr(item, data)
zout.close()
