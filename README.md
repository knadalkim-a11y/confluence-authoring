# Confluence Authoring

대화·자료·프로젝트 근거를 바탕으로 범용 Confluence 문서를 만드는 AI 레퍼런스입니다.
주간보고나 서버 모니터링 전용이 아닙니다. 목적에 맞는 작성법을 고르고, 설명에 도움이
될 때만 시각화나 애니메이션을 사용합니다.

## 현재: v0.3.0 / 기존 Draft PR #1

기존 문서 레시피 8개와 기본 모션 13개를 보존하고, 서버 모니터링 글을 기준으로 만든
복합 설명 레퍼런스 19개를 추가했습니다. 본문에 삽입된 18종 전체와 배포 코드에만 있는
GC 정지 보너스 1종을 구분합니다. 19개는 합성 기준 예시이며 모두 임의의 실측 데이터를
받아들이는 범용 렌더러라는 뜻은 아닙니다. 별도 `stories/` 계층은 만들지 않았습니다.

작업 브랜치: `feat/initial-authoring-skill`. main 병합은 별도이며 자동 게시하지 않습니다.

## AI에게 요청

> knadalkim-a11y/confluence-authoring의 feat/initial-authoring-skill 브랜치에서
> SKILL.md를 읽고, 아래 내용을 목적에 맞는 Confluence 문서로 정리해줘.

필요한 참조만 순서대로 읽습니다. 기본 패턴은 `references/motion-index.md`, 복합 기준
예시는 `references/monitoring-index.md`에서 찾습니다. 저장소에 둔다고 자동 설치되거나
항상 읽히는 것은 아닙니다. 사용 revision을 명확히 지정하세요.

## 기준 예시 18 + 1종 보기

```sh
python scripts/build_monitoring_suite.py
```

`dist/monitoring-suite/gallery.html`을 브라우저로 엽니다. 서버와 외부 리소스 없이 검색,
선택, 원문 해당 절 링크, 케이스별 비교 기록, 입력·가정 보기, 매크로 코드 저장을 제공합니다.
선택한 한 개만 재생하며, 갤러리·개별 미리보기·매크로는 동일한 생성 코드를 사용합니다.
개별 폴더에 macro.html/TXT, preview.html, input.json, model.json이 생성됩니다.

| 범주 | 새 기준 예시 |
|---|---|
| 지표 읽기 | 트래픽 네 패턴, 평균·백분위 비교, 생존자 편향, CPU·지연 조합 |
| 실행 자원 | CPU 스로틀링, 메모리 누수·스파이크, 스레드 풀, 이벤트 루프 |
| 흐름·병목 | 클러스터 연쇄 장애, 파이프라인 병목, 사용률·대기, 큐 상한·거부 |
| 계층·운영 | 캐시 미스 집중, 타임아웃 불일치, 장기 성능 저하, 배포 비교, 포스트모템 |
| 별도 보너스 | GC 정지와 지연 스파이크 |

원문과 공개 배포 코드의 표현·수치를 대조하고 제작본을 실제 로컬 브라우저에서 검수했습니다.
**원본 사이트의 실제 동시 재생 A/B와 사내 Confluence 게시 재생은 아직 미검증입니다.**
동급 품질 점수나 픽셀 일치를 주장하지 않습니다.

## 기존 기본 모션 13개 사용

| 범주 | 구현 패턴 |
|---|---|
| 변화 | line-reveal, threshold-cross, recovery |
| 비교 | before-after |
| 절차 | sequential-flow, parallel-flow, branch-flow, approval-gate, retry-loop |
| 시스템 | request-response |
| 원인·영향 | queue-buildup, failure-propagation |
| 데이터 | distribution-percentile |

```sh
python scripts/build_gallery.py
python scripts/render_motion.py parallel-flow rendered/flow.macro.html \
  --input my-flow.json --preview rendered/flow.preview.html
python scripts/validate_html_macro.py rendered/flow.macro.html
```

기본 갤러리는 `dist/gallery.html`입니다. 기본 입력 계약은 `references/motion-inputs.md`,
예시 입력은 `examples/motion-inputs.json`에 있습니다. 모션은 제목만 바꿔 데이터가 바뀐
것처럼 보이지 않도록 구조화된 입력을 요구합니다. 카탈로그의 planned 항목은 구현 수에
포함하지 않으며, 새 기준 예시가 생겨도 기존 planned 상태를 일괄 승격하지 않았습니다.

## 구조와 역할

```text
SKILL.md                         AI 진입점
references/                      작성 원칙·패턴 색인·입력 계약·품질 비교
recipes/                         문서 종류별 유연한 작성법 8개
templates/                       표·레이아웃·HTML 골격
visuals/components/player.*       공통 컨트롤·스타일·접근성
visuals/components/monitoring.css 복합 기준 예시의 공통 표시 부품
visuals/motion/                   기본 장면과 복합 예시 조립 슬롯
examples/                        합성 입력·가정·출처
scripts/                         계산·조립·생성·정적 검사
gallery/                         갤러리 원본 (빌드 후 dist 결과를 열 것)
tests/                           단위/브라우저 테스트와 실제 기록
docs/                            변경 내역·상태
```

장면 원본을 그대로 매크로에 붙이지 않습니다. 생성된 macro HTML은 공통 파일 경로,
JavaScript, 외부 리소스 의존성 없이 자체 포함됩니다. 생성에는 Python 3.10+만 필요합니다.

## 검증과 한계

새 기준 예시는 30개 단위 테스트, 19개 정적 검사, 19개 Chromium 브라우저 검사를 통과했습니다.
정지·계속·다시보기·최종 장면·320/390px·좁은 컨테이너·움직임 줄이기·인쇄 및 갤러리를
검증했습니다. 반복 테스트 절차는 `references/monitoring-tests.md`에 있습니다.
기존 v0.2 검사 기록은 보존하지만 이번 source-snapshot 환경에서 모두 재실행하지는 않았습니다.
GitHub Actions는 구성하지 않았습니다. 정적 검사는 보안 sanitizer를 대체하지 않습니다.

최적화는 동일 입력의 불필요한 CSS 키프레임 제거입니다. 19개 매크로 총 UTF-8 용량이
1,681,158 → 1,228,380 bytes (26.93%)로 감소했고 데이터 표와 계산 모델은 보존했습니다.
FPS 또는 gzip 성능 측정은 아닙니다. 근거는 `tests/monitoring-verification.json`입니다.

## 데이터와 보안

공개 저장소에는 범용 규칙과 합성 예시만 둡니다. 실제 업무 기록은 Confluence에 두며,
PAT·쿠키·비밀번호·내부 자료는 커밋하지 않습니다. 원문은 출처 링크·공개 파일 식별자만
남기고 외부 애니메이션 코드나 폰트는 재배포하지 않습니다. 생성 명령은 Confluence에
접속하거나 자동 게시하지 않습니다.
