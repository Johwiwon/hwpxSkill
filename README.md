# hwpxSkill — 팀장 최종본 양식 한글 보고서 스킬

한글(HWPX) 업무보고서를 팀장이 고친 최종본(2026-09-22) 양식대로 쓰기 위한
Claude Code 스킬 세 개입니다. 셋을 함께 설치합니다.

| 스킬 | 맡는 일 |
|---|---|
| `team-report-hwpx` | 서식: 글꼴·크기·자간·간격·표·붙임 띠까지 최종본과 같은 HWPX 생성, 양식 점검 |
| `korean-report-format` | 내용: 절 구성(양식 A/B), 문제점↔추진 내용 대응, 문장 규칙, 구조 점검 |
| `hwpx-skill` (서브모듈) | 기반: 기존 HWPX 수정, HWP 읽기·변환, 배포 전 검사, 미리보기 렌더러 |

`hwpx-skill` 은 공개 오픈소스([jkf87/hwpx-skill](https://github.com/jkf87/hwpx-skill))라
코드를 복사하지 않고 서브모듈로 연결했습니다. 검증을 마친 **v1.8.0**에 고정되어 있습니다.

`team-report-hwpx` 의 생성·점검은 단독으로도 동작하지만, 무엇을 어떤 순서로 쓸지는
`korean-report-format` 이 잡으므로 함께 있어야 보고서 작성 전 과정이 같은 기준으로 돌아갑니다.

## team-report-hwpx 기능

- 제목 상자·작성일 줄·□ ㅇ - * 기호·글꼴·크기·장평·간격·표·캡션·그림·붙임 띠를 최종본과 같게 생성
- 어중간하게 넘어가는 문단은 자간을 자동으로 좁혀 줄을 맞춤(최종본 실제 줄바꿈으로 맞춘 글자 폭 모델)
- 기존 HWPX의 글꼴·기호·줄 채움 점검

기준 보고서 원본은 이 저장소에 포함하지 않습니다. 생성·점검은 원본 없이 동작합니다.

## 설치

반드시 `--recurse-submodules` 로 받습니다(빠뜨리면 `hwpx-skill` 폴더가 빈 채로 옵니다).

```bash
git clone --recurse-submodules https://github.com/Johwiwon/hwpxSkill.git
# 이미 받았다면: git submodule update --init

# 내 모든 프로젝트에서 사용
cp -r hwpxSkill/team-report-hwpx hwpxSkill/korean-report-format hwpxSkill/hwpx-skill ~/.claude/skills/

# 검사 도구용 파이썬 패키지
pip install python-hwpx lxml
```

- 폴더 이름은 그대로 둡니다. 특히 `hwpx-skill` 은 미리보기 스크립트가 `~/.claude/skills/hwpx-skill` 경로로 찾습니다.
- 회사 PC에서 `pip install` 이 막혀 있으면(외부 관리 환경) `pip install --user` 나 가상환경을 씁니다.

Windows에서는 `~/.claude/skills/` 가 `C:\Users\<사용자>\.claude\skills\` 입니다.
설치 후 Claude Code를 다시 열면 「보고서 작성해줘」 같은 요청에 스킬이 쓰입니다.

## 필요한 것

| 항목 | 용도 | 필수 |
|---|---|---|
| Python 3.9+ | 생성·점검 스크립트(표준 라이브러리만 사용) | 필수 |
| 한글(한컴오피스) + 글꼴 HY헤드라인M·휴먼명조·함초롬돋움 | 결과 파일 열람 | 필수 |
| `hwpx-skill` + `python-hwpx`·`lxml` | 기존 HWPX 수정, 배포 전 검사 | 권장 |
| Node.js 18+ | HWP 읽기·변환, 미리보기(`render_svg.mjs`) | 권장 |

## 직접 실행

```bash
cd team-report-hwpx
python3 scripts/build_report.py examples/sample.txt sample.hwpx   # 생성
python3 scripts/inspect_report.py sample.hwpx                     # 양식 점검
```

입력 문법은 `team-report-hwpx/references/input-format.md`, 양식 수치는
`references/format-spec.md`, 문장 쓰는 법은 `references/writing-style.md` 를 봅니다.

korean-report-format 도구:

```bash
python3 korean-report-format/scripts/plan_flow.py --problems 3        # 문제점↔추진 내용 대응표 틀
python3 korean-report-format/scripts/check_report.py sample.hwpx      # 절 구성·개수 대응·라벨·줄 채움 점검
```

## 배포 전 검사

```bash
python3 ~/.claude/skills/hwpx-skill/scripts/validate.py sample.hwpx --layout
python3 ~/.claude/skills/hwpx-skill/scripts/fill_hwpx.py check sample.hwpx --strict
```
