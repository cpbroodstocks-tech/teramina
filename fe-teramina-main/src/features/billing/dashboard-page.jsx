import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Container,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useMyInvoices } from "./queries";

const formatIdr = (value) => `Rp ${Number(value || 0).toLocaleString("id-ID")}`;

const DashboardBillingPage = () => {
  const { data = [], isLoading, isError } = useMyInvoices();

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
                  <Chip label={invoice.status} color={invoice.status === "paid" ? "success" : "default"} />
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
