# API Authorization Audit

Audit date: 2026-07-12

## Scope

All Django Ninja controller routes under `core-be-teramina-main/teramina` were reviewed for authentication, resource ownership, and administrator-role enforcement. Resource-scoped service methods called by controllers were reviewed where enforcement is delegated below the route layer.

## Enforcement Model

- Farmer resources use the shared farm, pond, and cycle ownership helpers or user-scoped database queries.
- Dashboard filter services validate the farm owner and require ponds and cycles to belong to the selected parent resource.
- Advisory, billing, content-management, and access-management services enforce case ownership, invoice ownership, or administrator role before returning or mutating protected data.
- Background report and external-summary results bind task IDs to the requesting user.
- Mnemon routes validate every supplied farm, pond, and cycle context. LLM tool execution repeats these checks before invoking a tool.
- Public routes are limited to login/registration, access requests, published commercial content and packages, health endpoints, and unguessable-token report shares.

## Findings Closed

- Mnemon chat, streaming, control loops, memories, explanations, daily summaries, timelines, and tool calls previously trusted caller-supplied resource IDs.
- Dashboard overview, economics, feeding, PDF, and report creation previously checked farm ownership but did not validate optional pond and cycle ownership.
- Earlier P0 work closed cross-user access to dashboard/water-quality data and asynchronous task results, restricted global variable mutation, and made malformed IDs fail closed.

## Regression Coverage

Negative authorization tests cover cross-user dashboard, water-quality, report-task, external-summary, Mnemon chat, and Mnemon tool access. Existing service and controller suites cover user-scoped CRUD and administrator-only workflows.
