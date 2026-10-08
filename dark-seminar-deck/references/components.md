# 부품(레이아웃) 목록

견본 덱 `assets/template/_build/src.html`에 부품마다 견본 슬라이드가 하나씩 들어 있다. 새 장을 만들 때는 가장 가까운 견본 슬라이드를 복사해서 글만 바꾸는 것이 가장 빠르고 안전하다.

## 모든 장에 공통인 틀

```html
<section class="slide">
  <div class="bg"></div><div class="progress" style="width:{{P}}"></div>
  <header class="sh">
    <div class="kicker"><span class="num">03</span>장 분류(짧게)</div>
    <h2>장 제목: 결론을 한 문장으로</h2>
  </header>
  <div class="body center"> … 부품 … </div>
  <footer class="sf"><span>발표 제목</span><span class="pg">{{N}}</span></footer>
</section>
```

- `{{P}}`(진행 막대), `{{N}}`(쪽 번호)은 빌드가 채운다. 직접 숫자를 쓰지 않는다.
- `.kicker .num`(장 번호 배지)은 손으로 적는다. 장을 넣거나 빼면 뒤쪽 배지를 다시 매긴다. 같은 주제의 연속 장(결과 → 해석)은 같은 번호를 써도 된다.
- 꼬리말 왼쪽에는 발표 제목을 넣는다. 제목이 바뀌면 모든 장의 꼬리말과 `<title>`을 함께 바꾼다.
- 본문 영역은 `top:256px ~ bottom:112px`(높이 약 712px)이다. `.body.center`는 내용을 세로 가운데에 놓는다. 차트처럼 높이를 꽉 채울 때는 `.body`만 쓴다.

## 부품

| 견본 | 부품 | 언제 쓰나 | 핵심 클래스 |
|---|---|---|---|
| 1 | 표지 | 첫 장 | `.slide.cover` `.wrap` `h1` `.sub` `.sub2` `.meta` / 오른쪽 장식 `.card.viz`(`{{WAVE}}` 파형) |
| 2 | 사례 카드 3개 + 핵심 띠 | 문제 제기, 배경 | `.cards3` `.pcard`(`.phd` `.ptitle` `.plbl` `.ptxt`) + `.card.glow.banner` |
| 3 | 방식 비교 3열 | 기술 동향, 대안 비교 | `.routes` `.route`(`.rno` `.rttl` `.rdiag` `.rex` `.pro` `.con` `.exl`, 고른 것 `.glow` + `.used`) + `.banner` |
| 4 | 처리 흐름 + 확인할 질문 | 시스템 구성, 실험 구성 | `.flow` `.node`(`.glow` 핵심, `.extra` 부가) `.arw` / `.zones` `.zone` / `.qhead` `.qrow` `.qcard` |
| 5 | 번호 원칙 카드 + 표 | 설계 원칙, 사례 표 | `.numcards` `.ncard`(`.nnum.grad` `.ntitle` `.ntext` `.nmini`) / `.tbl`(`--cols` 로 열 비율) |
| 6 | 조건 카드 2개 | 평가 설계, 실험 조건 | `.kvgrid` `.kvcard`(`.kvhd` `.kvt` `.kv` 의 `.k` 라벨/값 쌍) + `.notecard` |
| 7 | 비교 수치 카드 | 결과(조건별 지표) | `.metrics` `.mcard`(`.mhd` `.mlabel` `.mboxes` `.mbox` `.mval.ok/.mid/.no` `.verdict.ok/.mid`) + `.notecard` |
| 8 | 막대 차트 + 옆 카드 | 결과(반복·그룹 비교) | `.chartrow` `.chartcard`(`.ttl` `.legend` + `.plotbox`) `.sidecol` `.sidecard`(`.srow`) |
| 9 | 큰 카드 2개 + 연결 띠 | 해석, 대비 | `.twobig` `.bigcard`(`.tag` `.bv` `.bd` `.bc.ok/.go`) + `.card.glow.center-line` |
| 10 | 담당 표시 단계 + 하위 카드 | 방법, 절차 | `.steps` `.step`(`.who` 담당 배지, `.sn` 번호, `.hl` 강조) `.loopband`(되돌림) `.subrow` `.subcard`(`.code` `.ex`) |
| 11 | 현상 · 위험 · 대응 | 주의할 점, 한계 | `.risks` `.rh` `.risk`(`.w` `.y` `.f`) + `.center-line` |
| 12 | 답 띠 + 3열 정리 | 정리 | `.answer`(`.aq` 질문, `.aa` 답) `.cols3` `.scard`(`.shd`, `li` / `li.warn` / `li.next`) |
| 13 | 감사합니다 | 마지막 장 | `.slide.thanks` `.tw` `.big.grad` `.qa` |

## 부품 크기 맞추기

- **처리 흐름 노드 수:** `.flow` 는 `--flow`(노드·화살표 열), 아래 `.zones` 는 `--zones`(구간 열)로 맞춘다. 노드 3개라면 `style="--flow: 1fr 40px 1fr 40px 1.2fr"` 와 `style="--zones: 2fr 1.2fr"` 처럼 둘을 함께 바꾼다.
- **질문 카드 수:** `.qrow` 에 `style="--q:3"`. 카드 안 설명 문장은 `.qd`.
- **큰 카드 주의 변형:** 약점·주의를 말하는 큰 카드는 `.tag.mid` `.bv.mid` `.bc.mid`(주황). 틀림은 `.bv.no`.
- **표지 제목 길이:** 기본 112px 두 줄. 한 줄이 열 글자를 넘으면 세 줄로 나누거나 `style="font-size:104px"` 로 줄인다.

## 표지 장식 바꾸기

견본 표지 오른쪽 `.card.viz` 는 음성→번역 주제용(파형 `{{WAVE}}`, 시각 `.ts`, EN/KO `.tag2`)이다. 다른 주제면 "입력 하나 → 결과 두세 줄" 형태로 바꾼다.

```html
<div class="card viz">
  <div class="cap"><i data-icon="search"></i>검색 예시</div>
  <div class="vinput"><i data-icon="search"></i>휴가 신청</div>
  <div class="turn"><i data-icon="arrow-down"></i><span>같은 질문 · 두 방식</span></div>
  <div class="vrow"><span class="tag2">키워드</span><span class="bad"><i data-icon="circle-x"></i>'연차 사용' 문서를 놓침</span></div>
  <div class="vrow"><span class="tag2 on">의미</span><span class="good"><i data-icon="circle-check"></i>'연차 사용' 문서도 찾음</span></div>
</div>
```

장식에 실제 결과를 쓸 때는 본문의 수치·예시와 같은 내용이어야 한다.

## 색과 강조

- 색 변형 클래스: `.icbox` · `.chip` · `.who` 뒤에 붙인다. 기본(하늘) / `.v` 보라 / `.m` 초록 / `.a` 주황 / `.r` 빨강 / `.g` 회색.
- 의미를 고정해서 쓴다. 초록 = 좋음·확인됨, 주황 = 주의·손실, 빨강 = 틀림·위험, 보라 = 다음 단계·부가.
- 글자 강조: `.grad`(제목 속 핵심어, 한 장에 한두 곳), `.hl` `.hl-a` `.hl-m` `.hl-r`(본문 속 색 강조), `<b>`(카드 안 굵게).
- 카드 강조: `.glow`(한 장에서 가장 중요한 카드 하나), `.warnc`(경고 카드).
- 차트 계열색: `--sA`(파랑) `--sB`(주황) `--sC`(보라). 어두운 카드 위 대비를 검증한 값이라 다른 색으로 바꾸지 않는다.

## 아이콘

- `<i data-icon="이름"></i>` 로 쓰면 빌드가 lucide 아이콘 SVG로 바꾼다. 이름은 https://lucide.dev/icons 에서 확인한다.
- 없는 이름이면 빌드가 멈추고 이름을 알려 준다. 비슷한 이름으로 바꾼다.
- 자주 쓴 이름: `circle-check` `circle-alert` `circle-x` `info` `arrow-right` `chevron-right` `audio-lines` `languages` `file-text` `database` `book-open-check` `git-merge` `refresh-ccw` `shield-check` `flask-conical` `milestone` `message-circle-question`

## 막대 차트

```html
<div class="plotbox" data-chart='{"max":100,"step":25,"height":420,"barW":90,
  "groups":[{"cat":"1회","vals":[[78.6,"B"],[100,"A"]]},{"cat":"2회","vals":[[85.7,"B"],[100,"A"]]}]}'></div>
```

- `vals` 의 두 번째 값 `"A"/"B"/"C"`는 계열색이다. 막대 위에 값이 직접 적힌다.
- `"unit":"%"` 를 주면 값 뒤에 단위가 붙는다.
- 방식별로 막대가 하나씩이면 그룹마다 `vals` 에 값 하나만 넣는다. 이때 범례는 빼도 된다(아래 분류 이름으로 충분).
- 범례(`.legend`)의 색 순서를 막대 순서와 맞춘다.
- 작은 차이를 보여 주는 결과라면 절대값 막대보다 `.metrics`(차이 숫자 카드)가 잘 읽힌다.

## 표 `.tbl`

```html
<div class="tbl" style="--cols: 70px 1fr 1fr 170px">
  <div class="th"><span>번호</span><span>원문</span><span>결과</span><span></span></div>
  <div class="tr"><span>0</span><span>…</span><span class="bad">…</span><span class="mark bad"><i data-icon="circle-x"></i>틀림</span></div>
</div>
```

- 원문과 결과처럼 대조할 것은 한 줄에 나란히 놓는다. 칸을 따로 떼어 놓으면 청중이 짝을 맞추지 못한다.
