# Confluence Authoring

대화·자료·프로젝트 근거를 바탕으로 범용 Confluence 문서를 만드는 AI 레퍼런스입니다.
주간보고 전용이 아닙니다. 문서 목적에 맞는 작성법을 고르고, 설명에 도움이 될 때만
시각화나 애니메이션을 사용합니다.

## 현재: v0.2.0 / PR #1 검토 중

8개 문서 레시피, 13개 구현 모션, 입력값 기반 렌더러, 검색형 갤러리, 자동 검사를 제공합니다.
13개 추가 후보는 `planned`로 남겨 두었으며 구현 수에 포함하지 않습니다.
이번 작업은 `feat/initial-authoring-skill` 브랜치에 있고 main 병합은 별도입니다.

| 범주 | 구현 패턴 |
|---|---|
| 변화 | line-reveal, threshold-cross, recovery |
| 비교 | before-after |
| 절차 | sequential-flow, parallel-flow, branch-flow, approval-gate, retry-loop |
| 시스템 | request-response |
| 원인·영향 | queue-buildup, failure-propagation |
| 데이터 | distribution-percentile |

## AI에게 요청

> knadalkim-a11y/confluence-authoring의 feat/initial-authoring-skill 브랜치에서
> SKILL.md를 읽고, 아래 내용을 목적에 맞는 Confluence 문서로 정리해줘.

저장소에 둔다고 자동 설치되거나 항상 읽히는 것은 아닙니다. 시작 파일과 사용 revision을
명확히 지정하세요. 이후 병합되면 main을 지정하면 됩니다.

## 샘플 보기

Python 3.10+가 있는 환경에서 저장소를 받은 뒤 실행합니다. 생성에는 추가 패키지가 없습니다.

```sh
python scripts/build_gallery.py
```

생성된 `dist/gallery.html`을 브라우저로 엽니다. 검색·분류·패턴 선택·매크로 코드 보기를
제공하며 선택한 한 개만 화면에 렌더링합니다. 서버나 외부 라이브러리가 필요하지 않습니다.
`gallery/index.html`은 갤러리의 원본이며 실제 샘플 데이터는 빌드 시 삽입합니다.
`dist/`에는 각 패턴의 입력 JSON, 미리보기 HTML, 복사 가능한 macro HTML도 생성됩니다.

## 원하는 내용으로 생성

`examples/motion-inputs.json`에서 필요한 패턴의 객체를 가져와 별도 JSON 파일로 수정합니다.

```sh
python scripts/render_motion.py parallel-flow rendered/flow.macro.html \
  --input my-flow.json --preview rendered/flow.preview.html
python scripts/validate_html_macro.py rendered/flow.macro.html
```

바로 예시를 만들려면 `--input ...` 대신 `--example`을 사용합니다.
입력 계약은 `references/motion-inputs.md`를 참고하세요. 기존 `--set` 방식으로 차트 제목만
바꿔 다른 데이터인 것처럼 쓰는 것을 막기 위해 모션은 구조화된 입력을 요구합니다.

## 구조와 역할

```text
SKILL.md                       AI 진입점과 작업 순서
references/                    원칙·입력 계약·패턴 색인·카탈로그
recipes/                       문서 종류별 유연한 작성법 8개
templates/                     표·레이아웃·일반 HTML 골격
visuals/components/player.*     공통 컨트롤·스타일·접근성 처리 1개
visuals/motion/*.html           설명 목적별 장면 원본 13개
examples/motion-inputs.json     각 장면의 합성 예시 입력
gallery/index.html             검색형 갤러리 원본
scripts/                       계산·조립·생성·정적 검사
tests/                         실제 단위/브라우저 검사와 기록
docs/                          변경 내역·상태
```

**장면 원본은 그대로 HTML 매크로에 붙이지 않습니다.** 렌더러가 공통 코드를 포함해 만든
`*.macro.html`을 넣습니다. 출력에는 JavaScript나 공통 파일 경로 의존성이 남지 않습니다.

## 검증

```sh
python -m unittest discover -s tests -v
python tests/browser_smoke.py --browser /path/to/chromium
```

두 번째 명령만 Playwright와 Chromium이 필요합니다. `tests/README.md`와 실제 기록을
참고하세요. 로컬 브라우저 검증과 실제 Confluence 게시 검증은 서로 다른 상태입니다.
현재 Confluence 게시·재생 검증은 수행하지 않았으며 GitHub Actions도 구성하지 않았습니다.

## 데이터와 보안

공개 저장소에는 범용 규칙과 합성 예시만 둡니다. 실제 업무 기록은 Confluence에 두며,
PAT·쿠키·비밀번호·내부 자료는 커밋하지 않습니다. 라이브러리 생성 명령은 Confluence에
접속하거나 자동 게시하지 않습니다. HTML 검사는 보수적인 lint이며 보안 sandbox나
서버 sanitizer를 대체하지 않습니다.
