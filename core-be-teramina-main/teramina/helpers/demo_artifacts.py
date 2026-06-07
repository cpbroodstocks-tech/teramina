"""User-linked artifacts for the synchronized onboarding demo bundle."""

from datetime import datetime, timedelta

from teramina.advisory.models.advisory_model import (
    AdvisoryCase,
    AdvisoryExpertReview,
    AdvisoryReport,
    ServicePackage,
)
from teramina.agent.models.agent_model import (
    AgentMemory,
    FarmAlert,
    MemoryEmbedding,
    MemoryEntity,
    MemoryObservation,
    MemoryRelation,
    WorkflowTask,
)
from teramina.agent.services.memory_retrieval import (
    LocalHashEmbeddingProvider,
    index_agent_memory,
    index_memory_observation,
)
from teramina.content.models.content_model import ContentAccess, ContentItem


DEMO_BUNDLE_VERSION = "abw-v2"
DEMO_TAG = f"demo_bundle:{DEMO_BUNDLE_VERSION}"


def _clear_user_artifacts(user_id: str):
    FarmAlert.objects(user_id=user_id, data__demo_bundle_version=DEMO_BUNDLE_VERSION).delete()
    WorkflowTask.objects(user_id=user_id, title__startswith="[Demo]").delete()

    memories = list(AgentMemory.objects(user_id=user_id, tags=DEMO_TAG).only("id"))
    memory_refs = [f"agent_memory:{memory.id}" for memory in memories]
    observations = list(MemoryObservation.objects(user_id=user_id, source_ref__startswith=DEMO_TAG).only("id"))
    observation_refs = [f"memory_observation:{observation.id}" for observation in observations]
    MemoryEmbedding.objects(source_ref__in=memory_refs + observation_refs).delete()
    AgentMemory.objects(user_id=user_id, tags=DEMO_TAG).delete()
    MemoryObservation.objects(user_id=user_id, source_ref__startswith=DEMO_TAG).delete()
    MemoryRelation.objects(user_id=user_id, source_ref__startswith=DEMO_TAG).delete()
    MemoryEntity.objects(user_id=user_id, metadata__demo_bundle_version=DEMO_BUNDLE_VERSION).delete()

    cases = list(AdvisoryCase.objects(user_id=user_id, intake_data__demo_bundle_version=DEMO_BUNDLE_VERSION).only("id"))
    case_ids = [str(case.id) for case in cases]
    AdvisoryReport.objects(user_id=user_id, case_id__in=case_ids).delete()
    AdvisoryExpertReview.objects(user_id=user_id, case_id__in=case_ids).delete()
    AdvisoryCase.objects(user_id=user_id, intake_data__demo_bundle_version=DEMO_BUNDLE_VERSION).delete()

def _create_memory(user_id: str, farm_id: str, pond_id: str, cycle_id: str, content: str, tags: list[str]):
    memory = AgentMemory(
        user_id=user_id,
        farm_id=farm_id,
        pond_id=pond_id,
        cycle_id=cycle_id,
        memory_type="event",
        content=content,
        tags=[DEMO_TAG, *tags],
        source="system_observation",
        confidence=0.9,
        is_verified=True,
    ).save()
    provider = LocalHashEmbeddingProvider()
    index_agent_memory(memory, provider)
    return memory


def seed_user_demo_artifacts(user_id: str, farm_id: str, scenarios: dict[str, dict[str, str]]) -> dict:
    """Create deterministic Today, Memory, Library, and Advisory demo records."""
    _clear_user_artifacts(user_id)
    now = datetime.utcnow()
    healthy = scenarios["healthy"]
    at_risk = scenarios["at_risk"]

    alert = FarmAlert(
        user_id=user_id,
        farm_id=farm_id,
        cycle_id=at_risk["cycle_id"],
        alert_type="water_quality",
        severity="critical",
        message="Scenario B: DO is declining while NH3 and feed leftovers are rising.",
        data={"demo_bundle_version": DEMO_BUNDLE_VERSION, "scenario": "at_risk"},
        expires_at=now + timedelta(days=30),
    ).save()
    task = WorkflowTask(
        user_id=user_id,
        farm_id=farm_id,
        pond_id=at_risk["pond_id"],
        cycle_id=at_risk["cycle_id"],
        task_type="check",
        title="[Demo] Check aeration and reduce feed in Scenario B",
        description="Verify DO before the next feeding and reduce the ration if leftovers persist.",
        due_at=now + timedelta(hours=4),
        source_alert_id=str(alert.id),
    ).save()
    alert.follow_up_task_id = str(task.id)
    alert.save()
    WorkflowTask(
        user_id=user_id,
        farm_id=farm_id,
        pond_id=healthy["pond_id"],
        cycle_id=healthy["cycle_id"],
        task_type="reminder",
        title="[Demo] Record Scenario A morning water quality",
        description="Keep the healthy scenario current for comparison.",
        due_at=now + timedelta(hours=8),
    ).save()

    healthy_memory = _create_memory(
        user_id,
        farm_id,
        healthy["pond_id"],
        healthy["cycle_id"],
        "Scenario A maintains stable oxygen, efficient feed conversion, and on-plan growth through DOC 60.",
        ["scenario:healthy", "growth", "feeding"],
    )
    risk_memory = _create_memory(
        user_id,
        farm_id,
        at_risk["pond_id"],
        at_risk["cycle_id"],
        "Scenario B shows a recurring low-DO pattern with elevated NH3, feed leftovers, and slower growth after DOC 45.",
        ["scenario:at_risk", "low_do", "nh3", "feeding"],
    )

    farm_entity = MemoryEntity(
        user_id=user_id,
        farm_id=farm_id,
        entity_type="farm",
        canonical_name="Demo A/B Farm",
        metadata={"demo_bundle_version": DEMO_BUNDLE_VERSION},
    ).save()
    for scenario_key, scenario, memory, observation_type in (
        ("healthy", healthy, healthy_memory, "outcome"),
        ("at_risk", at_risk, risk_memory, "risk_pattern"),
    ):
        pond_entity = MemoryEntity(
            user_id=user_id,
            farm_id=farm_id,
            entity_type="pond",
            canonical_name=scenario["pond_name"],
            metadata={"demo_bundle_version": DEMO_BUNDLE_VERSION, "scenario": scenario_key},
        ).save()
        MemoryRelation(
            user_id=user_id,
            farm_id=farm_id,
            source_entity_id=str(farm_entity.id),
            relation_type="contains",
            target_entity_id=str(pond_entity.id),
            confidence=1.0,
            source_type="imported_data",
            source_ref=f"{DEMO_TAG}:{scenario_key}",
        ).save()
        observation = MemoryObservation(
            user_id=user_id,
            farm_id=farm_id,
            pond_id=scenario["pond_id"],
            cycle_id=scenario["cycle_id"],
            entity_id=str(pond_entity.id),
            observation_type=observation_type,
            content=memory.content,
            structured_data={"demo_bundle_version": DEMO_BUNDLE_VERSION, "scenario": scenario_key},
            confidence=0.9,
            importance=4,
            source_type="imported_data",
            source_ref=f"{DEMO_TAG}:{scenario_key}",
            is_verified=True,
        ).save()
        index_memory_observation(observation, LocalHashEmbeddingProvider())

    granted_content = 0
    for item in ContentItem.objects(slug__in=["harvest-timing-price-size-economics", "farm-failure-post-mortem-framework"]):
        if not ContentAccess.objects(user_id=user_id, content_id=str(item.id)).first():
            ContentAccess(
                user_id=user_id,
                content_id=str(item.id),
                access_source="admin_grant",
            ).save()
        granted_content += 1

    package = ServicePackage.objects(slug="farm-diagnostic-review", is_active=True).first()
    case = AdvisoryCase(
        user_id=user_id,
        service_package_id=str(package.id) if package else "",
        case_type="farm_diagnostic",
        status="report_ready",
        farm_id=farm_id,
        pond_id=at_risk["pond_id"],
        cycle_id=at_risk["cycle_id"],
        title="Scenario B At-Risk Crop Diagnostic",
        intake_data={
            "demo_bundle_version": DEMO_BUNDLE_VERSION,
            "farm_name_location": "Demo A/B Farm, Jawa Timur",
            "stocking_date": "Rolling active demo cycle",
            "pond_size": "3000 m2",
            "stocking_density": "120 PL/m2",
            "pl_source": "Demo source",
            "feed_data_summary": "Feed leftovers increase after DOC 45.",
            "water_quality_summary": "DO declines while NH3 rises after DOC 45.",
            "mortality_timeline": "Mortality pressure increases late in the observed window.",
            "disease_test_results": "No test result supplied in demo.",
            "main_question": "How should the team stabilize Scenario B and protect margin?",
        },
    ).save()
    report = AdvisoryReport(
        case_id=str(case.id),
        user_id=user_id,
        title="Scenario B Corrective Action Plan",
        executive_summary="Scenario B requires immediate oxygen and feeding controls before growth and margin deteriorate further.",
        data_received=["Daily water quality", "Feed realization", "Growth", "Mortality", "Cost records"],
        key_findings=["DO pressure after DOC 45", "Rising NH3", "Feed leftovers above target", "Cost/kg above Scenario A"],
        likely_causes=["Insufficient aeration response", "Feeding not adjusted to appetite and water quality"],
        technical_interpretation="Water-quality pressure and excess feed reinforce each other and suppress growth.",
        economic_implication="Continuing unchanged increases FCR, cost/kg, and downside risk before harvest.",
        corrective_action_plan=["Verify aeration capacity", "Reduce feed 10-15%", "Measure DO before feeding", "Review NH3 daily"],
        monitoring_plan=["Compare Scenario A and B daily", "Escalate if DO remains below target"],
        assumptions_and_limits=["Demonstration report generated from deterministic onboarding data."],
        status="delivered",
        reviewed_by="demo-system",
        reviewed_at=now,
        delivered_at=now,
    ).save()
    AdvisoryExpertReview(
        case_id=str(case.id),
        user_id=user_id,
        reviewer_id="demo-system",
        review_type="technical",
        summary="Prioritize oxygen stability and appetite-based feeding.",
        findings=list(report.key_findings),
        recommendations=list(report.corrective_action_plan),
        risk_flags=["low_do", "rising_nh3", "feed_leftover"],
        next_actions=["Complete the linked Today task", "Recheck the forecast after corrective action"],
        status="delivered",
        delivered_at=now,
    ).save()
    case.report_id = str(report.id)
    case.save()

    return {
        "alerts": 1,
        "tasks": 2,
        "memories": 2,
        "content_access": granted_content,
        "advisory_cases": 1,
    }
