# Teramina Commercial Layer Development Plan

## Purpose

Add paid content and consulting workflows to the existing Teramina platform without creating a separate product or changing the current stack.

The commercial layer should turn Teramina's farm intelligence system into a repeatable business engine:

- free content attracts qualified leads;
- paid documents productize repeated expertise;
- advisory intake converts serious operators into cases;
- advisory reports create client value and reusable structured knowledge;
- selected verified findings can later feed Mnemon, benchmarks, and decision tools.

This plan assumes the current platform remains authoritative:

- frontend: React/Vite, TanStack Query, Zustand, MUI;
- backend: Django Ninja, MongoEngine/MongoDB, Celery/Redis;
- existing product core: farm/pond/cycle data, Google Sheets sync, PL reports, dashboards, Mnemon memory, alerts, tasks, and timeline.

Do **not** start a Next.js/Supabase/FastAPI rebuild for this work.

---

## Product Positioning

Teramina should be positioned as:

> Shrimp aquaculture operating intelligence for farms, hatcheries, investors, and aquaculture businesses.

Paid content and consulting are not separate side products. They are the commercial layer around the existing operating intelligence platform.

### V1 Audience

Prioritize users who can pay for technical clarity:

- farm owners and technical managers;
- hatchery owners and managers;
- investors and new shrimp-project entrants;
- input companies that need technical review or customer education.

### V1 Commercial Offers

Implement these as first-class service packages:

1. Farm Diagnostic Review
2. Crop Planning Review
3. Hatchery Performance Review
4. Broodstock/PL Procurement Advisory
5. Investor Technical Due Diligence
6. Monthly Advisory Retainer

Pricing can be stored as display ranges, not billing logic. Payments remain manual in V1.

---

## V1 Scope

Build both advisory and knowledge-library foundations together.

### In Scope

- Public service package pages.
- Public knowledge library listing and content detail pages.
- Free and paid content states.
- Manual content access grants.
- Advisory intake forms.
- Authenticated advisory case list and case detail pages.
- Advisory report records and file/report attachment flow.
- Minimal admin/service hooks for granting access and updating advisory case status.
- Documentation and test coverage for access behavior and case ownership.

### Out Of Scope

- Payment gateway integration.
- Recurring subscriptions.
- Full CMS migration.
- Public marketplace.
- Native mobile.
- Hatchery KPI database module.
- Client-facing AI over paid documents.
- Automated Mnemon memory writes from consulting reports.

These are future phases after V1 validates demand and workflow quality.

---

## Backend Plan

Follow the existing module style: `models`, `schemas`, `services`, `controllers`, and router registration in `teramina/api.py`.

### New Module: `content`

Purpose: manage free/paid documents and access grants.

#### `ContentItem`

MongoEngine document fields:

- `title`: string, required
- `slug`: string, required, unique
- `summary`: string
- `category`: string, required
- `tags`: list of strings
- `language`: `en` | `id`
- `variant_group_id`: string for grouping master/practical or bilingual versions
- `variant_type`: `master` | `practical`
- `source_content_id`: optional source/master content item id
- `content_type`: `article` | `guide` | `sop` | `checklist` | `template` | `calculator` | `report_template`
- `access_level`: `free` | `paid` | `client` | `admin`
- `body_markdown`: string
- `file_url`: string
- `version`: string, default `1.0`
- `status`: `draft` | `in_review` | `changes_requested` | `approved` | `published` | `archived`
- `review_notes`: latest editorial review note
- `reviewed_by`: reviewing admin user id
- `submitted_at`, `reviewed_at`: datetime, nullable
- `published_at`: datetime, nullable
- `created_at`, `updated_at`

Rules:

- Public list endpoints return only `published` content.
- Free content can expose full body/file metadata.
- Paid/client/admin content returns metadata only unless access is granted.
- Slug is the public stable identifier.

#### `ContentAccess`

MongoEngine document fields:

- `user_id`: string, required
- `content_id`: string, required
- `access_source`: `manual` | `consulting_case` | `admin_grant`
- `expires_at`: datetime, nullable
- `created_at`, `updated_at`

Rules:

- Access is valid when `expires_at` is empty or in the future.
- V1 access is user-scoped. Organization/company access is deferred unless an organization model already exists when implemented.

#### Content API

- `GET /content/items`
  - query: `category`, `tag`, `content_type`, `language`, `access_level`, `variant_group_id`, `variant_type`
  - returns published metadata with `access_status`: `free` | `locked` | `granted` | `expired`

- `GET /content/items/{slug}`
  - returns full content only if free or granted
  - returns metadata plus locked state for paid content without access

- `GET /content/items/{slug}/pdf`
  - returns a generated PDF for published free content

- `GET /content/my-items/{slug}/pdf`
  - authenticated
  - returns a generated PDF when the user has access to the document

- `GET /content/admin/items`
  - admin/internal only in V1
  - returns draft, published, and archived content for manual operations

- `GET /content/admin/access`
  - admin/internal only in V1
  - returns manual content access grants for audit/reconciliation

- `GET /content/admin/items/{content_id}`
  - admin/internal only in V1
  - returns full content for editing

- `GET /content/admin/items/{content_id}/revisions`
  - admin/internal only in V1
  - returns content revision history

- `POST /content/items`
  - admin/internal only in V1
  - creates draft or published content and stores revision 1

- `PATCH /content/items/{content_id}`
  - admin/internal only in V1
  - updates metadata/content/status and stores a new revision

- `POST /content/items/{content_id}/workflow`
  - admin/internal only in V1
  - moves content through review, approval, publication, or archive states and stores a revision

- `POST /content/access`
  - admin/internal only in V1
  - grants manual access to a user

Use the existing `DataSuccessSchema` / `DataErrorSchema` response style.

### New Module: `advisory`

Purpose: manage service offers, intake, review workflow, and advisory reports.

#### `ServicePackage`

MongoEngine document fields:

- `name`: string, required
- `slug`: string, required, unique
- `segment`: `farm` | `hatchery` | `investor` | `input_company` | `retainer`
- `description`: string
- `deliverables`: list of strings
- `required_data`: list of strings
- `price_min_idr`: integer, nullable
- `price_max_idr`: integer, nullable
- `is_active`: boolean
- `sort_order`: integer
- `created_at`, `updated_at`

Rules:

- Public endpoints expose active packages only.
- Prices are display metadata only; no automated payment logic in V1.

#### `AdvisoryCase`

MongoEngine document fields:

- `user_id`: string, required
- `service_package_id`: string, nullable
- `case_type`: `farm_diagnostic` | `crop_planning` | `hatchery_review` | `procurement_advisory` | `investor_due_diligence` | `retainer`
- `status`: `inquiry` | `awaiting_data` | `in_review` | `report_ready` | `closed` | `cancelled`
- `farm_id`, `pond_id`, `cycle_id`: strings, nullable
- `title`: string
- `intake_data`: dict
- `uploaded_files`: list of `{name, url, content_type}`
- `expert_notes`: string
- `report_id`: string, nullable
- `created_at`, `updated_at`

Rules:

- Users can only see their own cases.
- Linking to farm/pond/cycle is optional but should be supported because it connects consulting to existing platform data.
- Intake data remains flexible in V1 so the team can refine forms after real cases.

#### `AdvisoryReport`

MongoEngine document fields:

- `case_id`: string, required
- `user_id`: string, required
- `title`: string
- `executive_summary`: string
- `data_received`: list of strings
- `key_findings`: list of strings
- `likely_causes`: list of strings
- `technical_interpretation`: string
- `economic_implication`: string
- `corrective_action_plan`: list of strings
- `monitoring_plan`: list of strings
- `file_url`: string
- `status`: `draft` | `delivered`
- `created_at`, `updated_at`, `delivered_at`

Rules:

- Report delivery updates the related case to `report_ready`.
- V1 stores report content and/or a generated/uploaded file URL.
- Mnemon memory creation from reports is deferred and should require explicit human confirmation later.

#### `AdvisoryExpertReview`

MongoEngine document fields:

- `case_id`, `user_id`, `reviewer_id`
- `review_type`: string
- `summary`: string
- `findings`: list of strings
- `recommendations`: list of strings
- `risk_flags`: list of strings
- `next_actions`: list of strings
- `status`: `draft` | `delivered`
- `created_at`, `updated_at`, `delivered_at`

Rules:

- Admin users create structured expert review records.
- Delivered reviews are visible to the case owner.
- Draft reviews remain internal.

#### `RetainerCadence`

MongoEngine document fields:

- `case_id`, `user_id`
- `cadence_type`: `weekly` | `biweekly` | `monthly` | `custom`
- `status`: `active` | `paused` | `completed` | `cancelled`
- `last_review_at`, `next_review_at`
- `agenda`: list of strings
- `notes`: string
- `created_by`, `created_at`, `updated_at`

Rules:

- Admin users create cadence records.
- Case owners can see cadence state on their advisory case detail.

#### Advisory API

- `GET /advisory/packages`
  - public/authenticated
  - returns active service packages

- `POST /advisory/cases`
  - authenticated
  - creates an advisory case from selected package/type and intake payload

- `GET /advisory/cases`
  - authenticated
  - returns current user's cases

- `GET /advisory/history`
  - authenticated
  - query: `farm_id`, `pond_id`, `cycle_id`, `limit`
  - returns timeline-ready advisory case events scoped to the signed-in user, or all matching cases for admins
  - requires at least one farm, pond, or cycle filter

- `GET /advisory/cases/{case_id}`
  - authenticated
  - returns owned case detail, report summary, delivered expert reviews, and retainer cadence records if available

- `POST /advisory/cases/{case_id}/files`
  - authenticated
  - appends a private file reference to an owned case, or to any case for admins

- `GET /advisory/admin/cases`
  - admin/internal only in V1
  - returns all cases with `user_id` and expert notes for manual review workflow

- `PATCH /advisory/cases/{case_id}`
  - admin/internal only in V1
  - updates status, expert notes, linked farm/pond/cycle IDs

- `POST /advisory/reports`
  - admin/internal only in V1
  - creates or attaches an advisory report

- `POST /advisory/expert-reviews`
  - admin/internal only
  - creates a structured expert review linked to an advisory case

- `GET /advisory/admin/expert-reviews`
  - admin/internal only
  - returns structured reviews for operational audit

- `POST /advisory/retainer-cadences`
  - admin/internal only
  - creates a recurring review cadence linked to an advisory case

- `GET /advisory/admin/retainer-cadences`
  - admin/internal only
  - returns retainer cadence records for scheduling

- `GET /advisory/admin/reports`
  - admin/internal only in V1
  - returns all advisory reports for delivery audit

- `GET /advisory/reports/{report_id}`
  - authenticated
  - returns report only to the owner

### New Module: `billing`

Purpose: track manual commercial invoices before a payment gateway is introduced.

#### Billing API

- `GET /billing/my-invoices`
  - authenticated
  - returns the current user's invoices and payment status

- `GET /billing/admin/invoices`
  - admin/internal only
  - returns invoices for reconciliation

- `POST /billing/invoices`
  - admin/internal only
  - creates an issued manual invoice for content access, advisory, or subscription

- `POST /billing/invoices/{invoice_id}/mark-paid`
  - admin/internal only
  - marks an invoice paid and grants linked content access when `content_ids` are present

---

## Frontend Plan

Use existing feature-based structure and TanStack Query patterns.

### Public Routes

Add route-level pages:

- `/services`
- `/services/:slug`
- `/knowledge`
- `/knowledge/:slug`
- `/advisory/intake/:service_slug`

Behavior:

- Services page explains the six V1 commercial offers.
- Service detail page shows deliverables, required data, price range, and call to action.
- Knowledge page lists free and paid content with filters.
- Content detail page shows free content directly and paid content as locked unless access is granted.
- Intake page requires authentication before submission; unauthenticated users should be redirected to sign in with intended path preserved if current route handling supports it.

### Dashboard Routes

Add authenticated routes:

- `/dashboard/library`
- `/dashboard/advisory`
- `/dashboard/advisory/new`
- `/dashboard/advisory/:case_id`
- `/dashboard/billing`
- `/dashboard/commercial-admin`

Behavior:

- Dashboard library shows granted paid documents and free content.
- Advisory list shows user cases by status.
- New advisory case allows package/type selection and intake entry.
- Case detail shows submitted intake, linked farm/pond/cycle if present, status, and delivered report.
- Billing shows user invoices and payment status.
- Commercial admin lets admin users create content, grant library access, issue/mark invoices paid, update case status/notes, and deliver reports.

### Frontend Feature Folders

Add:

- `src/features/content/queries.ts`
- `src/features/content/...`
- `src/features/advisory/queries.ts`
- `src/features/advisory/...`

Use existing `helper/axios.js` and response-envelope parsing style.

---

## V1 Intake Forms

Keep V1 intake forms structured enough for advisory work but flexible enough to evolve.

### Farm Diagnostic Review

Fields:

- farm name/location
- linked farm/pond/cycle IDs if available
- stocking date
- pond size
- stocking density
- PL source
- water source
- feed data summary
- water quality summary
- mortality timeline
- disease test results
- harvest result if available
- main question/problem

### Crop Planning Review

Fields:

- farm/pond details
- planned stocking date
- pond size/depth
- target density
- PL source
- target size/DOC
- expected survival/FCR assumptions
- feed/electricity/labor cost assumptions
- market price assumptions
- main planning concern

### Hatchery Performance Review

Fields:

- hatchery name/location
- broodstock source
- quarantine/acclimation summary
- ablation timing
- mating rate
- spawning rate
- nauplii per spawn
- hatching rate
- larval survival
- PL quality/testing notes
- main performance concern

### Investor Technical Due Diligence

Fields:

- project type: farm | hatchery | integrated
- location
- planned capacity
- capex estimate
- opex estimate
- management/team background
- technical assumptions
- target ROI/payback
- documents available
- main investment question

---

## Implementation Sequence

### Slice 1 — Documentation And Navigation

- Add this plan to README's active documentation list.
- Add public service and knowledge routes as static/placeholder pages backed by constants if backend is not ready yet.
- Confirm route structure and copy align with `CYBERNETIC_PRODUCT_FRAMEWORK.md`.

### Slice 2 — Backend Commercial Primitives

- Implement `content` and `advisory` modules.
- Add models, schemas, services, controllers, and API registration.
- Add tests for access control, ownership, and service package visibility.

### Slice 3 — Frontend Library And Services

- Implement public service package pages from API.
- Implement knowledge library list/detail and locked/granted states.
- Add dashboard library page for granted content.
- Add frontend tests for locked/free/granted rendering.

### Slice 4 — Advisory Workflow

- Implement advisory intake submission.
- Implement dashboard advisory list/detail.
- Implement report display/attachment.
- Add frontend and backend tests for case ownership and status display.

### Slice 5 — Operational Hardening

- Add seed/demo command or fixture for initial service packages and sample content.
- Add manual admin access-grant procedure to documentation.
- Add manual QA checklist for one paid content grant and one advisory case.

---

## Acceptance Criteria

V1 is complete when:

- a visitor can see service packages;
- a visitor can browse free and locked paid content;
- a signed-in user can submit an advisory case;
- a signed-in user can view their advisory case status;
- a manually granted user can access paid content;
- a delivered advisory report appears in the user's dashboard;
- users cannot access another user's advisory case or report;
- tests cover content access, case ownership, and core UI states.

---

## Test Plan

### Backend

Run:

```bash
cd core-be-teramina-main
python -m pytest -q
python manage.py check --deploy
```

Required new tests:

- free content detail returns full body;
- paid content without access returns locked metadata;
- paid content with valid access returns full body;
- expired access does not unlock content;
- active service packages are public;
- inactive service packages are hidden from public list;
- advisory case creation stores intake data for signed-in user;
- advisory case list excludes other users' cases;
- advisory report is only visible to the owner.

### Frontend

Run:

```bash
cd fe-teramina-main
yarn lint
yarn typecheck
yarn test
yarn build
```

Required new tests:

- services page renders active packages;
- knowledge page shows free and locked paid cards;
- content detail displays locked state without access;
- dashboard library shows granted content;
- advisory intake submits a case;
- advisory case detail renders submitted status and delivered report state.

---

## Future Phases

### Phase 2 — Payment And Subscription

- Manual invoice/payment status foundation exists.
- Payment-driven content access exists for admin-marked paid invoices.
- Add Midtrans or Xendit.
- Add company/member subscriptions.
- Convert manual invoice payment into gateway webhooks.

### Phase 3 — Content Operations

- Version history and basic admin editing UI exist.
- Editorial approval workflow exists for review, approval, publication, and archive transitions.
- Downloadable PDF generation for markdown content exists.
- Bilingual master/practical content variant metadata exists.

### Phase 4 — Consulting Portal Depth

- Private file references exist for advisory cases.
- Structured expert review forms exist for admin users.
- Retainer review cadence records exist.
- Advisory history now links consulting cases into farm/pond/cycle timelines.

#### Completed Next-Stage Todo List

- [x] Add bilingual/master-practical content metadata:
  - store `variant_group_id`, `variant_type`, and `source_content_id` on content items;
  - expose variant metadata in public, authenticated, admin, and revision responses;
  - add admin controls for language, variant type, variant group, and source content;
  - cover language/variant filtering in backend tests.
- [x] Add private advisory file references:
  - allow case owners and admins to attach private file metadata to advisory cases;
  - keep actual storage provider integration deferred;
  - render uploaded file references in the client case detail.
- [x] Add structured expert review records:
  - create admin-only structured review forms linked to advisory cases;
  - capture summary, findings, recommendations, risk flags, and next actions;
  - expose delivered reviews to the case owner.
- [x] Add retainer cadence records:
  - create admin-only cadence records linked to retainer advisory cases;
  - track cadence type, last/next review dates, agenda, notes, and status;
  - expose cadence state in the client case detail.
- [x] Add advisory history linked to farm/pond/cycle timelines:
  - expose `/advisory/history` for farm, pond, or cycle filtered case events;
  - preserve owner scoping for clients and all-case visibility for admins;
  - render linked advisory case events in the existing pond timeline page.
- [x] Update manual QA and regression tests for each new operational path.

### Phase 5 — AI-Assisted Advisory

- Internal assistant brief generation exists for admin users.
- Assistant briefs summarize advisory intake, missing data, linked files, expert review records, existing reports, retainer cadence, and Mnemon-aligned cited source references.
- Assistant drafts can seed the advisory report form, but remain internal first-pass material with generated/accepted audit records.
- Uploaded case file metadata is normalized with case-private ownership fields and checked before assistant draft use.
- Assistant-generated report records stay internal with `expert_review_required` status until an admin delivers a reviewed report.
- Admin users can transition reviewed reports to `delivered`, which marks the case `report_ready` and indexes the delivered report as a case-private advisory source.
- Retrieval stays on the active MongoEngine/MongoDB Mnemon track; Postgres/pgvector remains deferred.
- Commercial documents and advisory outputs are indexed as advisory source embeddings, not farmer-visible `AgentMemory`.
- Allow client-facing AI only after citation, access isolation, and safety behavior are validated.

#### Completed First Slice

- [x] Add admin-only `/advisory/admin/cases/{case_id}/assistant-brief`.
- [x] Generate missing-data checklist and draft report sections from structured advisory records.
- [x] Recommend relevant published Teramina documents as internal references.
- [x] Add `advisory_source_embeddings` for source-cited commercial/advisory retrieval aligned with Mnemon embedding behavior.
- [x] Add source citations to generated assistant draft reports.
- [x] Add admin UI for generating a brief and copying draft sections into report delivery.
- [x] Add accepted-draft audit logs for generated briefs and report sections copied into deliverables.
- [x] Add management command to reindex published content, delivered advisory reports, and delivered expert reviews.
- [x] Add client/data isolation checks for uploaded case documents.
- [x] Add internal report drafting with citation blocks and expert-review-required status.
- [x] Add review/publish workflow for converting `expert_review_required` reports into delivered client reports.
- [x] Cover assistant brief behavior in backend and frontend tests.

#### Remaining Todo List

- Add source snippets and document IDs to any future conversational assistant answers.
- Add operator UI for browsing assistant brief logs and report workflow history.

### Phase 6 — Hatchery And Investor Modules

- Add hatchery profile, broodstock batches, maturation performance, spawning logs, nauplii output, PL quality tests.
- Add investor feasibility and due-diligence scoring reports.

---

## Commercial Guardrails

- Avoid miracle claims and guaranteed survival/profit language.
- Advisory output must state assumptions and data gaps.
- Client owns raw data.
- Teramina may use anonymized aggregate data only with explicit permission in terms or contract.
- Conflicts of interest around broodstock, PL, feed, or supplier recommendations must be disclosed.
- High-stakes disease or chemical guidance should recommend lab confirmation or qualified expert review.
