import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  MdCheckCircleOutline,
  MdDeleteOutline,
  MdDone,
  MdRefresh,
  MdSmartToy,
  MdTimeline,
  MdWarningAmber,
} from "react-icons/md";
import {
  useGetTodaySummary,
  useDismissAlert,
  useResolveAlert,
  useCompleteAgentTask,
  useCreateControlLoop,
  useInvalidateAgentAlerts,
  useInvalidateAgentTasks,
  useRecordControlLoopOutcome,
} from "components/agent-chat/queries";
import { useDashboardContextStore } from "store/dashboard-context.store";
import { useToastStore } from "store/toast.store";

const STATUS_COLORS = {
  ok: { bg: "#e8f5e9", border: "#66bb6a", label: "#2e7d32" },
  warning: { bg: "#fff8e1", border: "#ffa726", label: "#e65100" },
  critical: { bg: "#ffebee", border: "#ef5350", label: "#b71c1c" },
  unknown: { bg: "#f5f5f5", border: "#bdbdbd", label: "#616161" },
};

const panelSx = {
  borderColor: "#e2e8f0",
  borderRadius: 1,
};

const worstStatus = (...statuses) => {
  if (statuses.includes("critical")) return "critical";
  if (statuses.includes("warning")) return "warning";
  if (statuses.includes("ok")) return "ok";
  return "unknown";
};

const SectionTitle = ({ children, count }) => (
  <Stack direction="row" gap={1} sx={{ alignItems: "center", mb: 1.5 }}>
    <Typography variant="h6" fontWeight={700}>
      {children}
    </Typography>
    {count != null && <Chip size="small" variant="outlined" label={count} />}
  </Stack>
);

const PondCard = ({ pond }) => {
  const navigate = useNavigate();
  const setContext = useDashboardContextStore((state) => state.setContext);
  const status = worstStatus(pond.do_status, pond.nh3_status);
  const colors = STATUS_COLORS[status];

  return (
    <Card
      variant="outlined"
      sx={{
        background: colors.bg,
        borderColor: colors.border,
        borderWidth: 1,
        borderRadius: 1,
        height: "100%",
        minHeight: 260,
        transition: "box-shadow 160ms ease, transform 160ms ease",
        "&:hover": {
          boxShadow: "0 4px 14px rgba(31, 41, 55, 0.1)",
          transform: "translateY(-1px)",
        },
      }}
    >
      <CardContent sx={{ display: "flex", flexDirection: "column", height: "100%", p: 2.25, pb: "18px !important" }}>
        <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", alignItems: "flex-start" }}>
          <Box>
            <Typography variant="h6" fontWeight={700} color={colors.label} sx={{ lineHeight: 1.3 }}>
              {pond.pond_name}
            </Typography>
            {pond.current_doc != null && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
                DOC {pond.current_doc}
              </Typography>
            )}
          </Box>
          <Chip
            size="small"
            variant="outlined"
            icon={status !== "ok" ? <MdWarningAmber /> : undefined}
            label={status === "ok" ? "Healthy" : status === "warning" ? "At risk" : status}
            sx={{ color: colors.label, borderColor: colors.border, backgroundColor: "#ffffffb8", fontWeight: 700 }}
          />
        </Stack>

        <Stack gap={0} divider={<Divider />} sx={{ mt: 2 }}>
          {pond.do_avg != null && (
            <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", py: 0.85 }}>
              <Typography variant="body2" color="text.secondary">Dissolved oxygen</Typography>
              <Chip
                label={`${pond.do_avg} mg/L`}
                size="small"
                color={pond.do_status === "critical" ? "error" : pond.do_status === "warning" ? "warning" : "success"}
                sx={{ fontWeight: 700 }}
              />
            </Stack>
          )}
          {pond.temp_avg != null && (
            <Stack direction="row" sx={{ justifyContent: "space-between", py: 0.85 }}>
              <Typography variant="body2" color="text.secondary">Temperature</Typography>
              <Typography variant="body2" fontWeight={700}>{pond.temp_avg}°C</Typography>
            </Stack>
          )}
          {pond.nh3 != null && (
            <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", py: 0.85 }}>
              <Typography variant="body2" color="text.secondary">NH3</Typography>
              <Chip
                label={`${pond.nh3} mg/L`}
                size="small"
                color={pond.nh3_status === "critical" ? "error" : pond.nh3_status === "warning" ? "warning" : "success"}
                sx={{ fontWeight: 700 }}
              />
            </Stack>
          )}
          {pond.abw_g != null && (
            <Stack direction="row" sx={{ justifyContent: "space-between", py: 0.85 }}>
              <Typography variant="body2" color="text.secondary">Average body weight</Typography>
              <Typography variant="body2" fontWeight={700}>{pond.abw_g} g</Typography>
            </Stack>
          )}
        </Stack>

        {pond.active_cycle_id && (
          <Stack direction="row" gap={0.75} sx={{ mt: "auto", pt: 2 }}>
            <Button
              size="small"
              variant="outlined"
              startIcon={<MdSmartToy size={16} />}
              onClick={() => {
                setContext({
                  pond_id: pond.pond_id,
                  pond_name: pond.pond_name,
                  cycle_id: pond.active_cycle_id,
                });
                window.dispatchEvent(new CustomEvent("open-agent-chat", {
                  detail: { message: `What should I do about ${pond.pond_name} today? DO: ${pond.do_avg ?? "?"} mg/L, NH3: ${pond.nh3 ?? "?"} mg/L, DOC: ${pond.current_doc ?? "?"}` },
                }));
              }}
            >
              Ask
            </Button>
            <Button
              size="small"
              variant="outlined"
              startIcon={<MdTimeline size={16} />}
              onClick={() => navigate(`/dashboard/pond-timeline/${pond.active_cycle_id}`)}
            >
              Timeline
            </Button>
          </Stack>
        )}
      </CardContent>
    </Card>
  );
};

const AlertRow = ({ alert, onResolve, onDismiss }) => {
  const color = alert.severity === "critical" ? "error" : alert.severity === "warning" ? "warning" : "info";
  return (
    <Stack direction={{ xs: "column", sm: "row" }} gap={1.25} sx={{ alignItems: { sm: "center" }, py: 1.25 }}>
      <Chip label={alert.severity} size="small" color={color} sx={{ flexShrink: 0 }} />
      <Typography variant="body2" fontWeight={600} sx={{ flex: 1, lineHeight: 1.5 }}>{alert.message}</Typography>
      <Stack direction="row" gap={0.5} sx={{ alignSelf: { xs: "flex-end", sm: "center" } }}>
        <Tooltip title="Mark resolved">
          <IconButton
            size="small"
            onClick={() => onResolve(alert)}
            aria-label={`Resolve alert: ${alert.message}`}
            sx={{ color: "#2e7d32", border: "1px solid", borderColor: "divider" }}
          >
            <MdDone size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Dismiss">
          <IconButton
            size="small"
            onClick={() => onDismiss(alert.id)}
            aria-label={`Dismiss alert: ${alert.message}`}
            sx={{ border: "1px solid", borderColor: "divider" }}
          >
            <MdDeleteOutline size={18} />
          </IconButton>
        </Tooltip>
      </Stack>
    </Stack>
  );
};

const TaskRow = ({ task, onComplete }) => {
  const due = task.due_at ? new Date(task.due_at) : null;
  const overdue = task.is_overdue;
  return (
    <Stack direction="row" gap={1.5} sx={{ alignItems: "center", py: 1.25 }}>
      <Box flex={1}>
        <Typography variant="body2" fontWeight={600}>
          {task.title}
        </Typography>
        {due && (
          <Typography variant="caption" color={overdue ? "error" : "text.secondary"}>
            {overdue ? "Overdue — " : "Due "}
            {due.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
          </Typography>
        )}
      </Box>
      <Tooltip title="Mark done">
        <IconButton
          size="small"
          onClick={() => onComplete(task.id)}
          aria-label={`Complete task: ${task.title}`}
          sx={{ color: "#2e7d32", border: "1px solid", borderColor: "divider" }}
        >
          <MdCheckCircleOutline size={20} />
        </IconButton>
      </Tooltip>
    </Stack>
  );
};

const ControlLoopRow = ({ loop, onRecordOutcome }) => (
  <Stack direction={{ xs: "column", sm: "row" }} gap={1.25} sx={{ alignItems: { sm: "center" }, py: 1.25 }}>
    <Box flex={1}>
      <Typography variant="body2" fontWeight={700}>{loop.action}</Typography>
      <Typography variant="caption" color="text.secondary">
        {loop.next_check_at ? `Check ${new Date(loop.next_check_at).toLocaleString()}` : "Outcome check not scheduled"}
        {loop.success_signal ? ` · Success: ${loop.success_signal}` : ""}
      </Typography>
    </Box>
    <Button size="small" variant="outlined" onClick={() => onRecordOutcome(loop)}>
      Record outcome
    </Button>
  </Stack>
);

const tomorrowLocalInput = () => {
  const value = new Date(Date.now() + 24 * 60 * 60 * 1000);
  value.setMinutes(value.getMinutes() - value.getTimezoneOffset());
  return value.toISOString().slice(0, 16);
};

const TodayView = () => {
  const { setToast } = useToastStore();
  const farmId = useDashboardContextStore((state) => state.farm_id);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [selectedLoop, setSelectedLoop] = useState(null);
  const [actionForm, setActionForm] = useState({
    action: "",
    expected_benefit: "",
    next_check_at: tomorrowLocalInput(),
    success_signal: "",
    confidence: "medium",
  });
  const [outcomeForm, setOutcomeForm] = useState({ outcome: "", outcome_status: "worked" });

  const { data, isLoading, isError, refetch } = useGetTodaySummary(farmId || null);
  const invalidateAlerts = useInvalidateAgentAlerts();
  const invalidateTasks = useInvalidateAgentTasks();
  const { mutateAsync: resolveAlert } = useResolveAlert();
  const { mutateAsync: dismissAlert } = useDismissAlert();
  const { mutateAsync: completeTask } = useCompleteAgentTask();
  const { mutateAsync: createControlLoop, isPending: isCreatingLoop } = useCreateControlLoop();
  const { mutateAsync: recordOutcome, isPending: isRecordingOutcome } = useRecordControlLoopOutcome();

  const openResolve = (alert) => {
    setSelectedAlert(alert);
    setActionForm({
      action: "",
      expected_benefit: "",
      next_check_at: tomorrowLocalInput(),
      success_signal: "",
      confidence: "medium",
    });
  };

  const handleResolve = async () => {
    try {
      await createControlLoop({
        source_type: "alert",
        source_id: selectedAlert.id,
        action: actionForm.action,
        reason: selectedAlert.message,
        expected_benefit: actionForm.expected_benefit,
        next_check_at: actionForm.next_check_at ? new Date(actionForm.next_check_at).toISOString() : null,
        success_signal: actionForm.success_signal,
        confidence: actionForm.confidence,
      });
      await resolveAlert({ alertId: selectedAlert.id, resolutionNote: actionForm.action });
      invalidateAlerts();
      refetch();
      setSelectedAlert(null);
      setToast({ open: true, variant: "success", text: "Action and follow-up recorded" });
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to record action" });
    }
  };

  const handleDismiss = async (alertId) => {
    try {
      await dismissAlert(alertId);
      invalidateAlerts();
      refetch();
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to dismiss alert" });
    }
  };

  const handleComplete = async (taskId) => {
    try {
      await completeTask(taskId);
      invalidateTasks();
      refetch();
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to complete task" });
    }
  };

  const handleRecordOutcome = async () => {
    try {
      await recordOutcome({ loopId: selectedLoop.id, ...outcomeForm });
      setSelectedLoop(null);
      setOutcomeForm({ outcome: "", outcome_status: "worked" });
      refetch();
      setToast({ open: true, variant: "success", text: "Outcome recorded for future recommendations" });
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to record outcome" });
    }
  };

  const criticalAlerts = (data?.alerts || []).filter((a) => a.severity === "critical");
  const otherAlerts = (data?.alerts || []).filter((a) => a.severity !== "critical");

  if (!farmId) {
    return (
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Alert severity="info">Select a farm to see today&apos;s summary.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        gap={2}
        sx={{ mb: 3, justifyContent: "space-between", alignItems: { sm: "center" } }}
      >
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Today
          </Typography>
          {data?.farm_name && (
            <Typography variant="body2" color="text.secondary">
              {data.farm_name} — {new Date().toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" })}
            </Typography>
          )}
        </Box>
        <IconButton
          onClick={() => refetch()}
          title="Refresh"
          aria-label="Refresh today's summary"
          sx={{ alignSelf: { xs: "flex-start", sm: "center" }, border: "1px solid", borderColor: "divider" }}
        >
          <MdRefresh />
        </IconButton>
      </Stack>

      {isLoading && (
        <Stack direction="row" gap={1} sx={{ alignItems: "center", py: 2 }}>
          <CircularProgress size={18} />
          <Typography variant="body2">Loading today&apos;s summary…</Typography>
        </Stack>
      )}

      {isError && <Alert severity="error">Failed to load today&apos;s summary.</Alert>}

      {data && (
        <Stack gap={3}>
          {/* ── Urgent actions ── */}
          {criticalAlerts.length > 0 && (
            <Box>
              <SectionTitle count={criticalAlerts.length}>Urgent Actions</SectionTitle>
              <Paper variant="outlined" sx={{ ...panelSx, borderColor: "#ef5350", background: "#fff8f8", px: 2.5 }}>
                <Stack divider={<Divider />}>
                  {criticalAlerts.map((a) => (
                    <AlertRow key={a.id} alert={a} onResolve={openResolve} onDismiss={handleDismiss} />
                  ))}
                </Stack>
              </Paper>
            </Box>
          )}

          {/* ── Pond status grid ── */}
          {data.ponds?.length > 0 && (
            <Box>
              <SectionTitle count={data.ponds.length}>Pond Status</SectionTitle>
              <Box
                sx={{
                  display: "grid",
                  gap: 2,
                  gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(3, minmax(0, 1fr))" },
                }}
              >
                {data.ponds.map((pond) => (
                  <PondCard pond={pond} key={pond.pond_id} />
                ))}
              </Box>
            </Box>
          )}

          {/* ── Other alerts ── */}
          {otherAlerts.length > 0 && (
            <Box>
              <SectionTitle count={otherAlerts.length}>Active Alerts</SectionTitle>
              <Paper variant="outlined" sx={{ ...panelSx, px: 2.5 }}>
                <Stack divider={<Divider />}>
                  {otherAlerts.map((a) => (
                    <AlertRow key={a.id} alert={a} onResolve={openResolve} onDismiss={handleDismiss} />
                  ))}
                </Stack>
              </Paper>
            </Box>
          )}

          {/* ── Tasks ── */}
          {data.tasks?.length > 0 && (
            <Box>
              <SectionTitle count={data.tasks.length}>Tasks Due Today</SectionTitle>
              <Paper variant="outlined" sx={{ ...panelSx, px: 2.5 }}>
                <Stack divider={<Divider />}>
                  {data.tasks.map((t) => (
                    <TaskRow key={t.id} task={t} onComplete={handleComplete} />
                  ))}
                </Stack>
              </Paper>
            </Box>
          )}

          {data.control_loops?.length > 0 && (
            <Box>
              <SectionTitle count={data.control_loops.length}>Actions Awaiting Outcome</SectionTitle>
              <Paper variant="outlined" sx={{ ...panelSx, px: 2.5 }}>
                <Stack divider={<Divider />}>
                  {data.control_loops.map((loop) => (
                    <ControlLoopRow key={loop.id} loop={loop} onRecordOutcome={setSelectedLoop} />
                  ))}
                </Stack>
              </Paper>
            </Box>
          )}

          {criticalAlerts.length === 0 && otherAlerts.length === 0 && data.tasks?.length === 0 && data.control_loops?.length === 0 && (
            <Alert severity="success" icon={<MdCheckCircleOutline />}>
              All clear — no urgent alerts or tasks due today.
            </Alert>
          )}
        </Stack>
      )}

      <Dialog open={!!selectedAlert} onClose={() => setSelectedAlert(null)} fullWidth maxWidth="sm">
        <DialogTitle>Record action and follow-up</DialogTitle>
        <DialogContent>
          <Stack gap={2} sx={{ pt: 1 }}>
            <Alert severity={selectedAlert?.severity === "critical" ? "error" : "warning"}>{selectedAlert?.message}</Alert>
            <TextField
              label="Action taken"
              value={actionForm.action}
              onChange={(event) => setActionForm((prev) => ({ ...prev, action: event.target.value }))}
              required
              multiline
              minRows={2}
              slotProps={{ htmlInput: { "aria-label": "Action taken" } }}
            />
            <TextField
              label="Expected benefit"
              value={actionForm.expected_benefit}
              onChange={(event) => setActionForm((prev) => ({ ...prev, expected_benefit: event.target.value }))}
            />
            <TextField
              label="Next check"
              type="datetime-local"
              value={actionForm.next_check_at}
              onChange={(event) => setActionForm((prev) => ({ ...prev, next_check_at: event.target.value }))}
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              label="Success signal"
              value={actionForm.success_signal}
              onChange={(event) => setActionForm((prev) => ({ ...prev, success_signal: event.target.value }))}
              placeholder="Example: DO remains above 5 mg/L"
            />
            <TextField
              select
              label="Confidence"
              value={actionForm.confidence}
              onChange={(event) => setActionForm((prev) => ({ ...prev, confidence: event.target.value }))}
            >
              {["low", "medium", "high"].map((value) => <MenuItem key={value} value={value}>{value}</MenuItem>)}
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedAlert(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleResolve} disabled={!actionForm.action.trim() || isCreatingLoop}>
            {isCreatingLoop ? "Recording..." : "Record action"}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!selectedLoop} onClose={() => setSelectedLoop(null)} fullWidth maxWidth="sm">
        <DialogTitle>Record action outcome</DialogTitle>
        <DialogContent>
          <Stack gap={2} sx={{ pt: 1 }}>
            <Typography fontWeight={700}>{selectedLoop?.action}</Typography>
            <TextField
              select
              label="Result"
              value={outcomeForm.outcome_status}
              onChange={(event) => setOutcomeForm((prev) => ({ ...prev, outcome_status: event.target.value }))}
            >
              <MenuItem value="worked">Worked</MenuItem>
              <MenuItem value="partial">Partially worked</MenuItem>
              <MenuItem value="failed">Did not work</MenuItem>
              <MenuItem value="unknown">Too early to tell</MenuItem>
            </TextField>
            <TextField
              label="What happened?"
              value={outcomeForm.outcome}
              onChange={(event) => setOutcomeForm((prev) => ({ ...prev, outcome: event.target.value }))}
              multiline
              minRows={3}
              required
              slotProps={{ htmlInput: { "aria-label": "What happened?" } }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedLoop(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleRecordOutcome} disabled={!outcomeForm.outcome.trim() || isRecordingOutcome}>
            {isRecordingOutcome ? "Recording..." : "Save outcome"}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TodayView;
