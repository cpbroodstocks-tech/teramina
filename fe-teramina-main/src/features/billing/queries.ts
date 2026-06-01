import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const billingKeys = {
  myInvoices: ["billing-my-invoices"] as const,
  adminInvoices: ["billing-admin-invoices"] as const,
};

export const useMyInvoices = () =>
  useQuery({
    queryKey: billingKeys.myInvoices,
    queryFn: () => axios.get("/billing/my-invoices").then((r: any) => r?.payload?.invoices ?? []),
  });

export const useAdminInvoices = (enabled = true) =>
  useQuery({
    queryKey: billingKeys.adminInvoices,
    queryFn: () => axios.get("/billing/admin/invoices").then((r: any) => r?.payload?.invoices ?? []),
    enabled,
  });

export const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      user_id: string;
      invoice_type?: string;
      description?: string;
      amount_idr: number;
      content_ids?: string[];
      advisory_case_id?: string;
      service_package_id?: string;
      subscription_months?: number;
      access_expires_at?: string | null;
      due_at?: string | null;
      status?: string;
      payment_method?: string;
      notes?: string;
    }) => axios.post("/billing/invoices", payload).then((r: any) => r?.payload?.invoice ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.adminInvoices });
      queryClient.invalidateQueries({ queryKey: billingKeys.myInvoices });
    },
  });
};

export const useMarkInvoicePaid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      invoiceId,
      payload,
    }: {
      invoiceId: string;
      payload: {
        paid_at?: string | null;
        payment_method?: string;
        payment_reference?: string;
        notes?: string;
        access_expires_at?: string | null;
      };
    }) => axios.post(`/billing/invoices/${invoiceId}/mark-paid`, payload).then((r: any) => r?.payload ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: billingKeys.adminInvoices });
      queryClient.invalidateQueries({ queryKey: billingKeys.myInvoices });
    },
  });
};
