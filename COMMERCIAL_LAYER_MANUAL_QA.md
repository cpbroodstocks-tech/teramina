# Commercial Layer Manual QA

Use this checklist after backend, frontend, and MongoDB are running.

## Seed Starter Data

Run once per environment, then re-run whenever the starter catalog changes:

```bash
cd core-be-teramina-main
python manage.py seed_commercial_layer
```

Expected result:

- 6 active advisory service packages.
- 4 published starter content items.
- Re-running the command updates existing records instead of creating duplicates.

Optional cleanup:

```bash
python manage.py seed_commercial_layer --archive-missing
```

This archives content and disables service packages whose slugs are no longer in the seed catalog.

## Reindex Advisory Sources

Run after publishing knowledge content or delivering advisory records that should be available to internal assistant briefs:

```bash
python manage.py reindex_advisory_sources
```

Expected result:

- Published knowledge items are indexed as global advisory sources.
- Delivered advisory reports and expert reviews are indexed as case-private advisory sources.
- The command uses the local Mnemon-aligned hash embedding provider by default.

## Public Pages

1. Open `/services`.
2. Confirm the six service packages appear.
3. Click `Request Review` for Farm Diagnostic Review.
4. Confirm `/advisory/intake/farm-diagnostic-review` opens.
5. Open `/knowledge`.
6. Confirm free and paid knowledge items appear.
7. Open the free Farm Failure Post-Mortem content.
8. Confirm the body is visible.
9. Open a paid content item.
10. Confirm the locked access message appears.

## Advisory Intake

1. Sign in as a normal user.
2. Open `/dashboard/advisory`.
3. Click `New Advisory Case`.
4. Select Farm Diagnostic Review.
5. Fill the structured V1 intake fields:
   - farm name/location;
   - stocking date;
   - pond size;
   - stocking density;
   - PL source;
   - feed, water quality, mortality, disease, and harvest summaries;
   - main question or problem.
6. Submit the case.
7. Open `/dashboard/advisory`.
8. Confirm the case appears with `inquiry` status.
9. Open the case detail.
10. Confirm the structured intake, status, and no-report state render correctly.

## Manual Paid Content Access

V1 supports two manual access paths:

- direct admin access grant;
- invoice payment that automatically creates content access.

Required IDs:

- target `user_id`;
- target `content_id` from the paid `ContentItem`.

1. Sign in as a user with `role_user=admin`.
2. Open `/dashboard/commercial-admin`.
3. In `Create Content`, create a draft or published paid item if needed.
4. In `Grant Library Access`, select the paid content and enter the target `user_id`.
5. Submit the grant.
6. Confirm the grant appears under `Recent Grants`.
7. Sign in as the target user.
8. Open `/dashboard/library`.
9. Confirm the paid content appears as granted.
10. Open the paid content detail.
11. Confirm the full body or file access is visible.

## Content Operations

1. Sign in as a user with `role_user=admin`.
2. Open `/dashboard/commercial-admin`.
3. In `Content Operations`, select an existing content item.
4. Confirm the form loads title, summary, tags, version, status, and body markdown.
5. Change summary, version, or body markdown.
6. Enter a clear `Change note`.
7. Submit `Update Content`.
8. Confirm the update success message appears.
9. Confirm `Recent Revisions` shows the new revision number and change note.
10. In `Editorial Workflow`, move a draft item to `in_review`.
11. Confirm `/knowledge/<slug>` does not expose the item while it is not `published`.
12. Move the item to `approved`, then `published`, with review notes.
13. Confirm `Recent Revisions` records each workflow transition.
14. Open `/knowledge/<slug>` as a user with access and confirm published content renders the updated body.
15. Click `Download PDF`.
16. Confirm a generated PDF downloads for the unlocked document.
17. Set `Language`, `Variant`, `Variant group ID`, and optional `Source content ID` on a content item.
18. Save the content item and confirm the values persist after reselecting the item.
19. Create an Indonesian `practical` variant linked to an English `master` content item.
20. Open `/knowledge` and confirm language and variant chips appear.

## Consulting Portal Depth

Private file references:

1. Sign in as the advisory case owner.
2. Open `/dashboard/advisory/<case_id>`.
3. In `Attach Private File`, enter file name, private URL, and description.
4. Submit `Attach File`.
5. Confirm the file appears under `Private Files`.
6. Sign in as a different non-admin user and confirm the case remains inaccessible.

Structured expert review:

1. Sign in as a user with `role_user=admin`.
2. Open `/dashboard/commercial-admin`.
3. In `Expert Review Forms`, select a case.
4. Enter review summary, findings, recommendations, risk flags, and next actions.
5. Submit with `status=delivered`.
6. Sign in as the case owner.
7. Open `/dashboard/advisory/<case_id>`.
8. Confirm the delivered expert review appears.

Retainer cadence:

1. Sign in as a user with `role_user=admin`.
2. Open `/dashboard/commercial-admin`.
3. In `Retainer Cadence`, select a retainer case.
4. Set cadence type, status, next review date, agenda, and notes.
5. Submit `Create Cadence`.
6. Sign in as the case owner.
7. Open `/dashboard/advisory/<case_id>`.
8. Confirm the cadence type, next review, agenda, and notes appear.

Advisory history on pond timeline:

1. Create or update an advisory case so it has a `cycle_id` matching an existing pond cycle.
2. Open `/dashboard/pond-timeline/<cycle_id>` as the case owner.
3. Confirm the linked advisory case appears as an `Advisory` timeline event.
4. Click the `Advisory` filter.
5. Confirm only advisory case events remain visible.
6. Click `Open advisory case`.
7. Confirm `/dashboard/advisory/<case_id>` opens.

## Manual Billing

1. Sign in as a user with `role_user=admin`.
2. Open `/dashboard/commercial-admin`.
3. In `Billing`, create an invoice:
   - enter target `user_id`;
   - choose `content_access`, `advisory_case`, or `subscription`;
   - enter amount in IDR;
   - select paid content to unlock when relevant.
4. Confirm the invoice appears under `Recent Invoices` with `issued` status.
5. In `Mark Paid`, select the invoice and enter a payment reference.
6. Submit `Mark Paid`.
7. Confirm the invoice status changes to `paid`.
8. If content was selected, sign in as the target user and confirm the content appears in `/dashboard/library`.
9. As the target user, open `/dashboard/billing` and confirm the invoice appears with status and amount.

## Advisory Report Delivery

V1 report creation is admin-driven.

1. Sign in as a user with `role_user=admin`.
2. Open `/dashboard/commercial-admin`.
3. In `Advisory Cases`, select a target case.
4. Move status from `inquiry` to `awaiting_data` or `in_review` and add expert notes.
5. In `Assistant Brief`, select the same case.
6. Click `Generate Assistant Brief`.
7. Confirm missing data, draft findings, and reference documents appear.
8. Confirm `Document Isolation` shows the attached file count and no unexpected `Needs review` warning.
9. Confirm the reference documents match Teramina knowledge or prior advisory sources relevant to the case.
10. Click `Create Internal Draft Report`.
11. Confirm the created draft report has `expert_review_required` status and is not visible in the client case detail.
12. Click `Use Draft In Report Form`.
13. Confirm the draft sections copy into `Deliver Report` and the backend records the assistant brief as accepted.
14. In `Review Draft Report`, select the internal draft report.
15. Enter a review note and set workflow status to `delivered`.
16. Submit `Update Report Workflow`.
17. Confirm the case status changes to `report_ready`.
18. In `Advisory Audit Trail`, confirm the assistant brief log and report workflow event appear.
19. In `Controlled Assistant`, ask a source-cited internal question.
20. Confirm answer bullets, citations, and any safety flags appear.
21. In `Advisory Audit Trail`, confirm the assistant answer log appears with source and safety-flag counts.
22. Sign in as the case owner.
23. Open `/dashboard/advisory/<case_id>`.
24. Confirm the case status is `report_ready`.
25. Confirm the delivered report summary appears.

## Phase 6 Hatchery And Investor Records

Hatchery intelligence:

1. Sign in as a user with `role_user=admin`.
2. Open `/dashboard/commercial-admin`.
3. In `Hatchery Intelligence`, create a hatchery profile linked to a hatchery advisory case.
4. Set `Client visibility` to `Visible to case owner` only when the profile is approved for client viewing.
5. Confirm the profile appears under `Hatchery Profiles`.
6. Add a hatchery record for one of:
   - `broodstock_batch`;
   - `maturation_performance`;
   - `spawning_log`;
   - `nauplii_output`;
   - `pl_quality_test`.
7. Confirm the KPI fields change to match the selected record type.
8. Set `Record visibility` to `Visible to case owner` only when the record is approved for client viewing.
9. Confirm the record appears under `Recent Hatchery Records`.
10. Click `Edit Hatchery` or `Edit Record`, update at least one field, add a change note, and submit the update.
11. Confirm the updated record appears and `Phase 6 Revisions` shows the change note.
12. Sign in as the case owner and open `/dashboard/advisory/<case_id>`.
13. Confirm only visible hatchery profiles and records appear under `Hatchery Intelligence`.
14. Generate an assistant brief for the linked case.
15. Confirm the brief includes hatchery profile and record context in the draft report data received or findings.

Investor due diligence:

1. Create or select an advisory case with `case_type=investor_due_diligence`.
2. In `Investor Due Diligence`, enter project type, location, planned capacity, cost estimates, five scores, red flags,
   recommendations, and assumptions.
3. Submit `Create Investor Score`.
4. Confirm the record appears under `Recent Investor Scores` with overall score and risk level.
5. Click `Create DD Report`.
6. Confirm a draft report appears with `expert_review_required` status under `Deliver Report`.
7. Set `Score visibility` to `Visible to case owner` only when the score is approved for client viewing.
8. Click `Edit Score`, update at least one score or risk field, add a change note, and submit the update.
9. Confirm the overall score and risk level recalculate and `Phase 6 Revisions` shows the change note.
10. Sign in as the case owner and confirm visible investor scores appear in `/dashboard/advisory/<case_id>`.
11. Generate an assistant brief for the linked investor case.
12. Confirm the brief includes the investor score in the draft report data received or findings.

Phase 6 benchmarks:

1. Sign in as the case owner and open `/dashboard/advisory/<case_id>`.
2. In `Benchmark Consent`, review the anonymized aggregate benchmark terms.
3. Click `Accept Benchmark Terms`.
4. Sign in as an admin and open `/dashboard/commercial-admin`.
5. Confirm `Phase 6 Benchmarks` counts only cases with active owner consent records.
6. Confirm hatchery record-type chips and investor risk-level chips match the consented records.
7. Use the hatchery type, investor risk, project type, and month filters.
8. Confirm `Filtered source cases`, `Total consented`, and `Benchmark Trend` match the selected segment and month range.
9. Sign in again as the case owner, click `Revoke Consent`, and confirm the case leaves the benchmark aggregate.

Client assistant preview:

1. Sign in as the case owner and open a case with a delivered source-cited report.
2. Confirm delivered report citations appear under `Source Citations`.
3. Confirm `Ask Teramina Assistant` appears as disabled and does not allow client questions.

## Regression Checks

Run:

```bash
cd core-be-teramina-main
python -m pytest tests/test_commercial_layer.py -q
python manage.py check
python manage.py reindex_advisory_sources

cd ../fe-teramina-main
npm run test -- src/tests/components/commercial-layer.test.tsx
npm run typecheck
npm run build
```

Use `npm` in local shells where `yarn` is unavailable. CI should continue using the repository lockfile workflow.
