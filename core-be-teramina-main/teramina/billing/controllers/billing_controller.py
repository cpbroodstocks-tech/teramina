from ninja import Body, Router

from teramina.authentication.auth_bearer import AuthBearer
from teramina.authentication.services.authentication_service import get_signed_in_user
from teramina.schemas.general_schema import DataErrorSchema, DataSuccessSchema

from ..schemas.billing_schema import (
    CommercialInvoiceCreateSchema,
    CommercialInvoicePaidSchema,
)
from ..services.billing_service import BillingService

router = Router(tags=["Billing"])

response_schema = {200: DataSuccessSchema, 400: DataErrorSchema, 401: DataErrorSchema, 404: DataErrorSchema}


@router.get("/my-invoices", response=response_schema, auth=AuthBearer())
def list_my_invoices(request):
    user = get_signed_in_user(request)
    return BillingService.list_my_invoices(str(user.id))


@router.get("/admin/invoices", response=response_schema, auth=AuthBearer())
def admin_list_invoices(request, status: str = "", user_id: str = ""):
    user = get_signed_in_user(request)
    return BillingService.admin_list_invoices(user, status=status, user_id=user_id)


@router.post("/invoices", response=response_schema, auth=AuthBearer())
def create_invoice(request, data: CommercialInvoiceCreateSchema = Body(...)):
    user = get_signed_in_user(request)
    return BillingService.create_invoice(user, data)


@router.post("/invoices/{invoice_id}/mark-paid", response=response_schema, auth=AuthBearer())
def mark_invoice_paid(request, invoice_id: str, data: CommercialInvoicePaidSchema = Body(...)):
    user = get_signed_in_user(request)
    return BillingService.mark_invoice_paid(user, invoice_id, data)
