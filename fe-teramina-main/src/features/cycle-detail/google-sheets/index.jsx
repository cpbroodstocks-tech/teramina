import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { useToastStore } from "store/toast.store";
import {
  useGoogleSheetsStatus,
  useConnectSheets,
  useCreateSheetsTemplate,
  useSyncSheets,
  useDisconnectSheets,
  useSyncLog,
  usePreviewSync,
  useConfirmSync,
} from "features/cycle-detail/queries";

const extractSpreadsheetId = (input) => {
  const match = input.match(/\/d\/([a-zA-Z0-9_-]+)/);
  return match ? match[1] : input.trim();
};

const statusColor = (s) => {
  if (s === "ok") return "success";
  if (s === "partial") return "warning";
  if (s === "error") return "error";
  return "default";
};

const statusLabel = (s) => {
  if (s === "ok") return "Synced";
  if (s === "partial") return "Partial";
  if (s === "error") return "Error";
  if (s === "queued") return "Queued";
  if (s === "syncing") return "Syncing…";
  return s || "Pending";
};

const reasonColor = (reason) => {
  if (!reason) return "inherit";
  if (reason.startsWith("hard_failure")) return "#d32f2f";
  if (reason.startsWith("warn:")) return "#ed6c02";
  return "#616161";
};

const MAX_POLL_ATTEMPTS = 20;

// ─── Issues Table ─────────────────────────────────────────────────────────────

const IssuesTable = ({ rejectedRows, spreadsheetUrl, maxRows = 50 }) => {
  if (!rejectedRows?.length) return null;

  const visible = rejectedRows.slice(0, maxRows);
  const grouped = visible.reduce((acc, row) => {
    if (!acc[row.tab]) acc[row.tab] = [];
    acc[row.tab].push(row);
    return acc;
  }, {});

  return (
    <Box sx={{ overflowX: "auto", mt: 1 }}>
      <Table size="small">
        <TableHead>
          <TableRow sx={{ "& th": { fontWeight: 700, fontSize: 12 } }}>
            <TableCell>Tab</TableCell>
            <TableCell>Row</TableCell>
            <TableCell>Field</TableCell>
            <TableCell>Value</TableCell>
            <TableCell>Reason</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {Object.entries(grouped).map(([tab, rows]) =>
            rows.map((row, i) => (
              <TableRow key={`${tab}-${i}`} sx={{ "& td": { fontSize: 12, py: 0.5 } }}>
                {i === 0 && (
                  <TableCell rowSpan={rows.length} sx={{ fontWeight: 600, verticalAlign: "top", pt: 1 }}>
                    {tab}
                  </TableCell>
                )}
                <TableCell>{row.row_number ?? "—"}</TableCell>
                <TableCell sx={{ fontFamily: "monospace" }}>{row.field ?? "—"}</TableCell>
                <TableCell sx={{ maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {row.raw_value ?? "—"}
                </TableCell>
                <TableCell sx={{ color: reasonColor(row.reason), maxWidth: 180 }}>
                  {row.reason ?? "—"}
                </TableCell>
                <TableCell>
                  {spreadsheetUrl && (
                    <IconButton
                      size="small"
                      component="a"
                      href={spreadsheetUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <OpenInNewIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      {rejectedRows.length > maxRows && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: "block", pl: 1 }}>
          Showing first {maxRows} of {rejectedRows.length} issues.
        </Typography>
      )}
    </Box>
  );
};

// ─── Tab Summary Row ──────────────────────────────────────────────────────────

const TabSummaryRow = ({ summary }) => (
  <Box
    sx={{
      display: "flex",
      alignItems: "center",
      gap: 1.5,
      py: 0.5,
      flexWrap: "wrap",
    }}
  >
    <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 120, fontFamily: "monospace" }}>
      {summary.tab}
    </Typography>
    <Typography variant="caption" color="success.main">
      ↑{summary.inserted} in
    </Typography>
    {summary.updated > 0 && (
      <Typography variant="caption" color="info.main">
        ↻{summary.updated} up
      </Typography>
    )}
    {summary.deleted > 0 && (
      <Typography variant="caption" color="warning.main">
        -{summary.deleted} del
      </Typography>
    )}
    {summary.skipped > 0 && (
      <Typography variant="caption" color="text.secondary">
        /{summary.skipped} skip
      </Typography>
    )}
    {summary.rejected > 0 && (
      <Typography variant="caption" color="error.main" sx={{ fontWeight: 700 }}>
        ✕{summary.rejected} err
      </Typography>
    )}
    {summary.error && (
      <Typography variant="caption" color="error.main" sx={{ flexBasis: "100%", ml: { xs: 0, sm: 15 } }}>
        {summary.error}
      </Typography>
    )}
  </Box>
);

// ─── Preview Modal ────────────────────────────────────────────────────────────

const PreviewModal = ({ open, onClose, previewResult, spreadsheetUrl, onConfirm, confirming }) => {
  if (!open) return null;

  const hasIssues = previewResult?.rejected_rows?.length > 0;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Review Import
        {previewResult && (
          <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
            <span style={{ color: "#2e7d32", fontWeight: 700 }}>{previewResult.rows_valid} valid</span>
            {" · "}
            <span style={{ color: previewResult.rows_warning > 0 ? "#ed6c02" : "inherit" }}>
              {previewResult.rows_warning} warnings
            </span>
            {" · "}
            <span style={{ color: previewResult.rows_error > 0 ? "#d32f2f" : "inherit" }}>
              {previewResult.rows_error} errors
            </span>
          </Typography>
        )}
      </DialogTitle>
      <DialogContent>
        {!previewResult ? (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", py: 4, gap: 2 }}>
            <CircularProgress size={24} />
            <Typography>Analyzing sheet…</Typography>
          </Box>
        ) : (
          <>
            {previewResult.tab_summaries?.map((ts) => (
              <TabSummaryRow key={ts.tab} summary={ts} />
            ))}

            {hasIssues && (
              <>
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="subtitle2" gutterBottom>
                  Issues ({previewResult.rejected_rows.length})
                </Typography>
                <IssuesTable
                  rejectedRows={previewResult.rejected_rows}
                  spreadsheetUrl={spreadsheetUrl}
                  maxRows={30}
                />
              </>
            )}

            <Box sx={{ display: "flex", gap: 1.5, mt: 3, justifyContent: "flex-end" }}>
              <Button variant="outlined" onClick={onClose} disabled={confirming}>
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={onConfirm}
                disabled={confirming || previewResult.rows_valid === 0}
              >
                {confirming ? (
                  <>
                    <CircularProgress size={14} sx={{ mr: 0.75, color: "#fff" }} />
                    Importing…
                  </>
                ) : `Import ${previewResult.rows_valid} Valid Rows`}
              </Button>
            </Box>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

const GoogleSheets = () => {
  const { cycle_id } = useParams();
  const { setToast } = useToastStore();
  const [spreadsheetInput, setSpreadsheetInput] = useState("");
  const [showIssues, setShowIssues] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewResult, setPreviewResult] = useState(null);
  const [importMode, setImportMode] = useState("valid_rows_only");

  const prevStatusRef = useRef(null);
  const syncTriggeredRef = useRef(false);
  const pollCountRef = useRef(0);
  const pollTimerRef = useRef(null);

  const { data: status, isLoading, isError, dataUpdatedAt, refetch: refetchStatus } = useGoogleSheetsStatus(cycle_id);
  const { data: syncLog, refetch: refetchSyncLog } = useSyncLog(cycle_id);
  const { mutate: connect, isPending: connecting } = useConnectSheets(cycle_id);
  const { mutate: createTemplate, isPending: creatingTemplate } = useCreateSheetsTemplate(cycle_id);
  const { mutate: sync, isPending: syncing } = useSyncSheets(cycle_id);
  const { mutate: disconnect, isPending: disconnecting } = useDisconnectSheets(cycle_id);
  const { mutate: preview, isPending: previewing } = usePreviewSync(cycle_id);
  const { mutate: confirmSync, isPending: confirming } = useConfirmSync(cycle_id);

  const clearPollTimer = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const pollStatus = async () => {
    const result = await refetchStatus();
    if (!syncTriggeredRef.current) return;

    if (["queued", "syncing"].includes(result.data?.last_status)) {
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
      if (!["queued", "syncing"].includes(current) && prev !== null) {
        if (current === "ok") {
          setToast({ open: true, variant: "success", text: "Sync complete" });
        } else if (current === "partial") {
          setToast({ open: true, variant: "warning", text: "Sync finished with some errors — check issues below" });
        } else if (current === "error") {
          setToast({ open: true, variant: "error", text: `Sync failed: ${status?.last_error || ""}` });
        }
        syncTriggeredRef.current = false;
        pollCountRef.current = 0;
        clearPollTimer();
        refetchSyncLog();
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

  const handleReviewAndSync = () => {
    setPreviewResult(null);
    setPreviewOpen(true);
    preview(importMode, {
      onSuccess: (result) => setPreviewResult(result),
      onError: () => {
        setPreviewOpen(false);
        setToast({ open: true, variant: "error", text: "Failed to analyze sheet" });
      },
    });
  };

  const handleConfirmSync = () => {
    if (!previewResult?.preview_id) return;
    confirmSync(previewResult.preview_id, {
      onSuccess: () => {
        setPreviewOpen(false);
        setPreviewResult(null);
        syncTriggeredRef.current = true;
        pollCountRef.current = 0;
        setToast({ open: true, variant: "info", text: "Import queued — checking status…" });
        clearPollTimer();
        pollTimerRef.current = setTimeout(pollStatus, 3000);
      },
      onError: () => setToast({ open: true, variant: "error", text: "Failed to start import" }),
    });
  };

  // Legacy direct sync (kept for backward compat, used if preview is unavailable)
  const handleLegacySync = () => {
    sync(importMode, {
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
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box sx={{ py: 2 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Google Sheets unavailable</Typography>
            <Typography variant="body2" color="error" sx={{ mb: 2 }}>
              Could not load Google Sheets status. Please try again.
            </Typography>
            <Button variant="outlined" onClick={() => refetchStatus()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // ── Disconnected State ────────────────────────────────────────────────────
  if (!status?.is_active) {
    return (
      <Box sx={{ py: 2 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Connect Google Sheets</Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Create a new template sheet (recommended) or connect an existing one.
            </Typography>

            <Box sx={{ display: "flex", gap: 1, mb: 3 }}>
              <Button variant="contained" onClick={handleCreateTemplate} disabled={creatingTemplate}>
                {creatingTemplate && <CircularProgress size={18} sx={{ mr: 0.75 }} />}
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
              sx={{ mb: 1 }}
            />
            <Typography variant="caption" color="textSecondary" display="block" sx={{ mb: 1.5 }}>
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

  // ── Connected State ───────────────────────────────────────────────────────
  const isSyncing = ["queued", "syncing"].includes(status?.last_status) || syncing || previewing || confirming;
  const syncLogLoadError = syncLog?.error ? syncLog.message : null;
  const tabSummaries = syncLog?.tab_summaries ?? status?.tab_summaries ?? [];
  const rejectedRows = syncLog?.rejected_rows ?? [];
  const hasIssues = rejectedRows.length > 0;
  const totalValid = tabSummaries.reduce((s, t) => s + (t.inserted || 0) + (t.updated || 0), 0);
  const totalRejected = tabSummaries.reduce((s, t) => s + (t.rejected || 0), 0);
  const totalWarnings = rejectedRows.filter((r) => r.reason?.startsWith("warn:")).length;

  return (
    <Box sx={{ py: 2 }}>
      <Card>
        <CardContent>
          {/* Header */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1.5, flexWrap: "wrap" }}>
            <Typography variant="h6">Google Sheets</Typography>
            <Chip label="Connected" color="success" size="small" />
            {status.last_status && (
              <Chip
                label={statusLabel(status.last_status)}
                size="small"
                color={statusColor(status.last_status)}
              />
            )}
            {isSyncing && <CircularProgress size={16} />}
            {status.spreadsheet_url && (
              <Box component="a" href={status.spreadsheet_url} target="_blank" rel="noreferrer"
                sx={{ display: "flex", alignItems: "center", gap: 0.5, color: "primary.main", fontSize: 13, ml: "auto" }}>
                Open Spreadsheet ↗
              </Box>
            )}
          </Box>

          {/* Sync timestamp */}
          {status.last_synced && (
            <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
              Last sync: {new Date(status.last_synced).toLocaleString("id-ID")}
            </Typography>
          )}
          {(status.active_sync_id || status.last_sync_id) && (
            <Typography variant="caption" color="textSecondary" sx={{ mb: 1, display: "block", fontFamily: "monospace" }}>
              Sync ID: {status.active_sync_id || status.last_sync_id}
            </Typography>
          )}

          {/* Summary counts */}
          {syncLogLoadError && (
            <Typography variant="caption" color="warning.main" display="block" sx={{ mb: 1 }}>
              {syncLogLoadError}
            </Typography>
          )}

          {/* Summary counts */}
          {(tabSummaries.length > 0 || totalValid > 0) && (
            <Box sx={{ display: "flex", gap: 2, mb: 1.5, flexWrap: "wrap" }}>
              <Typography variant="caption" color="success.main" sx={{ fontWeight: 700 }}>
                {totalValid} valid
              </Typography>
              {totalWarnings > 0 && (
                <Typography variant="caption" color="warning.main" sx={{ fontWeight: 700 }}>
                  {totalWarnings} warnings
                </Typography>
              )}
              {totalRejected > 0 && (
                <Typography variant="caption" color="error.main" sx={{ fontWeight: 700 }}>
                  {totalRejected} errors
                </Typography>
              )}
            </Box>
          )}

          {/* Per-tab breakdown */}
          {tabSummaries.length > 0 && (
            <Box sx={{ mb: 1.5, pl: 1, borderLeft: "3px solid", borderColor: "divider" }}>
              {tabSummaries.map((ts) => (
                <TabSummaryRow key={ts.tab} summary={ts} />
              ))}
            </Box>
          )}

          {/* Error string (if any) */}
          {status.last_status === "error" && status.last_error && (
            <Typography variant="caption" color="error" display="block" sx={{ mb: 1 }}>
              {status.last_error}
            </Typography>
          )}
          {status.last_status === "error" && status.last_error?.includes("Sheet changed since preview") && (
            <Button size="small" variant="outlined" onClick={handleReviewAndSync} disabled={isSyncing} sx={{ mb: 1 }}>
              Review Again
            </Button>
          )}

          {/* View Issues toggle */}
          {hasIssues && (
            <>
              <Button
                size="small"
                variant="text"
                color="warning"
                endIcon={showIssues ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                onClick={() => setShowIssues((v) => !v)}
                sx={{ mb: 0.5, pl: 0 }}
              >
                View Issues ({rejectedRows.length})
              </Button>
              <Collapse in={showIssues}>
                <IssuesTable
                  rejectedRows={rejectedRows}
                  spreadsheetUrl={status.spreadsheet_url}
                />
              </Collapse>
            </>
          )}

          <Divider sx={{ my: 2 }} />

          {/* Actions */}
          <FormControl size="small" sx={{ minWidth: 190, mb: 1.5 }}>
            <InputLabel id="sheets-import-mode-label">Import mode</InputLabel>
            <Select
              labelId="sheets-import-mode-label"
              label="Import mode"
              value={importMode}
              onChange={(event) => setImportMode(event.target.value)}
              disabled={isSyncing}
            >
              <MenuItem value="valid_rows_only">Import valid rows</MenuItem>
              <MenuItem value="strict">Strict import</MenuItem>
            </Select>
          </FormControl>
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
            <Button variant="contained" onClick={handleReviewAndSync} disabled={isSyncing}>
              {previewing ? (
                <>
                  <CircularProgress size={14} sx={{ mr: 0.75, color: "#fff" }} />
                  Analyzing…
                </>
              ) : "Review & Sync"}
            </Button>
            <Button
              variant="outlined"
              onClick={handleLegacySync}
              disabled={isSyncing}
              size="small"
            >
              {isSyncing ? "Syncing…" : "Sync Now"}
            </Button>
            <Button
              variant="outlined"
              color="error"
              onClick={handleDisconnect}
              disabled={disconnecting || isSyncing}
            >
              {disconnecting ? <CircularProgress size={18} /> : "Disconnect"}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Review & Sync Modal */}
      <PreviewModal
        open={previewOpen}
        onClose={() => { setPreviewOpen(false); setPreviewResult(null); }}
        previewResult={previewResult}
        spreadsheetUrl={status?.spreadsheet_url}
        onConfirm={handleConfirmSync}
        confirming={confirming}
      />
    </Box>
  );
};

export default GoogleSheets;
