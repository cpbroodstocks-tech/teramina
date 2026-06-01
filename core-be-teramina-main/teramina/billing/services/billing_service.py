from datetime import datetime

from mongoengine.errors import NotUniqueError, ValidationError

from teramina.content.models.content_model import ContentAccess, ContentItem
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..models.billing_model import CommercialInvoice


def _is_admin(user) -> bool:
    return getattr(user, "role_user", "") == "admin"


def _invoice_number():
    return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


class BillingService:
    @staticmethod
    def create_invoice(user, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        payload = data.dict()
        try:
            invoice = CommercialInvoice(invoice_number=_invoice_number(), **payload)
            invoice.save()
        except (NotUniqueError, ValidationError) as exc:
            return 400, DataErrorSchema(code=400, message=str(exc))

        return 200, DataSuccessSchema(
            code=200,
            message="Invoice created",
            payload={"invoice": invoice.to_dict()},
        )

    @staticmethod
    def admin_list_invoices(user, status="", user_id=""):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        query = {}
        if status:
            query["status"] = status
        if user_id:
            query["user_id"] = user_id

        invoices = [
            invoice.to_dict()
            for invoice in CommercialInvoice.objects(**query).order_by("-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"invoices": invoices})

    @staticmethod
    def list_my_invoices(user_id):
        invoices = [
            invoice.to_dict()
            for invoice in CommercialInvoice.objects(user_id=user_id).order_by("-created_at")
        ]
        return 200, DataSuccessSchema(code=200, message="OK", payload={"invoices": invoices})

    @staticmethod
    def mark_invoice_paid(user, invoice_id, data):
        if not _is_admin(user):
            return 401, DataErrorSchema(code=401, message="Unauthorized")

        invoice = CommercialInvoice.objects(id=invoice_id).first()
        if not invoice:
            return 404, DataErrorSchema(code=404, message="Invoice not found")
        if invoice.status == "cancelled":
            return 400, DataErrorSchema(code=400, message="Cancelled invoices cannot be paid")

        invoice.status = "paid"
        invoice.paid_at = data.paid_at or datetime.now()
        invoice.payment_method = data.payment_method or invoice.payment_method
        invoice.payment_reference = data.payment_reference
        invoice.notes = data.notes or invoice.notes
        if data.access_expires_at:
            invoice.access_expires_at = data.access_expires_at
        invoice.updated_at = datetime.now()
        invoice.save()

        grants = BillingService._grant_invoice_content_access(invoice)

        return 200, DataSuccessSchema(
            code=200,
            message="Invoice marked paid",
            payload={"invoice": invoice.to_dict(), "access_grants": grants},
        )

    @staticmethod
    def _grant_invoice_content_access(invoice):
        grants = []
        for content_id in invoice.content_ids or []:
            if not ContentItem.objects(id=content_id).first():
                continue
            existing = ContentAccess.objects(
                user_id=invoice.user_id,
                content_id=content_id,
            ).order_by("-created_at").first()
            if existing and existing.is_valid():
                grants.append(existing.to_dict())
                continue
            access = ContentAccess(
                user_id=invoice.user_id,
                content_id=content_id,
                access_source="invoice_paid",
                expires_at=invoice.access_expires_at,
            )
            access.save()
            grants.append(access.to_dict())
        return grants
