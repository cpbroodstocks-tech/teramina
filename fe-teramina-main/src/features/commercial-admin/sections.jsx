import { Alert, Box, Button, Chip, Paper, Stack, Typography } from "@mui/material";

export const AdminSection = ({ id, title, description, children }) => (
  <Paper id={id} variant="outlined" sx={{ p: 3, scrollMarginTop: 16 }}>
    <Stack gap={2}>
      <Box>
        <Typography variant="h5" fontWeight={700}>{title}</Typography>
        <Typography color="text.secondary">{description}</Typography>
      </Box>
      {children}
    </Stack>
  </Paper>
);

export const AdminNavigation = () => (
  <Paper variant="outlined" sx={{ p: 1, position: "sticky", top: 8, zIndex: 2 }}>
    <Stack direction="row" gap={0.5} sx={{ flexWrap: "wrap" }}>
      <Button href="#access-requests" size="small">Access</Button>
      <Button href="#content-operations" size="small">Content</Button>
      <Button href="#billing-operations" size="small">Billing</Button>
      <Button href="#advisory-operations" size="small">Advisory</Button>
      <Button href="#audit-trail" size="small">Audit</Button>
    </Stack>
  </Paper>
);

export const AccessRequestsSection = ({ accessRequests, updateAccessRequest }) => (
  <AdminSection id="access-requests" title="Closed Beta Access" description="Approve or reject requests before users can create an account.">
    {updateAccessRequest.isError && <Alert severity="error">Failed to update access request.</Alert>}
    {accessRequests.length ? (
      <Stack gap={1}>
        {accessRequests.slice(0, 20).map((item) => (
          <Paper key={item.id} variant="outlined" sx={{ p: 1.5 }}>
            <Stack direction={{ xs: "column", sm: "row" }} gap={1} sx={{ alignItems: { sm: "center" } }}>
              <Box flex={1}>
                <Typography fontWeight={700}>{item.name || item.email}</Typography>
                <Typography variant="body2" color="text.secondary">{item.email} · {item.source}</Typography>
              </Box>
              <Chip size="small" label={item.status} color={item.status === "approved" ? "success" : "default"} />
              {item.status === "pending" && (
                <>
                  <Button size="small" variant="contained" onClick={() => updateAccessRequest.mutate({ requestId: item.id, status: "approved" })}>
                    Approve
                  </Button>
                  <Button size="small" color="error" onClick={() => updateAccessRequest.mutate({ requestId: item.id, status: "rejected" })}>
                    Reject
                  </Button>
                </>
              )}
            </Stack>
          </Paper>
        ))}
      </Stack>
    ) : (
      <Alert severity="info">No beta access requests yet.</Alert>
    )}
  </AdminSection>
);
