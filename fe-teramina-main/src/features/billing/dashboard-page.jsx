import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMyInvoices, useSubmitInvoicePayment } from "./queries";

const formatIdr = (value) => `Rp ${Number(value || 0).toLocaleString("id-ID")}`;

const DashboardBillingPage = () => {
  const { data = [], isLoading, isError } = useMyInvoices();
  const submitPayment = useSubmitInvoicePayment();
  const [activeInvoiceId, setActiveInvoiceId] = useState("");
  const [paymentForm, setPaymentForm] = useState({ payment_reference: "", payment_proof_url: "", notes: "" });

  const handleSubmitPayment = async (event, invoiceId) => {
    event.preventDefault();
    await submitPayment.mutateAsync({ invoiceId, payload: paymentForm });
    setActiveInvoiceId("");
    setPaymentForm({ payment_reference: "", payment_proof_url: "", notes: "" });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Stack gap={2} sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Billing</Typography>
        <Typography color="text.secondary">Issued and paid Teramina invoices for library access, advisory, and subscriptions.</Typography>
      </Stack>
      {isError && <Alert severity="error">Failed to load invoices.</Alert>}
      {isLoading ? (
        <CircularProgress />
      ) : data.length ? (
        <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" } }}>
          {data.map((invoice) => (
            <Paper key={invoice.id} variant="outlined" sx={{ p: 2.5 }}>
              <Stack gap={1}>
                <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                  <Typography variant="h6" fontWeight={700}>{invoice.invoice_number}</Typography>
                  <Chip
                    label={invoice.status.replaceAll("_", " ")}
                    color={invoice.status === "paid" ? "success" : invoice.status === "payment_submitted" ? "warning" : "default"}
                  />
                </Stack>
                <Typography color="text.secondary">{invoice.description || invoice.invoice_type?.replaceAll("_", " ")}</Typography>
                <Typography fontWeight={700}>{formatIdr(invoice.amount_idr)}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Issued {invoice.issued_at ? new Date(invoice.issued_at).toLocaleDateString() : "-"}
                  {invoice.due_at ? ` | Due ${new Date(invoice.due_at).toLocaleDateString()}` : ""}
                </Typography>
                {invoice.paid_at && (
                  <Typography variant="body2" color="text.secondary">
                    Paid {new Date(invoice.paid_at).toLocaleDateString()} via {invoice.payment_method}
                  </Typography>
                )}
                {invoice.status === "payment_submitted" && (
                  <Alert severity="info">Payment submitted. Teramina is verifying the transfer.</Alert>
                )}
                {invoice.status === "issued" && activeInvoiceId !== invoice.id && (
                  <Button variant="outlined" onClick={() => setActiveInvoiceId(invoice.id)} sx={{ alignSelf: "flex-start" }}>
                    Submit bank transfer
                  </Button>
                )}
                {invoice.status === "issued" && activeInvoiceId === invoice.id && (
                  <Stack component="form" gap={1.25} onSubmit={(event) => handleSubmitPayment(event, invoice.id)}>
                    <Alert severity="info">Transfer the invoice amount, then send the bank reference so the team can verify it.</Alert>
                    {submitPayment.isError && <Alert severity="error">Failed to submit payment details.</Alert>}
                    <TextField
                      label="Bank transfer reference"
                      value={paymentForm.payment_reference}
                      onChange={(event) => setPaymentForm((prev) => ({ ...prev, payment_reference: event.target.value }))}
                      required
                      size="small"
                    />
                    <TextField
                      label="Proof URL (optional)"
                      value={paymentForm.payment_proof_url}
                      onChange={(event) => setPaymentForm((prev) => ({ ...prev, payment_proof_url: event.target.value }))}
                      size="small"
                    />
                    <TextField
                      label="Note (optional)"
                      value={paymentForm.notes}
                      onChange={(event) => setPaymentForm((prev) => ({ ...prev, notes: event.target.value }))}
                      size="small"
                    />
                    <Stack direction="row" gap={1}>
                      <Button type="submit" variant="contained" disabled={submitPayment.isPending}>
                        {submitPayment.isPending ? "Submitting..." : "Submit for verification"}
                      </Button>
                      <Button onClick={() => setActiveInvoiceId("")}>Cancel</Button>
                    </Stack>
                  </Stack>
                )}
              </Stack>
            </Paper>
          ))}
        </Box>
      ) : (
        <Alert severity="info">No invoices have been issued yet.</Alert>
      )}
    </Container>
  );
};

export default DashboardBillingPage;
