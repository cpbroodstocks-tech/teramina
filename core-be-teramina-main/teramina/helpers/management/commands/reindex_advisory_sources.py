from django.core.management.base import BaseCommand

from teramina.advisory.models.advisory_model import (
    AdvisoryCase,
    AdvisoryExpertReview,
    AdvisoryReport,
    AdvisorySourceEmbedding,
)
from teramina.advisory.services.advisory_retrieval_service import AdvisoryRetrievalService
from teramina.content.models.content_model import ContentItem


class Command(BaseCommand):
    help = "Rebuild Mnemon-aligned advisory source embeddings from published knowledge and delivered advisory records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Drop existing advisory source embeddings before rebuilding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            AdvisorySourceEmbedding.drop_collection()

        content_count = self._index_content()
        report_count = self._index_reports()
        review_count = self._index_expert_reviews()

        self.stdout.write(self.style.SUCCESS(
            "Reindexed advisory sources: "
            f"content={content_count}, reports={report_count}, expert_reviews={review_count}, "
            f"total={content_count + report_count + review_count}"
        ))

    def _index_content(self):
        count = 0
        for item in ContentItem.objects(status="published").order_by("-published_at", "title"):
            AdvisoryRetrievalService.index_content_item(item)
            count += 1
        return count

    def _index_reports(self):
        count = 0
        for report in AdvisoryReport.objects(status="delivered").order_by("-created_at"):
            case = AdvisoryCase.objects(id=report.case_id).first()
            if not case:
                continue
            AdvisoryRetrievalService.index_report(report, case)
            count += 1
        return count

    def _index_expert_reviews(self):
        count = 0
        for review in AdvisoryExpertReview.objects(status="delivered").order_by("-created_at"):
            case = AdvisoryCase.objects(id=review.case_id).first()
            if not case:
                continue
            AdvisoryRetrievalService.index_expert_review(review, case)
            count += 1
        return count
