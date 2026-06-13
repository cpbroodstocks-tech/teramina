from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from django.core.management import call_command

from teramina.advisory.models.advisory_model import (
    AdvisoryAssistantAnswerLog,
    AdvisoryAssistantBriefLog,
    AdvisoryCase,
    AdvisoryExpertReview,
    AdvisoryReport,
    AdvisoryReportWorkflowEvent,
    AdvisorySourceEmbedding,
    BenchmarkConsentRecord,
    HatcheryOperationalRecord,
    HatcheryProfile,
    InvestorDueDiligenceScore,
    PhaseSixRecordRevision,
    RetainerCadence,
    ServicePackage,
)
from teramina.advisory.schemas.advisory_schema import (
    AdvisoryAssistantBriefAcceptSchema,
    AdvisoryAssistantAnswerSchema,
    AdvisoryAssistantDraftReportSchema,
    BenchmarkConsentSchema,
    AdvisoryCaseCreateSchema,
    AdvisoryCaseFileSchema,
    AdvisoryCaseUpdateSchema,
    AdvisoryExpertReviewSchema,
    HatcheryOperationalRecordUpdateSchema,
    AdvisoryReportSchema,
    AdvisoryReportWorkflowSchema,
    HatcheryOperationalRecordSchema,
    HatcheryProfileSchema,
    HatcheryProfileUpdateSchema,
    InvestorDueDiligenceReportSchema,
    InvestorDueDiligenceScoreSchema,
    InvestorDueDiligenceScoreUpdateSchema,
    RetainerCadenceSchema,
    ServicePackageSchema,
)
from teramina.advisory.services.advisory_service import AdvisoryService
from teramina.billing.models.billing_model import CommercialInvoice
from teramina.billing.schemas.billing_schema import (
    CommercialInvoiceCreateSchema,
    CommercialInvoicePaidSchema,
    CommercialInvoicePaymentSubmissionSchema,
)
from teramina.billing.services.billing_service import BillingService
from teramina.content.models.content_model import ContentAccess, ContentItem, ContentRevision
from teramina.content.schemas.content_schema import (
    ContentAccessGrantSchema,
    ContentItemSchema,
    ContentItemUpdateSchema,
    ContentWorkflowTransitionSchema,
)
from teramina.content.services.content_service import ContentService
from teramina.content.services.content_pdf_service import build_content_pdf


@pytest.fixture(autouse=True)
def clean_commercial_collections():
    CommercialInvoice.drop_collection()
    ContentAccess.drop_collection()
    ContentRevision.drop_collection()
    ContentItem.drop_collection()
    AdvisoryAssistantBriefLog.drop_collection()
    AdvisoryAssistantAnswerLog.drop_collection()
    AdvisoryReportWorkflowEvent.drop_collection()
    AdvisorySourceEmbedding.drop_collection()
    BenchmarkConsentRecord.drop_collection()
    InvestorDueDiligenceScore.drop_collection()
    PhaseSixRecordRevision.drop_collection()
    HatcheryOperationalRecord.drop_collection()
    HatcheryProfile.drop_collection()
    RetainerCadence.drop_collection()
    AdvisoryExpertReview.drop_collection()
    AdvisoryReport.drop_collection()
    AdvisoryCase.drop_collection()
    ServicePackage.drop_collection()
    yield
    CommercialInvoice.drop_collection()
    ContentAccess.drop_collection()
    ContentRevision.drop_collection()
    ContentItem.drop_collection()
    AdvisoryAssistantBriefLog.drop_collection()
    AdvisoryAssistantAnswerLog.drop_collection()
    AdvisoryReportWorkflowEvent.drop_collection()
    AdvisorySourceEmbedding.drop_collection()
    BenchmarkConsentRecord.drop_collection()
    InvestorDueDiligenceScore.drop_collection()
    PhaseSixRecordRevision.drop_collection()
    HatcheryOperationalRecord.drop_collection()
    HatcheryProfile.drop_collection()
    RetainerCadence.drop_collection()
    AdvisoryExpertReview.drop_collection()
    AdvisoryReport.drop_collection()
    AdvisoryCase.drop_collection()
    ServicePackage.drop_collection()


@pytest.fixture()
def admin_user():
    return SimpleNamespace(id="admin-user", role_user="admin")


@pytest.fixture()
def member_user():
    return SimpleNamespace(id="member-user", role_user="member")


def _published_content(access_level="free"):
    item = ContentItem(
        title="Harvest Economics",
        slug=f"harvest-economics-{access_level}",
        summary="Harvest decision guide",
        category="Economics",
        tags=["harvest"],
        content_type="guide",
        access_level=access_level,
        body_markdown="Full operating guide",
        status="published",
        published_at=datetime.now(),
    )
    item.save()
    return item


class TestContentAccess:
    def test_free_content_returns_body_publicly(self):
        item = _published_content("free")

        code, body = ContentService.get_item(item.slug)

        assert code == 200
        assert body.payload["item"]["access_status"] == "free"
        assert body.payload["item"]["body_markdown"] == "Full operating guide"

    def test_paid_content_without_access_is_locked(self):
        item = _published_content("paid")

        code, body = ContentService.get_item(item.slug, user_id="user-1")

        assert code == 200
        assert body.payload["item"]["access_status"] == "locked"
        assert "body_markdown" not in body.payload["item"]

    def test_paid_content_with_valid_access_returns_body(self):
        item = _published_content("paid")
        ContentAccess(
            user_id="user-1",
            content_id=str(item.id),
            access_source="manual",
        ).save()

        code, body = ContentService.get_item(item.slug, user_id="user-1")

        assert code == 200
        assert body.payload["item"]["access_status"] == "granted"
        assert body.payload["item"]["body_markdown"] == "Full operating guide"

    def test_content_pdf_download_requires_access_and_builds_pdf(self):
        item = _published_content("paid")

        code, locked = ContentService.get_downloadable_item(item.slug, user_id="user-1")

        assert code == 401
        assert locked.message == "Content access required"

        ContentAccess(user_id="user-1", content_id=str(item.id), access_source="manual").save()
        code, downloadable = ContentService.get_downloadable_item(item.slug, user_id="user-1")

        assert code == 200
        pdf_bytes = build_content_pdf(downloadable)
        assert pdf_bytes.startswith(b"%PDF")

    def test_expired_access_does_not_unlock_content(self):
        item = _published_content("paid")
        ContentAccess(
            user_id="user-1",
            content_id=str(item.id),
            access_source="manual",
            expires_at=datetime.now() - timedelta(days=1),
        ).save()

        code, body = ContentService.get_item(item.slug, user_id="user-1")

        assert code == 200
        assert body.payload["item"]["access_status"] == "expired"
        assert "body_markdown" not in body.payload["item"]

    def test_admin_can_grant_manual_access(self, admin_user):
        item = _published_content("paid")

        code, body = ContentService.grant_access(
            admin_user,
            ContentAccessGrantSchema(user_id="user-1", content_id=str(item.id)),
        )

        assert code == 200
        assert body.payload["access"]["content_id"] == str(item.id)
        assert ContentAccess.objects(user_id="user-1", content_id=str(item.id)).first()

    def test_admin_can_list_all_content_and_access_grants(self, admin_user):
        paid = _published_content("paid")
        draft = ContentItem(
            title="Draft SOP",
            slug="draft-sop",
            summary="Admin-only draft",
            category="Hatchery",
            access_level="paid",
            status="draft",
        ).save()
        ContentAccess(user_id="user-1", content_id=str(paid.id), access_source="manual").save()

        code, body = ContentService.admin_list_items(admin_user)

        assert code == 200
        assert {item["slug"] for item in body.payload["items"]} == {paid.slug, draft.slug}

        code, grants = ContentService.admin_list_access(admin_user, user_id="user-1")
        assert code == 200
        assert grants.payload["access"][0]["content_id"] == str(paid.id)
        assert grants.payload["access"][0]["is_valid"] is True

    def test_non_admin_cannot_list_commercial_admin_content(self, member_user):
        code, body = ContentService.admin_list_items(member_user)

        assert code == 401
        assert body.message == "Unauthorized"

    def test_content_create_and_update_write_revision_history(self, admin_user):
        code, created = ContentService.create_item(
            admin_user,
            ContentItemSchema(
                title="Broodstock SOP",
                slug="broodstock-sop",
                summary="Initial summary",
                category="Hatchery",
                access_level="paid",
                body_markdown="Initial body",
                status="draft",
                change_note="Initial draft",
            ),
        )

        assert code == 200
        content_id = created.payload["item"]["id"]
        assert ContentRevision.objects(content_id=content_id).count() == 1

        code, updated = ContentService.update_item(
            admin_user,
            content_id,
            ContentItemUpdateSchema(
                summary="Updated summary",
                body_markdown="Updated body",
                version="1.1",
                change_note="Reviewed technical thresholds",
            ),
        )

        assert code == 200
        assert updated.payload["item"]["summary"] == "Updated summary"

        code, revisions = ContentService.admin_list_revisions(admin_user, content_id)

        assert code == 200
        assert [revision["revision_number"] for revision in revisions.payload["revisions"]] == [2, 1]
        assert revisions.payload["revisions"][0]["version"] == "1.1"
        assert revisions.payload["revisions"][0]["change_note"] == "Reviewed technical thresholds"

    def test_content_variants_support_bilingual_master_and_practical_versions(self, admin_user):
        code, master = ContentService.create_item(
            admin_user,
            ContentItemSchema(
                title="EHP Risk Reduction Master",
                slug="ehp-risk-reduction-master",
                category="Disease",
                language="en",
                variant_group_id="ehp-risk-reduction",
                variant_type="master",
                body_markdown="English technical master",
                status="published",
            ),
        )
        assert code == 200

        code, practical = ContentService.create_item(
            admin_user,
            ContentItemSchema(
                title="Panduan Praktis Risiko EHP",
                slug="panduan-praktis-risiko-ehp",
                category="Disease",
                language="id",
                variant_group_id="ehp-risk-reduction",
                variant_type="practical",
                source_content_id=master.payload["item"]["id"],
                body_markdown="Versi praktis Bahasa Indonesia",
                status="published",
            ),
        )

        assert code == 200
        assert practical.payload["item"]["source_content_id"] == master.payload["item"]["id"]

        code, listed = ContentService.list_items(language="id", variant_group_id="ehp-risk-reduction", variant_type="practical")

        assert code == 200
        assert [item["slug"] for item in listed.payload["items"]] == ["panduan-praktis-risiko-ehp"]
        assert listed.payload["items"][0]["variant_type"] == "practical"

    def test_admin_can_run_content_editorial_workflow(self, admin_user):
        code, created = ContentService.create_item(
            admin_user,
            ContentItemSchema(
                title="Farm Failure Framework",
                slug="farm-failure-framework",
                summary="Draft framework",
                category="Farm",
                access_level="free",
                body_markdown="Draft body",
                status="draft",
            ),
        )
        content_id = created.payload["item"]["id"]

        code, review = ContentService.transition_workflow(
            admin_user,
            content_id,
            ContentWorkflowTransitionSchema(status="in_review", review_note="Ready for technical review"),
        )

        assert code == 200
        assert review.payload["item"]["status"] == "in_review"
        assert review.payload["item"]["submitted_at"]
        code, public = ContentService.get_item("farm-failure-framework")
        assert code == 404

        code, approved = ContentService.transition_workflow(
            admin_user,
            content_id,
            ContentWorkflowTransitionSchema(status="approved", review_note="Approved for publication"),
        )

        assert code == 200
        assert approved.payload["item"]["review_notes"] == "Approved for publication"
        assert approved.payload["item"]["reviewed_by"] == "admin-user"

        code, published = ContentService.transition_workflow(
            admin_user,
            content_id,
            ContentWorkflowTransitionSchema(status="published", review_note="Published after approval"),
        )

        assert code == 200
        assert published.payload["item"]["status"] == "published"
        assert published.payload["item"]["published_at"]
        assert ContentRevision.objects(content_id=content_id).count() == 4

        code, public = ContentService.get_item("farm-failure-framework")
        assert code == 200
        assert public.payload["item"]["body_markdown"] == "Draft body"

    def test_non_admin_cannot_run_content_editorial_workflow(self, member_user):
        item = _published_content("free")

        code, body = ContentService.transition_workflow(
            member_user,
            str(item.id),
            ContentWorkflowTransitionSchema(status="archived", review_note="Block public access"),
        )

        assert code == 401
        assert body.message == "Unauthorized"


class TestAdvisoryWorkflow:
    def test_active_service_packages_are_public(self, admin_user):
        AdvisoryService.create_package(
            admin_user,
            ServicePackageSchema(
                name="Farm Diagnostic Review",
                slug="farm-diagnostic-review",
                segment="farm",
                is_active=True,
            ),
        )
        AdvisoryService.create_package(
            admin_user,
            ServicePackageSchema(
                name="Hidden Package",
                slug="hidden-package",
                segment="farm",
                is_active=False,
            ),
        )

        code, body = AdvisoryService.list_packages()

        assert code == 200
        assert [pkg["slug"] for pkg in body.payload["packages"]] == ["farm-diagnostic-review"]

    def test_user_can_create_and_list_own_case(self):
        data = AdvisoryCaseCreateSchema(
            case_type="farm_diagnostic",
            title="Weak FCR review",
            intake_data={"main_problem": "FCR increased after DOC 50"},
        )

        code, body = AdvisoryService.create_case("user-1", data)

        assert code == 200
        case_id = body.payload["case"]["id"]
        code, own = AdvisoryService.list_cases("user-1")
        assert [case["id"] for case in own.payload["cases"]] == [case_id]
        code, other = AdvisoryService.list_cases("user-2")
        assert other.payload["cases"] == []

    def test_user_can_list_linked_advisory_history_by_cycle(self, member_user):
        _, own_cycle = AdvisoryService.create_case(
            "member-user",
            AdvisoryCaseCreateSchema(
                case_type="farm_diagnostic",
                farm_id="farm-1",
                pond_id="pond-1",
                cycle_id="cycle-1",
                title="DOC 45 mortality review",
            ),
        )
        AdvisoryService.create_case(
            "member-user",
            AdvisoryCaseCreateSchema(
                case_type="crop_planning",
                farm_id="farm-1",
                pond_id="pond-2",
                cycle_id="cycle-2",
                title="Next crop plan",
            ),
        )
        AdvisoryService.create_case(
            "other-user",
            AdvisoryCaseCreateSchema(
                case_type="farm_diagnostic",
                farm_id="farm-1",
                pond_id="pond-1",
                cycle_id="cycle-1",
                title="Other operator case",
            ),
        )

        code, body = AdvisoryService.list_history(member_user, cycle_id="cycle-1")

        assert code == 200
        assert body.payload["total_events"] == 1
        assert body.payload["events"][0]["case_id"] == own_cycle.payload["case"]["id"]
        assert body.payload["events"][0]["type"] == "advisory_case"
        assert body.payload["events"][0]["url"] == f"/dashboard/advisory/{own_cycle.payload['case']['id']}"

    def test_advisory_history_requires_farm_pond_or_cycle_filter(self, member_user):
        code, body = AdvisoryService.list_history(member_user)

        assert code == 400
        assert body.message == "At least one farm, pond, or cycle filter is required"

    def test_admin_can_list_all_cases_with_private_fields(self, admin_user):
        AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Farm case"),
        )
        AdvisoryService.create_case(
            "user-2",
            AdvisoryCaseCreateSchema(case_type="hatchery_review", title="Hatchery case"),
        )

        code, body = AdvisoryService.admin_list_cases(admin_user)

        assert code == 200
        assert {case["user_id"] for case in body.payload["cases"]} == {"user-1", "user-2"}
        assert {case["title"] for case in body.payload["cases"]} == {"Farm case", "Hatchery case"}

    def test_non_admin_cannot_list_all_cases(self, member_user):
        code, body = AdvisoryService.admin_list_cases(member_user)

        assert code == 401
        assert body.message == "Unauthorized"

    def test_user_cannot_read_another_users_case(self):
        code, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Private case"),
        )

        code, error = AdvisoryService.get_case(body.payload["case"]["id"], "user-2")

        assert code == 404
        assert error.message == "Advisory case not found"

    def test_case_owner_can_attach_private_file_reference(self, member_user):
        _, body = AdvisoryService.create_case(
            "member-user",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="File case"),
        )

        code, updated = AdvisoryService.add_case_file(
            member_user,
            body.payload["case"]["id"],
            AdvisoryCaseFileSchema(
                name="Water quality log",
                url="https://storage.example/private/wq-log.csv",
                content_type="text/csv",
                description="DOC 1-50 water quality export",
            ),
        )

        assert code == 200
        assert updated.payload["case"]["uploaded_files"][0]["name"] == "Water quality log"
        assert updated.payload["case"]["uploaded_files"][0]["access_scope"] == "case_private"
        assert updated.payload["case"]["uploaded_files"][0]["file_id"].startswith("case-file-")
        assert "user_id" not in updated.payload["case"]["uploaded_files"][0]

    def test_user_cannot_attach_file_to_another_users_case(self, member_user):
        _, body = AdvisoryService.create_case(
            "other-user",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Other file case"),
        )

        code, error = AdvisoryService.add_case_file(
            member_user,
            body.payload["case"]["id"],
            AdvisoryCaseFileSchema(name="Blocked file", url="https://storage.example/private/file.csv"),
        )

        assert code == 401
        assert error.message == "Unauthorized"

    def test_admin_can_create_delivered_expert_review_visible_to_owner(self, admin_user):
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Expert review case"),
        )

        code, review = AdvisoryService.create_expert_review(
            admin_user,
            AdvisoryExpertReviewSchema(
                case_id=body.payload["case"]["id"],
                review_type="disease",
                summary="Disease pressure is plausible but unconfirmed.",
                findings=["Mortality timeline accelerates after DOC 42"],
                recommendations=["Run PCR confirmation before restart"],
                risk_flags=["No recent lab result"],
                next_actions=["Collect pond-edge shrimp sample"],
                status="delivered",
            ),
        )

        assert code == 200
        assert review.payload["review"]["reviewer_id"] == "admin-user"

        code, case_detail = AdvisoryService.get_case(body.payload["case"]["id"], "user-1")

        assert code == 200
        assert case_detail.payload["expert_reviews"][0]["summary"] == "Disease pressure is plausible but unconfirmed."

    def test_admin_can_create_retainer_cadence_visible_to_owner(self, admin_user):
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="retainer", title="Monthly retainer"),
        )
        next_review = datetime.now() + timedelta(days=14)

        code, cadence = AdvisoryService.create_retainer_cadence(
            admin_user,
            RetainerCadenceSchema(
                case_id=body.payload["case"]["id"],
                cadence_type="biweekly",
                next_review_at=next_review,
                agenda=["Review feed curve", "Check mortality trend"],
                notes="Prepare latest pond logs before the call.",
            ),
        )

        assert code == 200
        assert cadence.payload["cadence"]["cadence_type"] == "biweekly"

        code, case_detail = AdvisoryService.get_case(body.payload["case"]["id"], "user-1")

        assert code == 200
        assert case_detail.payload["retainer_cadences"][0]["agenda"] == ["Review feed curve", "Check mortality trend"]

    def test_admin_can_create_hatchery_profile_and_operational_record(self, admin_user):
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="hatchery_review", title="Maturation performance review"),
        )

        code, profile = AdvisoryService.create_hatchery_profile(
            admin_user,
            HatcheryProfileSchema(
                case_id=body.payload["case"]["id"],
                name="Lampung Nauplii Center",
                location="Lampung",
                maturation_capacity=1200,
                larval_capacity=50000000,
                biosecurity_level="high",
                water_source="filtered seawater",
                client_visible=True,
            ),
        )

        assert code == 200
        assert profile.payload["hatchery"]["user_id"] == "user-1"

        code, record = AdvisoryService.create_hatchery_record(
            admin_user,
            HatcheryOperationalRecordSchema(
                hatchery_id=profile.payload["hatchery"]["id"],
                record_type="pl_quality_test",
                batch_code="PL-2026-06",
                metrics={"pl_quality_score": 82, "pcr_status": "pending"},
                notes="Uniform size, disease result not attached yet.",
                client_visible=True,
            ),
        )

        assert code == 200
        assert record.payload["record"]["case_id"] == body.payload["case"]["id"]
        assert record.payload["record"]["metrics"]["pl_quality_score"] == 82

        code, records = AdvisoryService.admin_list_hatchery_records(admin_user, case_id=body.payload["case"]["id"])

        assert code == 200
        assert records.payload["records"][0]["record_type"] == "pl_quality_test"

        code, updated_profile = AdvisoryService.update_hatchery_profile(
            admin_user,
            profile.payload["hatchery"]["id"],
            HatcheryProfileUpdateSchema(
                case_id=body.payload["case"]["id"],
                name="Lampung Nauplii Center Updated",
                location="Lampung",
                maturation_capacity=1500,
                larval_capacity=50000000,
                biosecurity_level="high",
                water_source="filtered seawater",
                client_visible=True,
                change_note="Capacity review",
            ),
        )

        assert code == 200
        assert updated_profile.payload["hatchery"]["name"] == "Lampung Nauplii Center Updated"
        assert updated_profile.payload["revision"]["revision_number"] == 1
        assert updated_profile.payload["revision"]["previous_data"]["name"] == "Lampung Nauplii Center"

        code, updated_record = AdvisoryService.update_hatchery_record(
            admin_user,
            record.payload["record"]["id"],
            HatcheryOperationalRecordUpdateSchema(
                hatchery_id=profile.payload["hatchery"]["id"],
                record_type="pl_quality_test",
                batch_code="PL-2026-06",
                metrics={"pl_quality_score": 88, "pcr_status": "negative"},
                notes="PCR cleared after follow-up.",
                client_visible=True,
                change_note="PCR result received",
            ),
        )

        assert code == 200
        assert updated_record.payload["record"]["metrics"]["pl_quality_score"] == 88
        assert PhaseSixRecordRevision.objects(record_kind="hatchery_record").count() == 1

        code, revisions = AdvisoryService.admin_list_phase_six_revisions(admin_user, case_id=body.payload["case"]["id"])

        assert code == 200
        assert {revision["record_kind"] for revision in revisions.payload["revisions"]} == {"hatchery_profile", "hatchery_record"}

        code, brief = AdvisoryService.build_assistant_brief(admin_user, body.payload["case"]["id"])

        assert code == 200
        assert "Hatchery operational records: 1" in brief.payload["brief"]["draft_report"]["data_received"]
        assert brief.payload["brief"]["hatchery_profiles"][0]["name"] == "Lampung Nauplii Center Updated"
        assert "Linked hatchery records available: pl_quality_test." in brief.payload["brief"]["draft_report"]["key_findings"]

        code, case_detail = AdvisoryService.get_case(body.payload["case"]["id"], "user-1")

        assert code == 200
        assert case_detail.payload["hatchery_profiles"][0]["name"] == "Lampung Nauplii Center Updated"
        assert case_detail.payload["hatchery_records"][0]["metrics"]["pl_quality_score"] == 88

    def test_admin_can_create_investor_due_diligence_score(self, admin_user):
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(
                case_type="investor_due_diligence",
                title="Integrated farm feasibility",
            ),
        )

        code, score = AdvisoryService.create_investor_due_diligence_score(
            admin_user,
            InvestorDueDiligenceScoreSchema(
                case_id=body.payload["case"]["id"],
                project_type="integrated",
                location="Sulawesi",
                planned_capacity="500 tons/year",
                capex_estimate_idr=20000000000,
                opex_estimate_idr=9000000000,
                technical_score=70,
                management_score=60,
                biosecurity_score=50,
                market_score=80,
                financial_score=65,
                red_flags=["No verified farm manager yet"],
                recommendations=["Validate pond engineering assumptions before investment close"],
                assumptions=["Capex is preliminary"],
                client_visible=True,
            ),
        )

        assert code == 200
        assert score.payload["score"]["overall_score"] == 65
        assert score.payload["score"]["risk_level"] == "moderate"

        code, scores = AdvisoryService.admin_list_investor_due_diligence_scores(admin_user, case_id=body.payload["case"]["id"])

        assert code == 200
        assert scores.payload["scores"][0]["red_flags"] == ["No verified farm manager yet"]

        code, updated_score = AdvisoryService.update_investor_due_diligence_score(
            admin_user,
            score.payload["score"]["id"],
            InvestorDueDiligenceScoreUpdateSchema(
                case_id=body.payload["case"]["id"],
                project_type="integrated",
                location="Sulawesi",
                planned_capacity="500 tons/year",
                capex_estimate_idr=20000000000,
                opex_estimate_idr=9000000000,
                technical_score=82,
                management_score=80,
                biosecurity_score=76,
                market_score=84,
                financial_score=78,
                red_flags=["Engineering assumptions still require validation"],
                recommendations=["Validate pond engineering assumptions before investment close"],
                assumptions=["Capex is preliminary"],
                client_visible=True,
                change_note="Updated after management interview",
            ),
        )

        assert code == 200
        assert updated_score.payload["score"]["overall_score"] == 80
        assert updated_score.payload["score"]["risk_level"] == "low"
        assert updated_score.payload["revision"]["previous_data"]["risk_level"] == "moderate"

        code, brief = AdvisoryService.build_assistant_brief(admin_user, body.payload["case"]["id"])

        assert code == 200
        assert "Investor due-diligence score: 80.0 (low)" in brief.payload["brief"]["draft_report"]["data_received"]
        assert brief.payload["brief"]["investor_scores"][0]["risk_level"] == "low"

        code, report = AdvisoryService.create_report_from_investor_score(
            admin_user,
            score.payload["score"]["id"],
            InvestorDueDiligenceReportSchema(),
        )

        assert code == 200
        assert report.payload["report"]["status"] == "expert_review_required"
        assert "Overall score is 80.0 with low risk." in report.payload["report"]["executive_summary"]
        assert report.payload["report"]["likely_causes"] == ["Engineering assumptions still require validation"]

        code, case_detail = AdvisoryService.get_case(body.payload["case"]["id"], "user-1")

        assert code == 200
        assert case_detail.payload["investor_scores"][0]["overall_score"] == 80.0

    def test_investor_score_requires_investor_case(self, admin_user):
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Farm case"),
        )

        code, error = AdvisoryService.create_investor_due_diligence_score(
            admin_user,
            InvestorDueDiligenceScoreSchema(case_id=body.payload["case"]["id"], technical_score=80),
        )

        assert code == 400
        assert error.message == "Case is not an investor due-diligence case"

    def test_phase_six_benchmarks_use_only_cases_with_active_owner_consent(self, admin_user, member_user):
        _, consented = AdvisoryService.create_case(
            member_user.id,
            AdvisoryCaseCreateSchema(case_type="hatchery_review", title="Consented hatchery case"),
        )
        code, consent = AdvisoryService.accept_benchmark_consent(
            member_user,
            consented.payload["case"]["id"],
            BenchmarkConsentSchema(),
        )
        assert code == 200
        assert consent.payload["benchmark_consent"]["active"] is True
        assert BenchmarkConsentRecord.objects(case_id=consented.payload["case"]["id"], status="active").count() == 1
        _, consented_investor = AdvisoryService.create_case(
            member_user.id,
            AdvisoryCaseCreateSchema(case_type="investor_due_diligence", title="Consented investor case"),
        )
        AdvisoryService.accept_benchmark_consent(
            member_user,
            consented_investor.payload["case"]["id"],
            BenchmarkConsentSchema(),
        )

        _, unconsented = AdvisoryService.create_case(
            "user-2",
            AdvisoryCaseCreateSchema(case_type="hatchery_review", title="Unconsented hatchery case"),
        )

        _, hatchery = AdvisoryService.create_hatchery_profile(
            admin_user,
            HatcheryProfileSchema(case_id=consented.payload["case"]["id"], name="Consented Hatchery"),
        )
        AdvisoryService.create_hatchery_record(
            admin_user,
            HatcheryOperationalRecordSchema(
                hatchery_id=hatchery.payload["hatchery"]["id"],
                record_type="pl_quality_test",
                metrics={"pl_quality_score": 90},
            ),
        )
        AdvisoryService.create_investor_due_diligence_score(
            admin_user,
            InvestorDueDiligenceScoreSchema(
                case_id=consented_investor.payload["case"]["id"],
                project_type="integrated",
                technical_score=60,
                management_score=60,
                biosecurity_score=60,
                market_score=60,
                financial_score=60,
            ),
        )
        _, unconsented_hatchery = AdvisoryService.create_hatchery_profile(
            admin_user,
            HatcheryProfileSchema(case_id=unconsented.payload["case"]["id"], name="Unconsented Hatchery"),
        )
        AdvisoryService.create_hatchery_record(
            admin_user,
            HatcheryOperationalRecordSchema(
                hatchery_id=unconsented_hatchery.payload["hatchery"]["id"],
                record_type="pl_quality_test",
                metrics={"pl_quality_score": 10},
            ),
        )

        code, body = AdvisoryService.admin_phase_six_benchmarks(admin_user)

        assert code == 200
        assert body.payload["source_case_count"] == 2
        assert body.payload["total_consented_case_count"] == 2
        assert body.payload["hatchery"]["record_count"] == 1
        assert body.payload["hatchery"]["average_pl_quality_score"] == 90
        assert body.payload["investor"]["score_count"] == 1
        assert body.payload["investor"]["risk_level_counts"] == {"moderate": 1}
        assert body.payload["trend"][0]["hatchery_record_count"] == 1
        assert body.payload["trend"][0]["investor_score_count"] == 1

        code, filtered = AdvisoryService.admin_phase_six_benchmarks(
            admin_user,
            record_type="pl_quality_test",
            risk_level="moderate",
            project_type="integrated",
        )

        assert code == 200
        assert filtered.payload["filters"]["project_type"] == "integrated"
        assert filtered.payload["hatchery"]["record_count"] == 1
        assert filtered.payload["investor"]["score_count"] == 1

        code, invalid_month = AdvisoryService.admin_phase_six_benchmarks(admin_user, from_month="2026-99")

        assert code == 400
        assert invalid_month.message == "Benchmark month filters must use YYYY-MM format"

        code, detail = AdvisoryService.get_case(consented.payload["case"]["id"], member_user.id)
        assert code == 200
        assert detail.payload["benchmark_consent"]["active"] is True

        code, revoked = AdvisoryService.revoke_benchmark_consent(member_user, consented.payload["case"]["id"])
        assert code == 200
        assert revoked.payload["benchmark_consent"]["active"] is False

        code, empty_benchmark = AdvisoryService.admin_phase_six_benchmarks(admin_user)
        assert code == 200
        assert empty_benchmark.payload["source_case_count"] == 1
        assert empty_benchmark.payload["total_consented_case_count"] == 1
        assert empty_benchmark.payload["hatchery"]["record_count"] == 0

    def test_admin_can_generate_internal_assistant_brief(self, admin_user):
        reference = ContentItem(
            title="Farm Failure Framework",
            slug="farm-failure-framework",
            summary="Reconstruct crop failure timelines and data gaps.",
            category="Farm",
            tags=["diagnostic"],
            status="published",
            published_at=datetime.now(),
        )
        reference.save()
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(
                case_type="farm_diagnostic",
                title="DOC 45 mortality review",
                farm_id="farm-1",
                cycle_id="cycle-1",
                intake_data={
                    "farm_name_location": "Tambak A, Lampung",
                    "main_question": "Mortality increased after DOC 45",
                    "water_quality_summary": "DO dropped at night",
                },
            ),
        )
        AdvisoryService.create_expert_review(
            admin_user,
            AdvisoryExpertReviewSchema(
                case_id=body.payload["case"]["id"],
                findings=["Mortality timeline needs lab confirmation"],
                risk_flags=["No PCR result attached"],
                next_actions=["Request disease test result"],
                status="draft",
            ),
        )
        AdvisoryService.add_case_file(
            admin_user,
            body.payload["case"]["id"],
            AdvisoryCaseFileSchema(name="DOC 45 water log", url="https://storage.example/private/doc-45.csv"),
        )

        code, brief = AdvisoryService.build_assistant_brief(admin_user, body.payload["case"]["id"])

        assert code == 200
        assert brief.payload["brief"]["draft_report"]["title"] == "Assistant Draft: DOC 45 mortality review"
        assert brief.payload["brief"]["brief_log_id"]
        assert "Client question: Mortality increased after DOC 45" in brief.payload["brief"]["draft_report"]["key_findings"]
        assert "No PCR result attached" in brief.payload["brief"]["draft_report"]["likely_causes"]
        assert "Farm Failure Framework" == brief.payload["brief"]["reference_documents"][0]["title"]
        assert brief.payload["brief"]["cited_sources"]["retrieval"] == "mnemon_aligned_advisory_sources"
        assert any(
            source["source_ref"].startswith("content_item:")
            for source in brief.payload["brief"]["draft_report"]["source_citations"]
        )
        content_citation = next(
            source for source in brief.payload["brief"]["draft_report"]["source_citations"] if source["source_ref"].startswith("content_item:")
        )
        assert content_citation["document_id"] == content_citation["source_id"]
        assert content_citation["source_snippet"] == content_citation["snippet"]
        assert AdvisorySourceEmbedding.objects(source_kind="content_item").count() == 1
        assert AdvisoryAssistantBriefLog.objects(case_id=body.payload["case"]["id"]).count() == 1
        brief_log = AdvisoryAssistantBriefLog.objects(id=brief.payload["brief"]["brief_log_id"]).first()
        assert brief_log.generated_by == "admin-user"
        assert any(source["source_ref"].startswith("content_item:") for source in brief_log.source_citations)
        assert brief.payload["brief"]["uploaded_file_checks"]["total_files"] == 1
        assert brief.payload["brief"]["uploaded_file_checks"]["needs_review"] == 0
        assert "Stocking Date" in brief.payload["brief"]["missing_data"]

        code, logs = AdvisoryService.admin_list_assistant_brief_logs(admin_user, case_id=body.payload["case"]["id"])
        assert code == 200
        assert logs.payload["logs"][0]["id"] == brief.payload["brief"]["brief_log_id"]

    def test_assistant_brief_flags_unisolated_legacy_file_metadata(self, admin_user):
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Legacy file case"),
        )
        case = AdvisoryCase.objects(id=body.payload["case"]["id"]).first()
        case.uploaded_files = [{"name": "Legacy sheet", "url": "https://storage.example/private/legacy.csv"}]
        case.save()

        code, brief = AdvisoryService.build_assistant_brief(admin_user, body.payload["case"]["id"])

        assert code == 200
        assert brief.payload["brief"]["uploaded_file_checks"]["needs_review"] == 1
        assert "case_id_mismatch" in brief.payload["brief"]["uploaded_file_checks"]["checks"][0]["issues"]

    def test_admin_can_accept_assistant_brief_audit_log(self, admin_user):
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Accepted draft case"),
        )
        code, brief = AdvisoryService.build_assistant_brief(admin_user, body.payload["case"]["id"])

        assert code == 200

        code, accepted = AdvisoryService.accept_assistant_brief(
            admin_user,
            brief.payload["brief"]["brief_log_id"],
            AdvisoryAssistantBriefAcceptSchema(report_id="report-1"),
        )

        assert code == 200
        assert accepted.payload["brief_log"]["status"] == "accepted"
        assert accepted.payload["brief_log"]["accepted_by"] == "admin-user"
        assert accepted.payload["brief_log"]["accepted_report_id"] == "report-1"

    def test_admin_can_generate_controlled_source_cited_assistant_answer(self, admin_user):
        reference = ContentItem(
            title="Farm Failure Framework",
            slug="farm-failure-framework",
            summary="Reconstruct mortality timelines, data gaps, and likely cause ranking.",
            category="Farm",
            tags=["diagnostic", "mortality"],
            status="published",
            published_at=datetime.now(),
        )
        reference.save()

        code, body = AdvisoryService.answer_assistant_question(
            admin_user,
            AdvisoryAssistantAnswerSchema(question="How should I investigate mortality after DOC 45?"),
        )

        assert code == 200
        assert body.payload["answer"]["status"] == "source_cited_internal_draft"
        assert body.payload["answer"]["source_citations"]
        assert body.payload["answer"]["source_citations"][0]["document_id"]
        assert body.payload["answer"]["source_citations"][0]["source_snippet"]
        assert body.payload["answer"]["safety_flags"] == ["Disease-related guidance requires lab data and expert review before client use."]
        assert body.payload["answer"]["answer_log_id"]
        assert AdvisoryAssistantAnswerLog.objects.count() == 1

        code, logs = AdvisoryService.admin_list_assistant_answer_logs(admin_user)
        assert code == 200
        assert logs.payload["logs"][0]["id"] == body.payload["answer"]["answer_log_id"]
        assert logs.payload["logs"][0]["question"] == "How should I investigate mortality after DOC 45?"
        assert logs.payload["logs"][0]["source_citations"][0]["document_id"]

    def test_admin_can_create_internal_cited_draft_report_from_assistant_brief(self, admin_user):
        reference = ContentItem(
            title="Farm Failure Framework",
            slug="farm-failure-framework",
            summary="Reconstruct crop failure timelines and data gaps.",
            category="Farm",
            tags=["diagnostic"],
            status="published",
            published_at=datetime.now(),
        )
        reference.save()
        _, body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(
                case_type="farm_diagnostic",
                title="Internal cited draft case",
                intake_data={"main_question": "Why did survival drop after DOC 40?"},
            ),
        )
        _, brief = AdvisoryService.build_assistant_brief(admin_user, body.payload["case"]["id"])

        code, draft = AdvisoryService.create_report_from_assistant_brief(
            admin_user,
            brief.payload["brief"]["brief_log_id"],
            AdvisoryAssistantDraftReportSchema(),
        )

        assert code == 200
        assert draft.payload["report"]["status"] == "expert_review_required"
        assert draft.payload["report"]["generated_from_brief_log_id"] == brief.payload["brief"]["brief_log_id"]
        assert draft.payload["report"]["source_citations"]
        assert draft.payload["brief_log"]["status"] == "accepted"
        case = AdvisoryCase.objects(id=body.payload["case"]["id"]).first()
        assert case.status == "in_review"
        assert case.report_id == draft.payload["report"]["id"]

        code, case_detail = AdvisoryService.get_case(body.payload["case"]["id"], "user-1")
        assert code == 200
        assert case_detail.payload["report"] is None

        code, error = AdvisoryService.get_report(draft.payload["report"]["id"], "user-1")
        assert code == 404
        assert error.message == "Advisory report not found"

        code, delivered = AdvisoryService.update_report_workflow(
            admin_user,
            draft.payload["report"]["id"],
            AdvisoryReportWorkflowSchema(status="delivered", review_note="Expert reviewed and cleared for client delivery."),
        )

        assert code == 200
        assert delivered.payload["report"]["status"] == "delivered"
        assert delivered.payload["report"]["reviewed_by"] == "admin-user"
        assert delivered.payload["case"]["status"] == "report_ready"
        assert AdvisorySourceEmbedding.objects(source_kind="advisory_report").count() == 1
        assert AdvisoryReportWorkflowEvent.objects(report_id=draft.payload["report"]["id"]).count() == 2

        code, events = AdvisoryService.admin_list_report_workflow_events(admin_user, report_id=draft.payload["report"]["id"])
        assert code == 200
        assert events.payload["events"][0]["previous_status"] == "expert_review_required"
        assert events.payload["events"][0]["new_status"] == "delivered"

        code, case_detail = AdvisoryService.get_case(body.payload["case"]["id"], "user-1")
        assert code == 200
        assert case_detail.payload["report"]["id"] == draft.payload["report"]["id"]

    def test_non_admin_cannot_generate_internal_assistant_brief(self, member_user):
        _, body = AdvisoryService.create_case(
            "member-user",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Private assistant case"),
        )

        code, error = AdvisoryService.build_assistant_brief(member_user, body.payload["case"]["id"])

        assert code == 401
        assert error.message == "Unauthorized"

    def test_delivered_report_marks_case_ready_and_is_owner_scoped(self, admin_user):
        _, case_body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(case_type="farm_diagnostic", title="Report case"),
        )

        code, body = AdvisoryService.create_report(
            admin_user,
            AdvisoryReportSchema(
                case_id=case_body.payload["case"]["id"],
                title="Diagnostic Report",
                executive_summary="Likely oxygen pressure issue.",
                status="delivered",
            ),
        )

        assert code == 200
        report_id = body.payload["report"]["id"]
        case = AdvisoryCase.objects(id=case_body.payload["case"]["id"]).first()
        assert case.status == "report_ready"
        assert case.report_id == report_id

        code, own = AdvisoryService.get_report(report_id, "user-1")
        assert code == 200
        assert own.payload["report"]["title"] == "Diagnostic Report"
        code, other = AdvisoryService.get_report(report_id, "user-2")
        assert code == 404


class TestBillingWorkflow:
    def test_admin_can_create_invoice_and_mark_paid_to_grant_access(self, admin_user):
        item = _published_content("paid")

        code, created = BillingService.create_invoice(
            admin_user,
            CommercialInvoiceCreateSchema(
                user_id="user-1",
                invoice_type="content_access",
                description="Paid library access",
                amount_idr=500000,
                content_ids=[str(item.id)],
            ),
        )

        assert code == 200
        invoice_id = created.payload["invoice"]["id"]
        assert created.payload["invoice"]["status"] == "issued"

        code, paid = BillingService.mark_invoice_paid(
            admin_user,
            invoice_id,
            CommercialInvoicePaidSchema(payment_reference="BANK-123"),
        )

        assert code == 200
        assert paid.payload["invoice"]["status"] == "paid"
        assert paid.payload["access_grants"][0]["access_source"] == "invoice_paid"

        code, content = ContentService.get_item(item.slug, user_id="user-1")
        assert code == 200
        assert content.payload["item"]["access_status"] == "granted"
        assert content.payload["item"]["body_markdown"] == "Full operating guide"

    def test_user_can_list_only_own_invoices(self, admin_user):
        BillingService.create_invoice(
            admin_user,
            CommercialInvoiceCreateSchema(
                user_id="user-1",
                description="User 1 invoice",
                amount_idr=100000,
            ),
        )
        BillingService.create_invoice(
            admin_user,
            CommercialInvoiceCreateSchema(
                user_id="user-2",
                description="User 2 invoice",
                amount_idr=200000,
            ),
        )

        code, body = BillingService.list_my_invoices("user-1")

        assert code == 200
        assert [invoice["description"] for invoice in body.payload["invoices"]] == ["User 1 invoice"]

    def test_user_can_submit_manual_payment_for_verification(self, admin_user):
        _, created = BillingService.create_invoice(
            admin_user,
            CommercialInvoiceCreateSchema(
                user_id="user-1",
                description="Advisory invoice",
                amount_idr=750000,
            ),
        )

        code, submitted = BillingService.submit_invoice_payment(
            "user-1",
            created.payload["invoice"]["id"],
            CommercialInvoicePaymentSubmissionSchema(
                payment_reference="BANK-TRANSFER-123",
                payment_proof_url="https://storage.example/proof.png",
            ),
        )

        assert code == 200
        assert submitted.payload["invoice"]["status"] == "payment_submitted"
        assert submitted.payload["invoice"]["payment_reference"] == "BANK-TRANSFER-123"

    def test_non_admin_cannot_create_invoice(self, member_user):
        code, body = BillingService.create_invoice(
            member_user,
            CommercialInvoiceCreateSchema(
                user_id="user-1",
                description="Blocked invoice",
                amount_idr=100000,
            ),
        )

        assert code == 401
        assert body.message == "Unauthorized"


class TestCommercialSeedCommand:
    def test_seed_commercial_layer_is_idempotent(self):
        call_command("seed_commercial_layer")

        assert ServicePackage.objects.count() == 6
        assert ContentItem.objects.count() == 4
        assert ServicePackage.objects(slug="farm-diagnostic-review", is_active=True).first()
        assert ContentItem.objects(slug="farm-failure-post-mortem-framework", status="published").first()

        call_command("seed_commercial_layer")

        assert ServicePackage.objects.count() == 6
        assert ContentItem.objects.count() == 4

    def test_reindex_advisory_sources_indexes_published_and_delivered_records(self, admin_user):
        _published_content("free")
        _, case_body = AdvisoryService.create_case(
            "user-1",
            AdvisoryCaseCreateSchema(
                case_type="farm_diagnostic",
                title="Reindex case",
                farm_id="farm-1",
                pond_id="pond-1",
                cycle_id="cycle-1",
            ),
        )
        AdvisoryService.create_report(
            admin_user,
            AdvisoryReportSchema(
                case_id=case_body.payload["case"]["id"],
                title="Delivered report",
                executive_summary="Weak survival linked to water quality volatility.",
                status="delivered",
            ),
        )
        AdvisoryService.create_expert_review(
            admin_user,
            AdvisoryExpertReviewSchema(
                case_id=case_body.payload["case"]["id"],
                summary="Expert review summary",
                findings=["Night oxygen pressure is likely."],
                status="delivered",
            ),
        )

        call_command("reindex_advisory_sources", clear=True)

        assert AdvisorySourceEmbedding.objects(source_kind="content_item").count() == 1
        assert AdvisorySourceEmbedding.objects(source_kind="advisory_report").count() == 1
        assert AdvisorySourceEmbedding.objects(source_kind="expert_review").count() == 1
