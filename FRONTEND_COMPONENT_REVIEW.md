# Frontend Large-Component Review

## Decision Standard

Extract only boundaries that own a cohesive workflow or can be tested independently. Do not split components merely to reduce line count when state and mutations remain tightly coupled.

## Reviewed Components

| Component | Approx. lines | Stable next boundary | Priority |
|---|---:|---|---:|
| Commercial admin | 2,300+ | Content, billing, advisory operations, and audit sections | High |
| Google Sheets | 679 | Connection/setup panel and sync-preview/results panel | High |
| Agent chat | 669 | Alerts/tasks tabs and memory-confirmation message | Medium |
| Memory page | 624 | Memory editor and memory-list/review panel | Medium |
| Today page | 579 | Urgent actions, active alerts, and pond-status grid | Medium |
| Advisory queries | 543 | Split query hooks by case, report, hatchery, and investor domains | Medium |
| Advisory dashboard pages | 429 | Case list and case detail surfaces | Low |
| Dashboard overview | 410 | KPI summary, chart area, and report-generation action | Low |
| Harvest simulator | 405 | Scenario editor and results comparison | Low |
| Forecast page | 378 | Historical chart and forecast confidence panel | Low |

## Current Extraction

The commercial-admin access-request workflow and shared section/navigation components now live in `src/features/commercial-admin/sections.jsx`. This boundary owns its rendering and mutations without duplicating page state.

## Next Slice

Extract commercial content operations next, but first move its form state and mutations into a dedicated hook. Passing the current form state through a large prop surface would reduce file length without reducing coupling. Preserve the existing commercial-layer integration test throughout the extraction.
