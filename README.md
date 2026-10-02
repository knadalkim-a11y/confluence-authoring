# Confluence Authoring

범용 Confluence 문서 제작을 위한 AI authoring reference + recipe + visual library입니다.

이 저장소의 목적은 특정 보고서 양식을 강제하는 것이 아니라, AI가 사용자의 목적과 근거 자료를 먼저 파악한 뒤 적절한 문서 구조와 시각 표현을 선택하도록 돕는 것입니다.

## 사용 예

- "지금까지 대화한 내용을 Confluence 주간 안건으로 정리해줘."
- "이 설계를 신입 개발자가 이해할 수 있는 기술 문서로 만들어줘."
- "장애 원인과 복구 과정을 Confluence에 기록해줘."
- "기존 방식과 개선 방식을 비교하는 설명자료를 만들어줘. 필요하면 애니메이션도 사용해."

AI에게 이 저장소를 참고하라고 지정한 뒤, 먼저 `SKILL.md`를 읽도록 하면 됩니다.

## 구조

```text
confluence-authoring/
├─ SKILL.md
├─ references/
├─ recipes/
├─ visuals/motion/
├─ templates/
├─ gallery/index.html
├─ scripts/
└─ tests/
```

## 기본 원칙

1. 문서의 목적이 먼저이며 애니메이션은 선택 사항입니다.
2. 기존 Confluence 페이지를 수정할 때는 먼저 현재 내용을 읽고 기존 자산과 구조를 보존합니다.
3. "하기로 한 것", "진행 중인 것", "완료한 것"을 구분합니다.
4. 확인되지 않은 수치나 완료 상태를 만들어내지 않습니다.
5. 가장 단순하게 의미를 전달하는 표현을 선택합니다.
6. HTML motion은 기본적으로 외부 라이브러리와 JavaScript 없이 CSS + SVG로 작성합니다.
7. 실제 Confluence 게시 후 저장 결과와 렌더링 상태를 별도로 확인합니다.

## Motion v0.1

초기 구현 패턴:
- `line-reveal`
- `sequential-flow`
- `distribution-percentile`

`references/motion-catalog.yaml`에는 향후 확장 후보도 관리합니다. `status: planned` 패턴은 구현된 것으로 간주하지 않습니다.

## 보안

PAT, 비밀번호, 쿠키, API key 등 인증정보를 저장소에 넣지 않습니다.

## 상태

v0.1 — initial authoring package.
