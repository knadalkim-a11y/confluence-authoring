# Monitoring animation quality review — 2026-10-02

## Scope and comparison method

The source article contains 18 mounted animation components. Its shared deployed
bundle exports one additional GC-pause component, which is marked bonus, not counted
as article coverage. The immutable blob identifiers are in monitoring-index.md.

We compared each explanation and published component behavior with an independently
implemented HTML/CSS/SVG reference, then rendered our implementation in Chromium.
This is source/semantic comparison plus our own visual QA, NOT a side-by-side replay
of the original website. The original site could not be loaded in the execution
browser because outbound DNS/network access was unavailable. No numerical claim of
"equal quality" or pixel fidelity is made. The samples are practical reference
candidates, not proof of automatic equivalence for any future text prompt.

## Case-by-case review

| Case | Source behavior inspected | Implemented behavior | Improvement / decision |
|---|---|---|---|
| 트래픽의 네 가지 모양 | 4개 동시 패널, 이동 커서, 급변·새벽 표식 | 동일 시간축 클립과 각 지점 마커; 모든 패널은 같은 축 범위를 사용 | 4개의 독립적인 경우를 단일 추세로 축소하지 않음 |
| 같은 평균, 다른 꼬리 지연 | 두 분포에 점 누적, 평균 뒤 세 백분위 마커 | 개별 요청 점 누적과 계산된 통계; 라벨·좌표·표는 동일 입력에서 생성 | 제작본 첫 검수의100.25ms 평균 오차를 수정; P50/P95/P99를 표본에서 재계산 |
| 실패가 늘었는데 P99는 좋아 보인다 | 에러율 상승 / 지연 하락 / 즉시 실패 분기 | 성공·실패 경로 분리와 동일 시점의 두 그래프 | 지연 지표의 분모와 필터 조건을 명시 |
| CPU와 응답 시간을 함께 읽기 | 세 상황별 CPU/P99 짝지은 그래프 | 3개 상황 × 2지표; 통일된 시간·지표별 범위 | 낮은 CPU인데 느린 경우를 정상과 구분 |
| 100ms 주기 안에서 사라지는 실행 시간 | 주기별 실행/스로틀 구간과 지연 해석 | 7개 CPU 시간 예산 막대; 실행과 정지를 해칭으로 구분 | quota로 임의 P99를 산출하지 않고 차단 시간 자체를 표현 |
| 톱니의 꼭대기보다 GC 뒤 바닥 | 두 톱니, GC 바닥 표시, 한계 도달·재시작 | 바닥 점·추세선과 OOM·재시작 이벤트를 같은 시간축에 표시 | 재시작으로 값이 낮아져도 원인이 해결됐다고 쓰지 않음 |
| 메모리 계단과 같은 시각의 요청 | 힙 계단과 액세스 로그의 동시 강조 | 사건 시각 수직선 + 순차 로그 + 합성 요청 강조 | 상관관계를 확정된 범인이라고 표현하지 않음 |
| 처리가 늦어질 때 풀과 대기열 | 8칸 점유/반납, DB 지연, 큐 누적 후 회복 | v0.4.0 라이브 런타임: 같은 FIFO 사건 모델을 시각 T 상태로 그림. 요청 점이 유입선·대기열·칸을 일관되게 이동, 사용+대기 누적 차트와 요청별 응답 점이 시간축 공유, "유입×처리 시간=필요 칸" 실시간 표시 | v0.3.2 다이어그램은 칸 점유만 표시하고 대기열(최대 14건)은 별도 차트에만 있었음; 높이 약 1,790→487px(715px 폭); 자막·재생 속도를 모델 사건 시각에 결합 |
| 한 대의 제외가 남은 서버에 미치는 영향 | LB/3대/DB, 실패 경로와 재분배 | 연결 경로의 비활성화·잔여 분배율·요청 이동을 동기화 | 99% 합계가 아닌 1/3 분배 의미와 0대 상태 명시 |
| CPU 작업이 이벤트 루프를 멈출 때 | 회전 루프, I/O 우회, CPU 정지와 큐 처리 | 회전 각도를 연속 계산하고 CPU 구간에서 실제로 정지 | 외부 I/O와 루프 실행을 하나의 실패 상태로 혼동하지 않음 |
| 병목 앞에 쌓이고 뒤에는 여유가 남는다 | 3단 파이프라인, 유입 밀도, 병목 큐, 단계 게이지 | 이전 파이프라인 샘플을 공통 렌더 부품으로 재구성; 누적 수치와 그래프 동기화 | 관찰 시간·유입 변화 시점과 대기량 계산을 연결 |
| 사용률과 대기는 같은 비율로 늘지 않는다 | 사용률 곡선과 80% 이후 강조 | 곡선 위 이동 마커와 계산된 기준점 표시 | 적용 모델·안정 조건을 추가 |
| 대기를 쌓을 것인가, 초과분을 거부할 것인가 | 좌우 대기/거부 경로/상한 비교 | 두 큐의 길이·누적 처리·거부 수를 한 모델로 산출 | 입력 200 대 처리 100에서 거부 비율의 보존 관계 보완 |
| 캐시 미스가 DB로 몰리는 순간 | HIT→MISS 경로 전환, 두 그래프, 회복 | 히트율에서 DB QPS를 계산하고 경로를 함께 변경 | 97% 히트 시 QPS는150으로 계산해 분모를 일치 |
| 사용자는 실패했는데 백엔드는 성공했다 | 3초 504, 계속된 작업,5초200, 응답 폐기 | 두 시간 예산 막대와 결과별 도착 경로 | 근거 없는40% 에러율 대신 요청1건의 계층별 결과 |
| 알람 없이 누적되는 성능 저하 | 4주 추세, 첫 주 겹침, 개선되지 않는 방향 | 초기 곡선 겹침과72.22%를 실제 계산 | 미래6주차 예측을 확정적 사실로 표시하지 않음 |
| 배포 뒤 회복과 악화를 나란히 보기 | A/B 추세, 배포·롤백 마커, 회복 강조 | 같은 축 범위와 이벤트 시점, B의 롤백 후 회복 | 수치만 보고 일괄 조치를 권하지 않고 예시와 정책을 분리 |
| 첫 흔적에서 복구까지의 시간을 나누기 | 복구 그래프, 네 마커, 두 구간 괄호 | 마커·구간 막대·18/32 및3/29 계산을 연결 | 알림→복구와 실제 대응 시작→복구를 구분 |
| GC 정지 시점과 꼬리 지연 (bonus) | GC 사건선과 힙/P99 스파이크 동시 표시 | 동일한 x축 클립과 이벤트 정렬 | 본문18종과 분리해 집계 |

## Corrections discovered in our own implementation

- The first constructed tail distribution averaged 100.25ms; changing its 4-count
  value from 45 to 42.5ms restores exactly 100ms. Both samples have 40 observations.
  Mean/P50/P95/P99 are calculated from the same points/frequencies.
- The bonus GC graph originally reset at a different time from the event marker.
  The reset timestamps and latency spikes now share exact normalized event points.
- A worker continuing with a queued job could briefly look idle due to overlapping
  keyframe boundary construction. Occupancy now uses the union of interval boundaries
  and tests all jobs at each boundary. The browser verifies 8 occupied slots at model 5s.
- Worker number labels overlapped; moved inside the lighter occupied cells.
- The failure path initially disappeared while the error rate remained elevated.
  The success/failure paths now continue in parallel; cache recovery remains separate.
- Cluster DB was initially styled as failed before the delay event; normal and slow
  states now switch at the same designated event time.
- Multi-series legends, visible model assumptions, source links, data tables and
  separate SVG IDs were added. Comparison charts share ranges where appropriate.

## Deliberate differences and limitations

The goal is explanatory parity, not copying layout, colors or exact fictional
measurements. Existing macros play once and hold; the source website loops. Our
controls/static/print states support document reading. Original timing and continuous
live numeric counters are not reproduced identically. Some summaries explicitly show
final/example values while a diagram animates; these are not live monitoring readings.

CPU throttling focuses on CPU-time budget and forced wait; it does not derive a P99
curve from quota alone. The worker example uses exact FIFO jobs, not an inferred fixed
queue size from Little's law under unstable overload. The bounded queue calculates
served/rejected/backlog conservation; it does not assume a constant rejection percentage.
Cache DB load comes from total traffic times miss ratio. The timeout example follows
one request and does not invent an aggregate gateway error percentage. The utilization
curve explicitly names M/M/1 assumptions; 80% is not asserted to be a universal threshold.

Symbolic moving dots are not counts except in the distribution sample where a dot is
one observation. Finite models/observed horizons and prescribed causal scenarios are
explicit. These models are not production monitoring simulators or automatic root-cause
detectors. Source correlations are not promoted into proven causes.

## What actually passed

30 new unit-test methods; 19 generated macro lint checks; 19 Chromium case regressions
and independent instance, keyboard, semantic-state and gallery checks. Each case
includes intermediate changes, pause/resume/replay, static-final equivalence, 320/390px
layout, narrow container, reduced motion and print. Wide/mid/narrow contact sheets and
the gallery were inspected. Test sources and artifact hashes are recorded.

The complete browser workload was executed in 10+9 case shards followed by extra
checks after monolithic runs exceeded the tool execution window. Merge validates
coverage, test hashes and artifact hashes; no incomplete run is reported as complete.
Historical v0.2 tests remain preserved but were not all rerun in this source-snapshot
workspace. No GitHub Actions run, Confluence publication or original live browser
verification is claimed.

## Optimization

Collinear CSS keyframes are removed only when property/unit skeleton and interpolated
numeric values agree within the documented rounding tolerance. Event holds are retained;
source tables/geometry/model values are not thinned. Compared with the identical final
source using no collinear elision, 19 macro UTF-8 outputs shrink from 1,681,158 bytes to
1,228,380 bytes (26.93%). This is not a comparison against the older v0.2 package, a gzip
size claim or an FPS benchmark. The gallery renders one selected instance rather than
running 19 previews simultaneously.

## Next verification boundary

The outstanding external gate is a real original-versus-generated browser replay and
published Confluence rendering on the target installation. Until then, use these as
reviewable reference samples and report that distinction rather than claiming that
all original effects are visually equivalent.
