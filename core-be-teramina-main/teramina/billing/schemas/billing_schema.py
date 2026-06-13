from datetime import datetime
from typing import Optional

from ninja import Schema


class CommercialInvoiceCreateSchema(Schema):
    user_id: str
    invoice_type: str = "content_access"
    description: str = ""
    amount_idr: int
    content_ids: list[str] = []
    advisory_case_id: str = ""
    service_package_id: str = ""
    subscription_months: int = 1
    access_expires_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    status: str = "issued"
    payment_method: str = "manual_transfer"
    notes: str = ""


class CommercialInvoicePaidSchema(Schema):
    paid_at: Optional[datetime] = None
    payment_method: str = "manual_transfer"
    payment_reference: str = ""
    notes: str = ""
    access_expires_at: Optional[datetime] = None


class CommercialInvoicePaymentSubmissionSchema(Schema):
    payment_reference: str
    payment_proof_url: str = ""
    notes: str = ""
