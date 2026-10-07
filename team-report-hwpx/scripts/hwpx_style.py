"""header.xml 의 글자모양(charPr)·문단모양(paraPr)·테두리(borderFill)를
속성으로 찾고, 없으면 기존 항목을 복제해 새로 만든다.

팀장 최종본의 header.xml 을 그대로 쓰므로, 같은 속성의 항목이 이미 있으면
그 id 를 재사용한다. 자간을 문단마다 다르게 주어도 다른 문단과 charPr 을
공유하지 않도록 (글꼴, 크기, 자간, 굵기, 색) 조합마다 별도 id 를 둔다.
"""
import re

LANGS = ('hangul', 'latin', 'hanja', 'japanese', 'other', 'symbol', 'user')
LANG_TAGS = ('HANGUL', 'LATIN', 'HANJA', 'JAPANESE', 'OTHER', 'SYMBOL', 'USER')


class HeaderStyles:
    def __init__(self, header_xml: str):
        self.xml = header_xml
        self._font_ids = self._parse_fonts()
        self._char_cache = {}
        self._para_cache = {}
        self._bf_cache = {}

    # ------------------------------------------------------------------ fonts
    def _parse_fonts(self):
        ids = {}
        for m in re.finditer(r'<hh:fontface lang="(\w+)" fontCnt="\d+">(.*?)</hh:fontface>', self.xml, re.S):
            ids[m.group(1)] = {f.group(2): f.group(1) for f in re.finditer(r'<hh:font id="(\d+)" face="([^"]+)"', m.group(2))}
        return ids

    def font_id(self, lang_tag: str, face: str) -> str:
        table = self._font_ids[lang_tag]
        if face in table:
            return table[face]
        # 해당 언어 목록에 글꼴이 없으면 HANGUL 목록의 정의를 복사해 추가한다.
        src = re.search(r'<hh:font id="\d+" face="%s".*?</hh:font>' % re.escape(face), self.xml, re.S)
        if not src:
            raise ValueError(f'글꼴 정의를 찾을 수 없음: {face}')
        new_id = str(len(table))
        block = re.search(r'(<hh:fontface lang="%s" fontCnt=")(\d+)(">)(.*?)(</hh:fontface>)' % lang_tag, self.xml, re.S)
        font_xml = re.sub(r'id="\d+"', f'id="{new_id}"', src.group(0), count=1)
        new_block = f'{block.group(1)}{int(block.group(2)) + 1}{block.group(3)}{block.group(4)}{font_xml}{block.group(5)}'
        self.xml = self.xml[:block.start()] + new_block + self.xml[block.end():]
        table[face] = new_id
        return new_id

    # ------------------------------------------------------------- utilities
    def _items(self, tag):
        return [(m.group(1), m.group(0)) for m in re.finditer(r'<hh:%s id="(\d+)".*?</hh:%s>' % (tag, tag), self.xml, re.S)]

    def _append(self, container, tag, item_xml_fn):
        items = self._items(tag)
        new_id = str(max(int(i) for i, _ in items) + 1)
        item = item_xml_fn(new_id)
        close = f'</hh:{container}>'
        pos = self.xml.index(close)
        self.xml = self.xml[:pos] + item + self.xml[pos:]
        self.xml = re.sub(r'(<hh:%s itemCnt=")(\d+)(")' % container,
                          lambda m: f'{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}', self.xml, count=1)
        return new_id

    # -------------------------------------------------------------- charPr
    def _char_key(self, xml):
        g = lambda pat: re.search(pat, xml).group(1)
        face_id = g(r'<hh:fontRef hangul="(\d+)"')
        face = next(f for f, i in self._font_ids['HANGUL'].items() if i == face_id)
        ul = re.search(r'<hh:underline type="(\w+)"', xml)
        return (face, int(g(r'height="(\d+)"')), int(g(r'<hh:spacing hangul="(-?\d+)"')),
                int(g(r'<hh:ratio hangul="(\d+)"')), '<hh:bold/>' in xml, g(r'textColor="(#\w+)"').upper(),
                '<hh:italic/>' in xml, (ul.group(1) if ul else 'NONE'), 'strikeout shape="NONE"' in xml or 'strikeout' not in xml)

    def char(self, face, size_pt, spacing=0, bold=False, color='#000000', ratio=100):
        """charPr id. size_pt 는 pt 단위(소수 허용), spacing 은 자간(%)."""
        height = int(round(size_pt * 100))
        key = (face, height, int(spacing), int(ratio), bool(bold), color.upper())
        if key in self._char_cache:
            return self._char_cache[key]
        for cid, xml in self._items('charPr'):
            k = self._char_key(xml)
            if k[:6] == key and not k[6] and k[7] == 'NONE' and k[8] and 'emboss' not in xml:
                self._char_cache[key] = cid
                return cid
        # 같은 글꼴의 평범한 항목을 골라 복제한다.
        base = None
        for cid, xml in self._items('charPr'):
            k = self._char_key(xml)
            if k[0] == face and not k[6] and k[7] == 'NONE' and k[8] and 'emboss' not in xml:
                base = xml
                break
        if base is None:
            base = next(xml for _, xml in self._items('charPr') if 'emboss' not in xml)
        fids = {lang: self.font_id(tag, face) for lang, tag in zip(LANGS, LANG_TAGS)}

        def build(new_id):
            x = re.sub(r'<hh:charPr id="\d+"', f'<hh:charPr id="{new_id}"', base, count=1)
            x = re.sub(r'height="\d+"', f'height="{height}"', x, count=1)
            x = re.sub(r'textColor="#\w+"', f'textColor="{color.upper()}"', x, count=1)
            x = re.sub(r'<hh:fontRef [^>]*/>', '<hh:fontRef ' + ' '.join(f'{l}="{fids[l]}"' for l in LANGS) + '/>', x)
            x = re.sub(r'<hh:ratio [^>]*/>', '<hh:ratio ' + ' '.join(f'{l}="{ratio}"' for l in LANGS) + '/>', x)
            x = re.sub(r'<hh:spacing [^>]*/>', '<hh:spacing ' + ' '.join(f'{l}="{int(spacing)}"' for l in LANGS) + '/>', x)
            x = x.replace('<hh:bold/>', '')
            if bold:
                x = x.replace('<hh:underline', '<hh:bold/><hh:underline', 1)
            return x

        cid = self._append('charProperties', 'charPr', build)
        self._char_cache[key] = cid
        return cid

    # -------------------------------------------------------------- paraPr
    def para(self, align='JUSTIFY', intent=0, left=0, right=0, line=160, keep_word=True):
        """paraPr id. intent<0 이면 내어쓰기(HWPUNIT)."""
        key = (align, int(intent), int(left), int(right), int(line), keep_word)
        if key in self._para_cache:
            return self._para_cache[key]
        word = 'KEEP_WORD' if keep_word else 'BREAK_WORD'
        for pid, xml in self._items('paraPr'):
            case = re.search(r'<hp:case.*?</hp:case>', xml, re.S)
            src = case.group(0) if case else xml
            vals = dict(re.findall(r'<hc:(intent|left|right|prev|next) value="(-?\d+)"', src))
            ls = re.search(r'<hh:lineSpacing type="PERCENT" value="(\d+)"', src)
            if (re.search(r'horizontal="(\w+)"', xml).group(1) == align and int(vals.get('intent', 0)) == key[1]
                    and int(vals.get('left', 0)) == key[2] and int(vals.get('right', 0)) == key[3]
                    and int(vals.get('prev', 0)) == 0 and int(vals.get('next', 0)) == 0
                    and ls and int(ls.group(1)) == key[4] and f'breakNonLatinWord="{word}"' in xml
                    and 'heading type="NONE"' in xml and 'borderFillIDRef="2"' in xml):
                self._para_cache[key] = pid
                return pid
        base = next(xml for _, xml in self._items('paraPr') if 'heading type="NONE"' in xml and '<hp:switch>' in xml)

        def margin(scale):
            return (f'<hh:margin><hc:intent value="{int(intent) * scale}" unit="HWPUNIT"/>'
                    f'<hc:left value="{int(left) * scale}" unit="HWPUNIT"/>'
                    f'<hc:right value="{int(right) * scale}" unit="HWPUNIT"/>'
                    f'<hc:prev value="0" unit="HWPUNIT"/><hc:next value="0" unit="HWPUNIT"/></hh:margin>'
                    f'<hh:lineSpacing type="PERCENT" value="{int(line)}" unit="HWPUNIT"/>')

        def build(new_id):
            x = re.sub(r'<hh:paraPr id="\d+"', f'<hh:paraPr id="{new_id}"', base, count=1)
            x = re.sub(r'horizontal="\w+"', f'horizontal="{align}"', x, count=1)
            x = re.sub(r'breakNonLatinWord="\w+"', f'breakNonLatinWord="{word}"', x, count=1)
            # 한글 2016+ 는 case(HwpUnitChar) 값을, 구버전은 default(2배 단위) 값을 읽는다.
            x = re.sub(r'(<hp:case [^>]*>).*?(</hp:case>)', lambda m: m.group(1) + margin(1) + m.group(2), x, flags=re.S)
            x = re.sub(r'(<hp:default>).*?(</hp:default>)', lambda m: m.group(1) + margin(2) + m.group(2), x, flags=re.S)
            x = re.sub(r'<hh:border borderFillIDRef="\d+"', '<hh:border borderFillIDRef="2"', x, count=1)
            return x

        pid = self._append('paraProperties', 'paraPr', build)
        self._para_cache[key] = pid
        return pid

    # ---------------------------------------------------------- borderFill
    def border_fill(self, line='SOLID', width='0.12 mm', fill=None, image_ref=None):
        """표 셀 테두리. fill 은 '#RRGGBB', image_ref 는 BinData 항목 id(셀 배경 그림)."""
        key = (line, width, (fill or '').upper(), image_ref)
        if key in self._bf_cache:
            return self._bf_cache[key]
        if image_ref is None:
            for bid, xml in self._items('borderFill'):
                sides = re.findall(r'<hh:(?:left|right|top|bottom)Border type="(\w+)" width="([^"]+)" color="(#\w+)"', xml)
                if len(sides) != 4 or any(s != (line, width, '#000000') for s in sides):
                    continue
                face = re.search(r'faceColor="(#\w+)"', xml)
                has_fill = face is not None and face.group(1).lower() != 'none'
                if 'gradation' in xml or 'imgBrush' in xml or 'slash type="NONE"' not in xml:
                    continue
                if (fill is None and not has_fill) or (fill and has_fill and face.group(1).upper() == fill.upper()):
                    self._bf_cache[key] = bid
                    return bid

        def build(new_id):
            sides = ''.join(f'<hh:{s}Border type="{line}" width="{width}" color="#000000"/>' for s in ('left', 'right', 'top', 'bottom'))
            brush = ''
            if fill:
                brush = f'<hc:fillBrush><hc:winBrush faceColor="{fill}" hatchColor="#000000" alpha="0"/></hc:fillBrush>'
            if image_ref:
                brush = (f'<hc:fillBrush><hc:imgBrush mode="TOTAL"><hc:img binaryItemIDRef="{image_ref}" bright="0" '
                         f'contrast="0" effect="REAL_PIC" alpha="0"/></hc:imgBrush></hc:fillBrush>')
            return (f'<hh:borderFill id="{new_id}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
                    '<hh:slash type="NONE" Crooked="0" isCounter="0"/><hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
                    f'{sides}<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>{brush}</hh:borderFill>')

        bid = self._append('borderFills', 'borderFill', build)
        self._bf_cache[key] = bid
        return bid
