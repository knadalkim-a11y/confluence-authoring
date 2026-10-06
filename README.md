# Confluence Authoring

대화·자료·프로젝트 근거로 Confluence 문서를 쓰고, 보고서에 들어갈 그림을 만드는 AI용 레퍼런스입니다.
그림은 JSON 스펙 하나를 쓰면 엔진이 그리고 검사까지 해서 Confluence HTML 매크로로 내보냅니다.

## 쓰는 법 (사내 AI에게)

> knadalkim-a11y/confluence-authoring 의 main 브랜치에서 SKILL.md 를 읽고, 아래 내용을 문서로 정리하고
> 필요한 그림을 만들어줘.

AI가 읽는 순서는 `SKILL.md` → `references/visual-specs.md` → `examples/visuals/` 의 가장 가까운 스펙입니다.
빌드에는 Python 3.10+ 와 Node.js 가, 브라우저 검사와 PNG 내보내기에는 Playwright + Chromium 이 필요합니다.

```sh
python scripts/build_visual.py my-figure.json --out dist/my-figure --check
# dist/my-figure/macro.html 을 Confluence HTML 매크로에 붙여 넣기 (figure.svg / figure.png 도 생성)
```

## 구조

```text
SKILL.md                AI 진입점 (문서 작성 원칙, 그림 만드는 순서)
references/             스펙 문법(visual-specs.md), 시각 언어, Confluence 규칙, 실행 구조
recipes/ templates/     문서 종류별 작성법과 표·레이아웃
examples/visuals/       복사해서 쓰는 그림 스펙 (종류별)
scripts/                build_visual.py (진입) · visual_spec.py → kinds/<종류>.py · model.py · choreo.py
                        · live_scene.py · visual_gates.py · figure_metrics.py · validate_html_macro.py
visuals/live/           브라우저에서 도는 장면 코드 (kit, choreo, scenes, runtime)
tests/                  단위 테스트, 피드백 재현 고정 예제(fixtures)
docs/                   변경 내역(CHANGELOG), 상태(STATUS), 설계 문서
lab/                    참고 자료: 품질 기준으로 삼은 모니터링 글 18개 사례 재현, 초기 CSS 모션 13종 (lab/README.md)
```

`lab/` 은 그림을 만드는 데 필요하지 않습니다. 제품 코드는 `lab/` 을 가져다 쓰지 않습니다.

## 검증

`tests/README.md` 에 명령이 있습니다. 브라우저 검사는 로컬 Chromium 결과이며, 사내 Confluence 에서의
표시는 별도로 확인해야 합니다. 상태와 실제 결과는 `docs/STATUS.md` 에 기록합니다.

## 데이터와 보안

공개 저장소에는 범용 규칙과 가상 예시만 둡니다. 사내 자료, PAT·쿠키·비밀번호는 커밋하지 않습니다.
사내 피드백은 내용을 바꾼 가상 그림으로 재현해 `tests/fixtures/` 에 둡니다. 생성 명령은 Confluence 에
접속하거나 자동 게시하지 않습니다.
