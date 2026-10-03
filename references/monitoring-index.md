# Monitoring reference index — v0.3 benchmark pack

18 article cases + 1 bonus. This extends the reference collection; it does not turn
the existing 13 basic patterns into 32 unrestricted measured-data renderers.

Source article: https://kciter.so/posts/server-monitoring-analysis-guide/
Published source: `kciter/kciter.github.io`; article blob
`44ec1362094f2e9725754224c74452c81e1a021e`, animation bundle blob
`424e0af2d7bad3217020c99c268a940120daf1a3`.
Only links, metadata and independently written examples are included. No third-party
animation implementation, article text dump or fonts are redistributed.

## Choose a case

| Case ID | Purpose | Original component | In article |
|---|---|---|---|
| `traffic-patterns` | 같은 축에서 정상·급락·급증·주기적 스파이크를 비교한다. | `TrafficPatternDemo` | yes |
| `percentile-comparison` | 관측값이 쌓인 뒤 평균과 P50·P95·P99를 비교한다. | `PercentileDemo` | yes |
| `survivorship-bias` | 에러율·성공 요청의 지연 분포·빠른 거부 경로를 함께 본다. | `SurvivorshipDemo` | yes |
| `cpu-latency` | 정상·대기 문제·CPU 포화의 세 가지 조합을 비교한다. (live runtime) | `CpuPatternDemo` | yes |
| `cpu-throttling` | 할당량 사용과 강제 대기를 시간 구간으로 구분한다. | `ThrottlingDemo` | yes |
| `memory-leak` | 정상 수거와 GC 후 잔존량 증가를 나란히 비교한다. | `MemoryLeakDemo` | yes |
| `memory-spike` | 메모리 급증 지점과 이벤트 로그를 같은 시간에 겹쳐 본다. | `MemorySpikeDemo` | yes |
| `thread-pool` | 동일한 요청 유입에서 처리 시간 변화가 점유와 대기에 미치는 영향을 보여준다. (live runtime) | `ThreadPoolDemo` | yes |
| `cluster-cascade` | 3개 서버의 분배율이 1/3, 1/2, 1로 바뀌는 과정을 본다. | `CascadeDemo` | yes |
| `event-loop` | 회전·위임 I/O·CPU 정지·대기 처리 재개를 구분한다. | `EventLoopDemo` | yes |
| `pipeline-bottleneck` | 유입 변화·단계별 한도·대기 증가를 하나의 파이프라인으로 본다. (live runtime) | `BottleneckDemo` | yes |
| `utilization-wait` | 사용률 변화에 따라 곡선을 따라가는 마커로 비선형성을 보여준다. | `UtilizationCurveDemo` | yes |
| `bounded-queue` | 같은 유입과 처리 능력에서 무한 대기와 상한 있는 큐를 비교한다. (live runtime) | `BackpressureDemo` | yes |
| `cache-stampede` | 캐시 히트율·DB 유입·요청 경로가 함께 바뀌는 모습을 본다. | `CacheStampedeDemo` | yes |
| `timeout-mismatch` | 게이트웨이의 대기 종료와 백엔드 완료를 같은 시간축에 놓는다. | `TimeoutMismatchDemo` | yes |
| `slow-degradation` | 4주의 추세와 같은 요일의 비교선을 구분해 본다. | `SlowBurnDemo` | yes |
| `deploy-comparison` | 같은 배포 마커에서 시작한 두 경로와 롤백 뒤 상태를 비교한다. | `DeployDemo` | yes |
| `postmortem-timeline` | 첫 징후·알림·대응 시작·복구의 네 사건과 간격을 보여준다. | `PostmortemDemo` | yes |
| `gc-pause` | 주기적인 지연 스파이크와 GC 사건을 같은 축에 놓는다. | `GcPauseDemo` | bonus only |

## Use

```sh
python scripts/build_monitoring_suite.py
```

Open `dist/monitoring-suite/gallery.html`. This is an offline single-preview gallery;
its JavaScript is only the gallery UI. The exact macro is mounted, shown as code and
exported. Individual folders include macro HTML/TXT, preview, input and model evidence.

For one case, start with its complete object from `examples/monitoring-cases.json`:

```sh
python scripts/build_monitoring_suite.py --case pipeline-bottleneck \
  --input my-case.json --output rendered/my-case
python scripts/validate_html_macro.py rendered/my-case/macro.html
```

The renderer defaults to a fresh prefix for a single case. The all-case gallery uses
stable distinct prefixes for reproducibility. Do not paste the SAME generated macro
twice on a Confluence page; render a fresh instance for each insertion.

## Input boundary

`params` supports only the declared keys for that case. Numeric model inputs are
validated. Cases with empty `params` are illustrative authored examples, not generic
data-import templates. Text edits do not turn synthetic curves into measurements.
All reference outputs explicitly remain synthetic. For measured data, use the basic
motion input contracts or add and test an appropriate renderer. Do not relabel fixed
geometry as measurements. `model.json` contains the calculations actually used.

The implementation uses existing `player.*` and new `reference_scene.py` helpers for
unique multi-chart IDs, explicit x-time, accumulating tables and normalized animation.
`monitoring_cases.py` supplies case-specific behavior. No `stories/` layer was added.

## Comparison boundary

Read `monitoring-quality-review.md` and `monitoring-tests.md` before claiming quality.
Original explanatory text and published code were inspected. Our macros were actually
rendered/tested locally. Original live browser A/B, target Confluence publication,
reader comprehension and cross-browser/FPS equivalence are NOT verified.
