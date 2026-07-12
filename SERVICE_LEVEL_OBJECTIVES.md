# Teramina Service Level Objectives

## Initial Beta Targets

Measured monthly, excluding announced maintenance:

| Indicator | Objective |
|---|---:|
| Authenticated API availability | 99.5% |
| Frontend availability | 99.5% |
| API p95 latency, excluding report/AI generation | <= 1.5 seconds |
| API p99 latency, excluding report/AI generation | <= 4 seconds |
| Interactive background jobs completed | 95% within 2 minutes |
| Scheduled monitoring jobs completed | 99% within 30 minutes of schedule |
| Recovery time objective | <= 60 minutes |
| Recovery point objective | <= 24 hours |

## Measurement

- Availability uses external health probes, not container uptime.
- Latency is measured at the API boundary and segmented by route.
- Job latency runs from enqueue time to terminal state.
- Dependency failures count unless the product degrades safely and remains usable.
- Report and AI generation have separate duration and success-rate dashboards.

## Error Budget

The 99.5% monthly target permits about 3 hours 39 minutes of unavailability in a 30-day month. At half-budget consumption, pause non-critical releases. When exhausted, ship only reliability and security work until the trailing 30-day window recovers.

Review targets after each pilot cohort and monthly during beta. Tighten them only when telemetry demonstrates stable performance.
