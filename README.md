# hwpxSkill — 팀장 최종본 양식 한글 보고서 스킬

한글(HWPX) 업무보고서를 팀장이 고친 최종본(2026-09-22) 양식대로 쓰는 Claude Code
스킬 `team-report-hwpx` 입니다. 스킬 하나로 다음을 모두 합니다.

| 단계 | 하는 일 |
|---|---|
| 내용 설계 | 양식 A/B 선택, 문제점↔추진 내용 대응표, 문장 규칙 |
| 생성 | 제목 상자·□ ㅇ - * 기호·글꼴·크기·자간·간격·표·캡션·그림·붙임 띠까지 최종본과 같은 HWPX |
| 줄 맞춤 | 어중간하게 넘어가는 문단의 자간을 자동으로 좁힘(최종본 실제 줄바꿈으로 맞춘 글자 폭 모델) |
| 점검 | 양식(글꼴·기호·줄 채움), 구조(절 구성·개수 대응·라벨) |
| 배포 전 검사 | 패키지·XML·참조·표 구조 |
| 기존 문서 | HWP 읽기용 사본 만들기, 쪽별 미리보기 |

기준 보고서 원본은 이 저장소에 포함하지 않습니다. 모든 기능은 원본 없이 동작합니다.

## 설치

```bash
git clone https://github.com/Johwiwon/hwpxSkill.git

# 내 모든 프로젝트에서 사용
cp -r hwpxSkill/team-report-hwpx ~/.claude/skills/

# 또는 특정 프로젝트에서만 사용 (프로젝트 루트에서)
mkdir -p .claude/skills && cp -r hwpxSkill/team-report-hwpx .claude/skills/
```

Windows에서는 `~/.claude/skills/` 가 `C:\Users\<사용자>\.claude\skills\` 입니다.
설치 후 Claude Code를 다시 열면 「보고서 작성해줘」 같은 요청에 스킬이 쓰입니다.

## 필요한 것

| 항목 | 용도 | 필수 |
|---|---|---|
| Python 3.9+ | 생성·점검·검사 (표준 라이브러리만 사용, 추가 설치 없음) | 필수 |
| 한글(한컴오피스) + 글꼴 HY헤드라인M·휴먼명조·함초롬돋움 | 결과 파일 열람 | 필수 |
| Node.js 18+ | HWP 읽기(`read_hwp.mjs`), 미리보기(`render_svg.mjs`) | 선택 |

## 직접 실행

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

## 포함된 외부 코드

- `vendor/rhwp/` — rhwp HWP 렌더러 WASM, MIT License (Copyright (c) 2025-2026 Edward Kim). `vendor/rhwp/LICENSE` 참고.
