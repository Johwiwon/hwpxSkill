# hwpxSkill — 팀장 최종본 양식 한글 보고서 스킬

한글(HWPX) 업무보고서를 팀장이 고친 최종본(2026-09-22) 양식대로 쓰기 위한
Claude Code 스킬 두 개입니다. 둘을 함께 설치합니다.

| 스킬 | 맡는 일 |
|---|---|
| `team-report-hwpx` | 서식: 글꼴·크기·자간·간격·표·붙임 띠까지 최종본과 같은 HWPX 생성, 양식 점검 |
| `korean-report-format` | 내용: 절 구성(양식 A/B), 문제점↔추진 내용 대응, 문장 규칙, 구조 점검 |

`team-report-hwpx` 의 생성·점검은 단독으로도 동작하지만, 무엇을 어떤 순서로 쓸지는
`korean-report-format` 이 잡으므로 함께 있어야 보고서 작성 전 과정이 같은 기준으로 돌아갑니다.

## team-report-hwpx 기능

- 제목 상자·작성일 줄·□ ㅇ - * 기호·글꼴·크기·장평·간격·표·캡션·그림·붙임 띠를 최종본과 같게 생성
- 어중간하게 넘어가는 문단은 자간을 자동으로 좁혀 줄을 맞춤(최종본 실제 줄바꿈으로 맞춘 글자 폭 모델)
- 기존 HWPX의 글꼴·기호·줄 채움 점검

기준 보고서 원본은 이 저장소에 포함하지 않습니다. 생성·점검은 원본 없이 동작합니다.

## 설치

둘 중 하나를 고릅니다.

```bash
# 1) 내 모든 프로젝트에서 사용
git clone https://github.com/Johwiwon/hwpxSkill.git
cp -r hwpxSkill/team-report-hwpx hwpxSkill/korean-report-format ~/.claude/skills/

# 2) 특정 프로젝트에서만 사용 (프로젝트 루트에서)
mkdir -p .claude/skills && cp -r hwpxSkill/team-report-hwpx hwpxSkill/korean-report-format .claude/skills/
```

Windows에서는 `~/.claude/skills/` 가 `C:\Users\<사용자>\.claude\skills\` 입니다.
설치 후 Claude Code를 다시 열면 「보고서 작성해줘」 같은 요청에 스킬이 쓰입니다.

## 필요한 것

| 항목 | 용도 | 필수 |
|---|---|---|
| Python 3.9+ | 생성·점검 스크립트(표준 라이브러리만 사용) | 필수 |
| 한글(한컴오피스) + 글꼴 HY헤드라인M·휴먼명조·함초롬돋움 | 결과 파일 열람 | 필수 |
| `hwpx` 스킬 (`~/.claude/skills/hwpx-skill`) | 배포 전 검사, 미리보기(`render_svg.mjs`) | 선택 |
| Node.js 18+ | 미리보기(`render_svg.mjs`) | 선택 |

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

## 함께 쓰면 좋은 스킬

- `hwpx`: HWPX 파일 조작과 배포 전 검사(이 저장소에는 없음)
