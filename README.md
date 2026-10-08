# hwpxSkill — Claude Code 스킬 모음

업무에 쓰는 Claude Code 스킬을 모아 두는 저장소입니다. 스킬마다 폴더 하나이고, 필요한 것만 골라 설치합니다.

| 스킬 | 하는 일 | 주로 쓰는 요청 |
|---|---|---|
| [`team-report-hwpx`](team-report-hwpx/) | 팀장 최종본 양식의 한글(HWPX) 업무보고서 생성·점검 | 「보고서 작성해줘」, 「보고서 양식 점검」 |
| [`dark-seminar-deck`](dark-seminar-deck/) | 다크 테크 양식 세미나 발표자료(HTML → 이미지 PDF, 선택 PPTX) | 「발표자료 만들어줘」, 「세미나 자료 이 양식으로」 |

## 설치

```bash
git clone https://github.com/Johwiwon/hwpxSkill.git

# 내 모든 프로젝트에서 사용: 원하는 스킬 폴더를 복사
cp -r hwpxSkill/<스킬 이름> ~/.claude/skills/

# 또는 특정 프로젝트에서만 사용 (프로젝트 루트에서)
mkdir -p .claude/skills && cp -r hwpxSkill/<스킬 이름> .claude/skills/
```

Windows에서는 `~/.claude/skills/` 가 `C:\Users\<사용자>\.claude\skills\` 입니다.
설치 후 Claude Code를 다시 열면 스킬이 쓰입니다. 저장소를 업데이트한 뒤에는 같은 방법으로 다시 복사합니다.

## 스킬 추가 규칙

- 스킬 하나 = 최상위 폴더 하나(`<스킬 이름>/SKILL.md` 필수). 위 표에 한 줄, 아래에 절 하나를 추가합니다.
- 내부 원본 문서·실제 업무 자료는 올리지 않습니다(필요하면 `.gitignore` 에 추가).
- 외부 코드·글꼴을 넣으면 라이선스 파일을 함께 넣고 맨 아래 "포함된 외부 코드"에 적습니다.

---

## team-report-hwpx — 팀장 최종본 양식 한글 보고서

한글(HWPX) 업무보고서를 팀장이 고친 최종본(2026-09-22) 양식대로 쓰는 스킬입니다. 스킬 하나로 다음을 모두 합니다.

| 단계 | 하는 일 |
|---|---|
| 내용 설계 | 양식 A/B 선택, 문제점↔추진 내용 대응표, 문장 규칙 |
| 생성 | 제목 상자·□ ㅇ - * 기호·글꼴·크기·자간·간격·표·캡션·그림·붙임 띠까지 최종본과 같은 HWPX |
| 줄 맞춤 | 어중간하게 넘어가는 문단의 자간을 자동으로 좁힘(최종본 실제 줄바꿈으로 맞춘 글자 폭 모델) |
| 점검 | 양식(글꼴·기호·줄 채움), 구조(절 구성·개수 대응·라벨) |
| 배포 전 검사 | 패키지·XML·참조·표 구조 |
| 기존 문서 | HWP 읽기용 사본 만들기, 쪽별 미리보기 |

기준 보고서 원본은 이 저장소에 포함하지 않습니다. 모든 기능은 원본 없이 동작합니다.

### 설치

```bash
cp -r hwpxSkill/team-report-hwpx ~/.claude/skills/
```

설치 후 「보고서 작성해줘」 같은 요청에 스킬이 쓰입니다.

### 필요한 것

| 항목 | 용도 | 필수 |
|---|---|---|
| Python 3.9+ | 생성·점검·검사 (표준 라이브러리만 사용, 추가 설치 없음) | 필수 |
| 한글(한컴오피스) + 글꼴 HY헤드라인M·휴먼명조·함초롬돋움 | 결과 파일 열람 | 필수 |
| Node.js 18+ | HWP 읽기(`read_hwp.mjs`), 미리보기(`render_svg.mjs`) | 선택 |

### 직접 실행

```bash
cd team-report-hwpx
python3 scripts/plan_flow.py --problems 3                         # 대응표 틀
python3 scripts/build_report.py examples/sample.txt sample.hwpx   # 생성
python3 scripts/inspect_report.py sample.hwpx                     # 양식 점검
python3 scripts/check_report.py sample.hwpx                       # 구조 점검
python3 scripts/check_hwpx.py sample.hwpx                         # 배포 전 검사
node scripts/read_hwp.mjs 기존.hwp 사본.hwpx                       # HWP 읽기용 사본
```

입력 문법은 `references/input-format.md`, 양식 수치는 `references/format-spec.md`,
구성·문장 규칙은 `references/structure.md`·`flow.md`·`writing-rules.md`·`writing-style.md` 를 봅니다.

---

## dark-seminar-deck — 다크 테크 양식 세미나 발표자료

한국어 세미나 발표자료를 정해진 다크 테크 양식(1920×1080, 남색 배경, Pretendard, 카드·칩 강조)으로
만들어 이미지 PDF로 내보내는 Claude Code 스킬입니다. 필요하면 같은 화면의 PPTX(발표자 노트 포함)도 만듭니다.

| 단계 | 하는 일 |
|---|---|
| 덱 만들기 | 부품 13종(표지, 사례 카드, 방식 비교, 처리 흐름, 원칙 카드, 평가 설계, 비교 수치 카드, 막대 차트, 해석 카드, 담당 표시 단계, 현상·위험·대응, 정리, 감사합니다)이 든 견본 덱 생성 |
| 장 구성 | 견본 장 고르기·복제·순서 바꾸기(`slides.py`) |
| 빌드 | 아이콘(lucide)·막대 차트·쪽 번호를 채워 `index.html` 생성 |
| 내보내기 | 헤드리스 크롬으로 캡처 → 이미지 PDF(실제 쪽수 자동 확인), 선택 PPTX |
| 문구 | 결론형 장 제목, 숫자 표기, 측정하지 않은 효과 주장 금지 등 작성 원칙 |

### 설치

```bash
cp -r hwpxSkill/dark-seminar-deck ~/.claude/skills/
```

설치 후 Claude Code를 다시 열면 「발표자료 만들어줘」, 「세미나 자료 이 양식으로」 같은 요청에 스킬이 쓰입니다.
발표 제목·발표자·주관(소속)은 스킬에 들어 있지 않고, 덱을 만들 때마다 사용자에게 묻습니다.

### 필요한 것

| 항목 | 용도 | 필수 |
|---|---|---|
| Google Chrome | 슬라이드 캡처, PDF 묶기 (WSL에서는 윈도 크롬을 자동으로 찾음) | 필수 |
| Node.js 18+ | 빌드, PPTX | 필수 |
| npm | 아이콘 패키지 `lucide-static`, PPTX용 `pptxgenjs` 를 처음 한 번 `~/.cache/dark-seminar-deck` 에 설치 | 필수 |
| Python 3 | 장 고르기, PDF 쪽수 확인, PPTX 노트 정리 | 필수 |

### 직접 실행

```bash
SK=~/.claude/skills/dark-seminar-deck
bash $SK/scripts/new_deck.sh my-deck                              # 견본 덱 생성
python3 $SK/scripts/slides.py my-deck/_build/src.html list       # 장 목록
python3 $SK/scripts/slides.py my-deck/_build/src.html keep 1,2,7,12,13
python3 $SK/scripts/slides.py my-deck/_build/src.html check    # 남은 자리표시(발표 제목·이름·부서 등) 검사
node my-deck/_build/build.mjs                                     # 빌드
bash $SK/scripts/shots.sh my-deck shots                           # 캡처 (1.5배)
bash $SK/scripts/pdf.sh shots my-deck.pdf                         # 이미지 PDF
bash $SK/scripts/pptx.sh shots my-deck.pptx notes.json            # 선택: PPTX
```

부품 목록은 `references/components.md`, 문구 원칙은 `references/writing-rules.md`,
문제 해결은 `references/troubleshooting.md` 를 봅니다.

---

## 포함된 외부 코드

- `vendor/rhwp/` — rhwp HWP 렌더러 WASM, MIT License (Copyright (c) 2025-2026 Edward Kim). `vendor/rhwp/LICENSE` 참고.
- `dark-seminar-deck/assets/template/fonts/PretendardVariable.woff2` — Pretendard 글꼴, SIL Open Font License 1.1 (Copyright (c) 2021, Kil Hyung-jin). 같은 폴더의 `LICENSE-Pretendard.txt` 참고.
- 아이콘 `lucide-static`(ISC)과 `pptxgenjs`(MIT)는 저장소에 넣지 않고 처음 실행할 때 npm으로 설치합니다.
