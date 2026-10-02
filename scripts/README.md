# Scripts

No third-party Python packages are required.

## Render a motion template

Example:

```bash
python scripts/render_template.py \
  visuals/motion/line-reveal.html \
  rendered/line-demo.html \
  --prefix ca-line-001 \
  --set "TITLE=응답 시간 변화" \
  --set "DESCRIPTION=설명용 예시 데이터" \
  --set "ACCESSIBLE_DESCRIPTION=응답 시간이 중간 이후 증가하는 선 그래프" \
  --set "CHANGE_LABEL=변화 시작" \
  --set "CAPTION=중간 구간부터 응답 시간이 증가합니다."
```

The renderer fails when required tokens remain unresolved unless `--allow-unresolved` is explicitly passed.

## Validate rendered macro HTML

```bash
python scripts/validate_html_macro.py rendered/line-demo.html
```

The validator rejects:
- html/head/body wrappers;
- script and iframe;
- external network dependencies;
- unresolved tokens;
- missing reduced-motion behavior;
- missing print/static behavior.

Template source files intentionally contain tokens. To inspect a template directly:

```bash
python scripts/validate_html_macro.py visuals/motion/line-reveal.html --allow-template-tokens
```

This is static validation only. Actual Confluence rendering must still be checked in the target instance.
