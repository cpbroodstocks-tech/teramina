from datetime import datetime

from teramina.agent.services.memory_retrieval import (
    DEFAULT_EMBEDDING_MODEL,
    LocalHashEmbeddingProvider,
    _content_hash,
    _cosine_similarity,
    _lexical_score,
    _normalize_embedding,
)
from teramina.content.models.content_model import ContentItem

from ..models.advisory_model import (
    AdvisoryCase,
    AdvisoryExpertReview,
    AdvisoryReport,
    AdvisorySourceEmbedding,
)

SOURCE_CATEGORIES = {
    "farm_diagnostic": ["Farm", "Disease", "Management"],
    "crop_planning": ["Farm", "Economics", "Management"],
    "hatchery_review": ["Hatchery", "Management"],
    "procurement_advisory": ["Genetics", "Hatchery", "Farm"],
    "investor_due_diligence": ["Economics", "Management", "Farm"],
    "retainer": ["Management", "Farm", "Hatchery"],
}


def _text_join(parts):
    return "\n".join(str(part) for part in parts if part)


def _snippet(text, limit=260):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else f"{text[:limit].rstrip()}..."


class AdvisoryRetrievalService:
    """Mnemon-aligned retrieval for commercial knowledge and advisory records."""

    @staticmethod
    def retrieve_global(query: str, limit=6, provider=None):
        AdvisoryRetrievalService._refresh_global_sources(provider=provider)
        sources = AdvisorySourceEmbedding.objects(access_scope="global")
        return AdvisoryRetrievalService._rank_sources(
            list(sources),
            query=query,
            limit=limit,
            provider=provider,
        )

    @staticmethod
    def retrieve_for_case(case: AdvisoryCase, query: str, limit=6, provider=None):
        AdvisoryRetrievalService._refresh_case_sources(case, provider=provider)
        sources = AdvisorySourceEmbedding.objects(
            __raw__={
                "$or": [
                    {"access_scope": "global"},
                    {"access_scope": "case_private", "user_id": case.user_id},
                ]
            }
        )
        return AdvisoryRetrievalService._rank_sources(
            list(sources),
            query=query,
            limit=limit,
            provider=provider,
        )

    @staticmethod
    def _refresh_global_sources(provider=None):
        for item in ContentItem.objects(status="published").order_by("-published_at", "title")[:100]:
            AdvisoryRetrievalService.index_content_item(item, provider=provider)

    @staticmethod
    def _refresh_case_sources(case: AdvisoryCase, provider=None):
        categories = SOURCE_CATEGORIES.get(case.case_type, [])
        content_query = {"status": "published"}
        if categories:
            content_query["category__in"] = categories
        for item in ContentItem.objects(**content_query).order_by("-published_at", "title")[:50]:
            AdvisoryRetrievalService.index_content_item(item, provider=provider)

        for report in AdvisoryReport.objects(user_id=case.user_id).order_by("-created_at")[:50]:
            report_case = AdvisoryCase.objects(id=report.case_id).first()
            if report_case and AdvisoryRetrievalService._is_related_case(case, report_case):
                AdvisoryRetrievalService.index_report(report, report_case, provider=provider)

        for review in AdvisoryExpertReview.objects(user_id=case.user_id).order_by("-created_at")[:50]:
            review_case = AdvisoryCase.objects(id=review.case_id).first()
            if review_case and AdvisoryRetrievalService._is_related_case(case, review_case):
                AdvisoryRetrievalService.index_expert_review(review, review_case, provider=provider)

    @staticmethod
    def _is_related_case(current: AdvisoryCase, other: AdvisoryCase):
        if str(current.id) == str(other.id):
            return True
        if current.cycle_id and current.cycle_id == other.cycle_id:
            return True
        if current.pond_id and current.pond_id == other.pond_id:
            return True
        return bool(current.farm_id and current.farm_id == other.farm_id)

    @staticmethod
    def index_content_item(item: ContentItem, provider=None):
        content = _text_join([
            item.title,
            item.summary,
            item.category,
            " ".join(item.tags or []),
            item.body_markdown,
        ])
        return AdvisoryRetrievalService._upsert_source(
            source_ref=f"content_item:{item.id}",
            source_kind="content_item",
            source_id=str(item.id),
            title=item.title,
            category=item.category,
            snippet=_snippet(item.summary or item.body_markdown),
            content=content,
            access_scope="global",
            access_level=item.access_level,
            language=item.language,
            url=f"/knowledge/{item.slug}",
            provider=provider,
        )

    @staticmethod
    def index_report(report: AdvisoryReport, case: AdvisoryCase, provider=None):
        content = _text_join([
            report.title,
            report.executive_summary,
            " ".join(report.data_received or []),
            " ".join(report.key_findings or []),
            " ".join(report.likely_causes or []),
            report.technical_interpretation,
            report.economic_implication,
            " ".join(report.corrective_action_plan or []),
            " ".join(report.monitoring_plan or []),
            " ".join(report.assumptions_and_limits or []),
        ])
        return AdvisoryRetrievalService._upsert_source(
            source_ref=f"advisory_report:{report.id}",
            source_kind="advisory_report",
            source_id=str(report.id),
            title=report.title,
            category="Advisory Report",
            snippet=_snippet(report.executive_summary or " ".join(report.key_findings or [])),
            content=content,
            user_id=report.user_id,
            case_id=report.case_id,
            farm_id=case.farm_id,
            pond_id=case.pond_id,
            cycle_id=case.cycle_id,
            access_scope="case_private",
            access_level="client",
            url=f"/dashboard/advisory/{report.case_id}",
            provider=provider,
        )

    @staticmethod
    def index_expert_review(review: AdvisoryExpertReview, case: AdvisoryCase, provider=None):
        content = _text_join([
            review.review_type,
            review.summary,
            " ".join(review.findings or []),
            " ".join(review.recommendations or []),
            " ".join(review.risk_flags or []),
            " ".join(review.next_actions or []),
        ])
        return AdvisoryRetrievalService._upsert_source(
            source_ref=f"expert_review:{review.id}",
            source_kind="expert_review",
            source_id=str(review.id),
            title=f"{review.review_type.title()} expert review",
            category="Expert Review",
            snippet=_snippet(review.summary or " ".join(review.findings or [])),
            content=content,
            user_id=review.user_id,
            case_id=review.case_id,
            farm_id=case.farm_id,
            pond_id=case.pond_id,
            cycle_id=case.cycle_id,
            access_scope="case_private",
            access_level="admin",
            url=f"/dashboard/advisory/{review.case_id}",
            provider=provider,
        )

    @staticmethod
    def _upsert_source(provider=None, **data):
        content = data.get("content") or ""
        embedding, model = AdvisoryRetrievalService._embed(content, provider=provider)
        AdvisorySourceEmbedding.objects(source_ref=data["source_ref"]).update_one(
            set__source_kind=data["source_kind"],
            set__source_id=data["source_id"],
            set__title=data.get("title", ""),
            set__category=data.get("category", ""),
            set__snippet=data.get("snippet", ""),
            set__content=content,
            set__user_id=data.get("user_id", ""),
            set__case_id=data.get("case_id", ""),
            set__farm_id=data.get("farm_id", ""),
            set__pond_id=data.get("pond_id", ""),
            set__cycle_id=data.get("cycle_id", ""),
            set__access_scope=data.get("access_scope", "global"),
            set__access_level=data.get("access_level", ""),
            set__language=data.get("language", ""),
            set__url=data.get("url", ""),
            set__embedding=embedding,
            set__embedding_model=model,
            set__content_hash=_content_hash(content),
            set__updated_at=datetime.now(),
            set_on_insert__created_at=datetime.now(),
            upsert=True,
        )
        return AdvisorySourceEmbedding.objects(source_ref=data["source_ref"]).first()

    @staticmethod
    def _embed(text, provider=None):
        if provider is None:
            provider = LocalHashEmbeddingProvider()
        embedding = _normalize_embedding(provider.embed([text])[0])
        model = getattr(provider, "model", DEFAULT_EMBEDDING_MODEL)
        return embedding, model

    @staticmethod
    def _rank_sources(sources, query: str, limit=6, provider=None):
        query_embedding, _ = AdvisoryRetrievalService._embed(query or "", provider=provider)
        ranked = []
        for source in sources:
            semantic = _cosine_similarity(query_embedding, source.embedding)
            lexical = _lexical_score(query, _text_join([source.title, source.snippet, source.content]))
            score = semantic + lexical
            ranked.append((score, source))
        ranked.sort(key=lambda item: (item[0], item[1].updated_at or datetime.min), reverse=True)
        citations = [source.to_citation(score=score) for score, source in ranked[:limit] if score > 0]
        return {
            "retrieval": "mnemon_aligned_advisory_sources",
            "query": query,
            "count": len(citations),
            "citations": citations,
        }
