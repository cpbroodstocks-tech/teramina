from datetime import datetime

from mongoengine import Document, QuerySetManager, fields


class CommercialInvoice(Document):
    invoice_number = fields.StringField(required=True, unique=True)
    user_id = fields.StringField(required=True)
    invoice_type = fields.StringField(
        choices=["content_access", "advisory_case", "subscription"],
        default="content_access",
    )
    status = fields.StringField(
        choices=["draft", "issued", "paid", "cancelled"],
        default="issued",
    )
    description = fields.StringField(default="")
    amount_idr = fields.IntField(required=True, min_value=0)
    content_ids = fields.ListField(fields.StringField())
    advisory_case_id = fields.StringField(default="")
    service_package_id = fields.StringField(default="")
    subscription_months = fields.IntField(default=1, min_value=1)
    access_expires_at = fields.DateTimeField(null=True)
    due_at = fields.DateTimeField(null=True)
    issued_at = fields.DateTimeField(default=datetime.now)
    paid_at = fields.DateTimeField(null=True)
    payment_method = fields.StringField(default="manual_transfer")
    payment_reference = fields.StringField(default="")
    notes = fields.StringField(default="")
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)

    meta = {
        "indexes": ["invoice_number", "user_id", "status", "invoice_type", "-created_at"],
        "collection": "commercial_invoices",
    }
    objects = QuerySetManager()

    def to_dict(self):
        return {
            "id": str(self.id),
            "invoice_number": self.invoice_number,
            "user_id": self.user_id,
            "invoice_type": self.invoice_type,
            "status": self.status,
            "description": self.description,
            "amount_idr": self.amount_idr,
            "content_ids": list(self.content_ids or []),
            "advisory_case_id": self.advisory_case_id,
            "service_package_id": self.service_package_id,
            "subscription_months": self.subscription_months,
            "access_expires_at": self.access_expires_at.isoformat() if self.access_expires_at else None,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
