import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import { useToastStore } from "store/toast.store";
import {
  useGoogleSheetsStatus,
  useConnectSheets,
  useCreateSheetsTemplate,
  useSyncSheets,
  useDisconnectSheets,
} from "features/cycle-detail/queries";

const extractSpreadsheetId = (input) => {
  const match = input.match(/\/d\/([a-zA-Z0-9_-]+)/);
  return match ? match[1] : input.trim();
};

const statusChipColor = (s) => {
  if (s === "ok") return "success";
  if (s === "partial") return "warning";
  if (s === "error") return "error";
  return "default";
};

const statusChipLabel = (s) => {
  if (s === "ok") return "Synced";
  if (s === "partial") return "Partial";
  if (s === "error") return "Error";
  if (s === "syncing") return "Syncing…";
  return s || "Pending";
};

const MAX_POLL_ATTEMPTS = 20;

const GoogleSheets = () => {
  const { cycle_id } = useParams();
  const { setToast } = useToastStore();
  const [spreadsheetInput, setSpreadsheetInput] = useState("");
  const prevStatusRef = useRef(null);
  const syncTriggeredRef = useRef(false);
  const pollCountRef = useRef(0);
  const pollTimerRef = useRef(null);

  const { data: status, isLoading, dataUpdatedAt, refetch: refetchStatus } = useGoogleSheetsStatus(cycle_id);
  const { mutate: connect, isPending: connecting } = useConnectSheets(cycle_id);
  const { mutate: createTemplate, isPending: creatingTemplate } = useCreateSheetsTemplate(cycle_id);
  const { mutate: sync, isPending: syncing } = useSyncSheets(cycle_id);
  const { mutate: disconnect, isPending: disconnecting } = useDisconnectSheets(cycle_id);

  const clearPollTimer = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const pollStatus = async () => {
    const result = await refetchStatus();
    if (!syncTriggeredRef.current) return;

    if (result.data?.last_status === "syncing") {
      pollCountRef.current += 1;
      if (pollCountRef.current >= MAX_POLL_ATTEMPTS) {
        setToast({ open: true, variant: "warning", text: "Sync is taking longer than expected" });
        syncTriggeredRef.current = false;
        pollCountRef.current = 0;
        clearPollTimer();
        return;
      }

      pollTimerRef.current = setTimeout(pollStatus, 3000);
    }
  };

  useEffect(() => {
    const prev = prevStatusRef.current;
    const current = status?.last_status;

    if (syncTriggeredRef.current) {
      if (current !== "syncing" && prev !== null) {
        if (current === "ok") {
          setToast({ open: true, variant: "success", text: "Sync complete" });
        } else if (current === "partial") {
          setToast({ open: true, variant: "warning", text: "Sync finished with some errors" });
        } else if (current === "error") {
          setToast({ open: true, variant: "error", text: `Sync failed: ${status?.last_error || ""}` });
        }
        syncTriggeredRef.current = false;
        pollCountRef.current = 0;
        clearPollTimer();
      }
    }

    prevStatusRef.current = current;
  }, [dataUpdatedAt]);

  useEffect(() => () => clearPollTimer(), []);

  const handleConnect = () => {
    const spreadsheet_id = extractSpreadsheetId(spreadsheetInput);
    if (!spreadsheet_id) return;
    connect(spreadsheet_id, {
      onSuccess: () => setToast({ open: true, variant: "success", text: "Google Sheets connected" }),
      onError: () => setToast({ open: true, variant: "error", text: "Failed to connect — check sheet is shared with the service account" }),
    });
  };

  const handleCreateTemplate = () => {
    createTemplate(undefined, {
      onSuccess: (payload) => {
        if (payload?.spreadsheet_url) window.open(payload.spreadsheet_url, "_blank");
        setToast({ open: true, variant: "success", text: "Template created and connected" });
      },
      onError: () => setToast({ open: true, variant: "error", text: "Failed to create template" }),
    });
  };

  const handleSync = () => {
    sync(undefined, {
      onSuccess: () => {
        syncTriggeredRef.current = true;
        pollCountRef.current = 0;
        setToast({ open: true, variant: "info", text: "Sync queued — checking status…" });
        clearPollTimer();
        pollTimerRef.current = setTimeout(pollStatus, 3000);
      },
      onError: () => setToast({ open: true, variant: "error", text: "Failed to queue sync" }),
    });
  };

  const handleDisconnect = () => {
    disconnect(undefined, {
      onSuccess: () => setToast({ open: true, variant: "success", text: "Disconnected" }),
      onError: () => setToast({ open: true, variant: "error", text: "Failed to disconnect" }),
    });
  };

  if (isLoading) {
    return (
      <Box style={{ display: "flex", justifyContent: "center", padding: 32 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!status?.is_active) {
    return (
      <Box style={{ padding: "16px 0" }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Connect Google Sheets</Typography>
            <Typography variant="body2" color="textSecondary" style={{ marginBottom: 16 }}>
              Create a new template sheet (recommended) or connect an existing one.
            </Typography>

            <Box style={{ display: "flex", gap: 8, marginBottom: 24 }}>
              <Button variant="contained" onClick={handleCreateTemplate} disabled={creatingTemplate}>
                {creatingTemplate ? <CircularProgress size={18} style={{ marginRight: 6 }} /> : null}
                Create Template
              </Button>
            </Box>

            <Typography variant="subtitle2" gutterBottom>Or connect an existing sheet</Typography>
            <TextField
              fullWidth
              size="small"
              label="Spreadsheet ID or URL"
              value={spreadsheetInput}
              onChange={(e) => setSpreadsheetInput(e.target.value)}
              style={{ marginBottom: 8 }}
            />
            <Typography variant="caption" color="textSecondary" display="block" style={{ marginBottom: 12 }}>
              Share your sheet with the service account first (see SETUP tab after creating a template).
            </Typography>
            <Button variant="outlined" onClick={handleConnect} disabled={connecting || !spreadsheetInput.trim()}>
              {connecting ? <CircularProgress size={18} /> : "Connect"}
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  const isSyncing = status?.last_status === "syncing" || syncing;

  return (
    <Box style={{ padding: "16px 0" }}>
      <Card>
        <CardContent>
          <Box style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
            <Typography variant="h6">Google Sheets</Typography>
            <Chip label="Connected" color="success" size="small" />
            {status.last_status && (
              <Chip label={statusChipLabel(status.last_status)} size="small" color={statusChipColor(status.last_status)} />
            )}
            {isSyncing && <CircularProgress size={16} />}
          </Box>

          {status.spreadsheet_url && (
            <Typography variant="body2" style={{ marginBottom: 4 }}>
              <a href={status.spreadsheet_url} target="_blank" rel="noreferrer">Open Spreadsheet ↗</a>
            </Typography>
          )}

          {status.last_synced && (
            <Typography variant="body2" color="textSecondary" style={{ marginBottom: 2 }}>
              Last synced: {new Date(status.last_synced).toLocaleString("id-ID")}
            </Typography>
          )}

          {status.rows_synced != null && (
            <Typography variant="body2" color="textSecondary" style={{ marginBottom: 2 }}>
              Total rows synced: {status.rows_synced}
            </Typography>
          )}

          {status.last_status === "error" && status.last_error && (
            <Typography variant="caption" color="error" display="block" style={{ marginBottom: 8 }}>
              {status.last_error}
            </Typography>
          )}

          <Box style={{ display: "flex", gap: 8, marginTop: 16 }}>
            <Button variant="contained" onClick={handleSync} disabled={isSyncing}>
              {isSyncing ? (
                <>
                  <CircularProgress size={14} style={{ marginRight: 6, color: "#fff" }} />
                  Syncing…
                </>
              ) : "Sync Now"}
            </Button>
            <Button variant="outlined" color="error" onClick={handleDisconnect} disabled={disconnecting || isSyncing}>
              {disconnecting ? <CircularProgress size={18} /> : "Disconnect"}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default GoogleSheets;
