from datetime import datetime

from django.core.management.base import BaseCommand

from teramina.advisory.models.advisory_model import ServicePackage
from teramina.content.models.content_model import ContentItem


SERVICE_PACKAGES = [
    {
        "name": "Farm Diagnostic Review",
        "slug": "farm-diagnostic-review",
        "segment": "farm",
        "description": "Structured second opinion for weak crop performance, mortality events, poor FCR, or failed harvest outcomes.",
        "deliverables": ["60-90 minute review call", "Likely cause ranking", "Next-cycle corrective plan", "Management checklist"],
        "required_data": ["Stocking and PL source", "Feed and water quality logs", "Mortality timeline", "Harvest or current biomass data"],
        "price_min_idr": 3_000_000,
        "price_max_idr": 10_000_000,
        "sort_order": 10,
    },
    {
        "name": "Crop Planning Review",
        "slug": "crop-planning-review",
        "segment": "farm",
        "description": "Pre-stocking review of density, feed, aeration, survival, FCR, harvest-size strategy, and economic assumptions.",
        "deliverables": ["Stocking density recommendation", "Crop economics model", "Harvest-size strategy", "Risk checklist"],
        "required_data": ["Pond profile", "PL source", "Cost assumptions", "Target harvest size and market price"],
        "price_min_idr": 5_000_000,
        "price_max_idr": 20_000_000,
        "sort_order": 20,
    },
    {
        "name": "Hatchery Performance Review",
        "slug": "hatchery-performance-review",
        "segment": "hatchery",
        "description": "Review of broodstock handling, maturation KPIs, nauplii output, PL quality, and disease-control discipline.",
        "deliverables": ["KPI review", "Operational risk map", "Corrective action priorities", "Follow-up metric plan"],
        "required_data": ["Broodstock source", "Mating/spawning/hatching data", "PL quality data", "Disease test protocol"],
        "price_min_idr": 10_000_000,
        "price_max_idr": 50_000_000,
        "sort_order": 30,
    },
    {
        "name": "Broodstock/PL Procurement Advisory",
        "slug": "broodstock-pl-procurement-advisory",
        "segment": "hatchery",
        "description": "Supplier comparison, trait-fit review, risk checklist, procurement planning, and receiving SOP support.",
        "deliverables": ["Supplier comparison", "Trait fit analysis", "Procurement plan", "Receiving checklist"],
        "required_data": ["Target market", "Supplier options", "Production goals", "Known disease or quality constraints"],
        "price_min_idr": 5_000_000,
        "price_max_idr": 25_000_000,
        "sort_order": 40,
    },
    {
        "name": "Investor Technical Due Diligence",
        "slug": "investor-technical-due-diligence",
        "segment": "investor",
        "description": "Technical risk and economics review for shrimp farm, hatchery, or integrated aquaculture investments.",
        "deliverables": ["Feasibility review", "Capex/opex sanity check", "Technical risk scoring", "Go/no-go opinion"],
        "required_data": ["Project plan", "Location and capacity", "Capex/opex estimates", "Management assumptions"],
        "price_min_idr": 30_000_000,
        "price_max_idr": 150_000_000,
        "sort_order": 50,
    },
    {
        "name": "Monthly Advisory Retainer",
        "slug": "monthly-advisory-retainer",
        "segment": "retainer",
        "description": "Ongoing review cadence for serious operators who need recurring technical decision support.",
        "deliverables": ["Recurring review calls", "Data review", "Written monthly notes", "Follow-up action tracking"],
        "required_data": ["Active farm or hatchery records", "Responsible technical contact", "Monthly operating goals"],
        "price_min_idr": 7_500_000,
        "price_max_idr": 100_000_000,
        "sort_order": 60,
    },
]

CONTENT_ITEMS = [
    {
        "title": "Farm Failure Post-Mortem Framework",
        "slug": "farm-failure-post-mortem-framework",
        "summary": "A practical structure for reconstructing crop failure timelines and ranking likely causes.",
        "category": "Farm",
        "tags": ["diagnostic", "mortality", "management"],
        "language": "en",
        "content_type": "template",
        "access_level": "free",
        "body_markdown": (
            "Use stocking, mortality, water quality, feed, disease test, treatment, and harvest data to reconstruct what changed before crop performance declined.\n\n"
            "Recommended sections: background, timeline, data received, likely causes, economic impact, corrective plan, and next-cycle monitoring."
        ),
        "version": "1.0",
        "sort_order": 10,
    },
    {
        "title": "Shrimp Farm Crop Planning Template",
        "slug": "shrimp-farm-crop-planning-template",
        "summary": "Planning structure for density, survival, FCR, cost, harvest size, and market-price assumptions.",
        "category": "Farm",
        "tags": ["planning", "economics", "stocking"],
        "language": "en",
        "content_type": "template",
        "access_level": "free",
        "body_markdown": "Plan crop assumptions before stocking: pond size, target density, PL source, expected survival, FCR, feed price, aeration, labor, and harvest price.",
        "version": "1.0",
        "sort_order": 20,
    },
    {
        "title": "Broodstock Receiving, Acclimation, and Quarantine SOP",
        "slug": "broodstock-receiving-acclimation-quarantine-sop",
        "summary": "Operational SOP for reducing stress and disease risk when receiving broodstock.",
        "category": "Hatchery",
        "tags": ["broodstock", "quarantine", "biosecurity"],
        "language": "en",
        "content_type": "sop",
        "access_level": "paid",
        "body_markdown": "",
        "version": "1.0",
        "sort_order": 30,
    },
    {
        "title": "Harvest Timing and Price-Size Economics",
        "slug": "harvest-timing-price-size-economics",
        "summary": "Decision framework for balancing DOC, size, survival, FCR, price, and cash-flow risk.",
        "category": "Economics",
        "tags": ["harvest", "margin", "pricing"],
        "language": "en",
        "content_type": "guide",
        "access_level": "paid",
        "body_markdown": "",
        "version": "1.0",
        "sort_order": 40,
    },
]


class Command(BaseCommand):
    help = "Seed V1 commercial layer service packages and starter content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--archive-missing",
            action="store_true",
            help="Archive existing seeded records whose slugs are not in this command's catalog.",
        )

    def handle(self, *args, **options):
        package_slugs = set()
        content_slugs = set()
        packages_created = 0
        packages_updated = 0
        content_created = 0
        content_updated = 0

        for index, payload in enumerate(SERVICE_PACKAGES, start=1):
            payload = {**payload, "is_active": True, "sort_order": payload.get("sort_order", index)}
            package_slugs.add(payload["slug"])
            package = ServicePackage.objects(slug=payload["slug"]).first()
            if package:
                for key, value in payload.items():
                    setattr(package, key, value)
                package.updated_at = datetime.now()
                package.save()
                packages_updated += 1
            else:
                ServicePackage(**payload).save()
                packages_created += 1

        for index, payload in enumerate(CONTENT_ITEMS, start=1):
            payload = {
                **payload,
                "status": "published",
                "published_at": datetime.now(),
            }
            payload.pop("sort_order", None)
            content_slugs.add(payload["slug"])
            item = ContentItem.objects(slug=payload["slug"]).first()
            if item:
                for key, value in payload.items():
                    setattr(item, key, value)
                item.updated_at = datetime.now()
                item.save()
                content_updated += 1
            else:
                ContentItem(**payload).save()
                content_created += 1

        if options["archive_missing"]:
            ServicePackage.objects(slug__nin=list(package_slugs)).update(set__is_active=False, set__updated_at=datetime.now())
            ContentItem.objects(slug__nin=list(content_slugs)).update(set__status="archived", set__updated_at=datetime.now())

        self.stdout.write(self.style.SUCCESS(
            "Seeded commercial layer: "
            f"packages created={packages_created}, packages updated={packages_updated}, "
            f"content created={content_created}, content updated={content_updated}"
        ))
