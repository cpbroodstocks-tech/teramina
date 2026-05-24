import { useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  Stack,
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
  useInvalidateAgentAlerts,
  useInvalidateAgentTasks,
} from "components/agent-chat/queries";
import { useToastStore } from "store/toast.store";

const STATUS_COLORS = {
  ok: { bg: "#e8f5e9", border: "#66bb6a", label: "#2e7d32" },
  warning: { bg: "#fff8e1", border: "#ffa726", label: "#e65100" },
  critical: { bg: "#ffebee", border: "#ef5350", label: "#b71c1c" },
  unknown: { bg: "#f5f5f5", border: "#bdbdbd", label: "#616161" },
};

const worstStatus = (...statuses) => {
  if (statuses.includes("critical")) return "critical";
  if (statuses.includes("warning")) return "warning";
  if (statuses.includes("ok")) return "ok";
  return "unknown";
};

const SectionTitle = ({ children }) => (
  <Typography variant="h6" fontWeight={700} sx={{ mb: 1.5 }}>
    {children}
  </Typography>
);

const PondCard = ({ pond }) => {
  const navigate = useNavigate();
  const status = worstStatus(pond.do_status, pond.nh3_status);
  const colors = STATUS_COLORS[status];

  return (
    <Card
      variant="outlined"
      sx={{
        background: colors.bg,
        borderColor: colors.border,
        borderWidth: status !== "ok" ? 2 : 1,
        height: "100%",
      }}
    >
      <CardContent sx={{ pb: "12px !important" }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="subtitle2" fontWeight={700} color={colors.label}>
              {pond.pond_name}
            </Typography>
            {pond.current_doc != null && (
              <Typography variant="caption" color="text.secondary">
                DOC {pond.current_doc}
              </Typography>
            )}
          </Box>
          {status !== "ok" && (
            <MdWarningAmber size={18} color={colors.label} />
          )}
        </Stack>

        <Stack gap={0.5} sx={{ mt: 1 }}>
          {pond.do_avg != null && (
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="caption" color="text.secondary">DO</Typography>
              <Chip
                label={`${pond.do_avg} mg/L`}
                size="small"
                color={pond.do_status === "critical" ? "error" : pond.do_status === "warning" ? "warning" : "success"}
                sx={{ height: 18, fontSize: 11 }}
              />
            </Stack>
          )}
          {pond.temp_avg != null && (
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="caption" color="text.secondary">Suhu</Typography>
              <Typography variant="caption">{pond.temp_avg}°C</Typography>
            </Stack>
          )}
          {pond.nh3 != null && (
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="caption" color="text.secondary">NH3</Typography>
              <Chip
                label={`${pond.nh3} mg/L`}
                size="small"
                color={pond.nh3_status === "critical" ? "error" : pond.nh3_status === "warning" ? "warning" : "success"}
                sx={{ height: 18, fontSize: 11 }}
              />
            </Stack>
          )}
          {pond.abw_g != null && (
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="caption" color="text.secondary">ABW</Typography>
              <Typography variant="caption">{pond.abw_g}g</Typography>
            </Stack>
          )}
        </Stack>

        {pond.active_cycle_id && (
          <Stack direction="row" gap={0.5} sx={{ mt: 1 }}>
            <Button
              size="small"
              startIcon={<MdSmartToy size={12} />}
              onClick={() => {
                localStorage.setItem("pond_id", pond.pond_id);
                localStorage.setItem("pond_name", pond.pond_name);
                localStorage.setItem("cycle_id", pond.active_cycle_id);
                window.dispatchEvent(new CustomEvent("open-agent-chat", {
                  detail: { message: `What should I do about ${pond.pond_name} today? DO: ${pond.do_avg ?? "?"} mg/L, NH3: ${pond.nh3 ?? "?"} mg/L, DOC: ${pond.current_doc ?? "?"}` },
                }));
              }}
              sx={{ fontSize: 11, p: "2px 8px" }}
            >
              Ask
            </Button>
            <Button
              size="small"
              startIcon={<MdTimeline size={12} />}
              onClick={() => navigate(`/dashboard/pond-timeline/${pond.active_cycle_id}`)}
              sx={{ fontSize: 11, p: "2px 8px" }}
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
    <Stack direction="row" alignItems="flex-start" gap={1} sx={{ py: 1 }}>
      <Chip label={alert.severity} size="small" color={color} sx={{ flexShrink: 0 }} />
      <Typography variant="body2" sx={{ flex: 1, fontSize: 13 }}>{alert.message}</Typography>
      <Tooltip title="Mark resolved">
        <IconButton size="small" onClick={() => onResolve(alert.id)} sx={{ color: "#4caf50" }}>
          <MdDone size={16} />
        </IconButton>
      </Tooltip>
      <Tooltip title="Dismiss">
        <IconButton size="small" onClick={() => onDismiss(alert.id)}>
          <MdDeleteOutline size={16} />
        </IconButton>
      </Tooltip>
    </Stack>
  );
};

const TaskRow = ({ task, onComplete }) => {
  const due = task.due_at ? new Date(task.due_at) : null;
  const overdue = task.is_overdue;
  return (
    <Stack direction="row" alignItems="flex-start" gap={1} sx={{ py: 1 }}>
      <Box flex={1}>
        <Typography variant="body2" sx={{ fontSize: 13, fontWeight: overdue ? 600 : 400 }}>
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
        <IconButton size="small" onClick={() => onComplete(task.id)} sx={{ color: "#4caf50" }}>
          <MdCheckCircleOutline size={18} />
        </IconButton>
      </Tooltip>
    </Stack>
  );
};

const TodayView = () => {
  const { setToast } = useToastStore();
  const farmId = localStorage.getItem("farm_id") || "";

  const { data, isLoading, isError, refetch } = useGetTodaySummary(farmId || null);
  const invalidateAlerts = useInvalidateAgentAlerts();
  const invalidateTasks = useInvalidateAgentTasks();
  const { mutateAsync: resolveAlert } = useResolveAlert();
  const { mutateAsync: dismissAlert } = useDismissAlert();
  const { mutateAsync: completeTask } = useCompleteAgentTask();

  const handleResolve = async (alertId) => {
    try {
      await resolveAlert(alertId);
      invalidateAlerts();
      refetch();
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to resolve alert" });
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

  const criticalAlerts = (data?.alerts || []).filter((a) => a.severity === "critical");
  const otherAlerts = (data?.alerts || []).filter((a) => a.severity !== "critical");

  if (!farmId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">Select a farm to see today&apos;s summary.</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
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
        <IconButton onClick={() => refetch()} title="Refresh">
          <MdRefresh />
        </IconButton>
      </Stack>

      {isLoading && (
        <Stack direction="row" gap={1} alignItems="center">
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
              <SectionTitle>Urgent Actions</SectionTitle>
              <Card variant="outlined" sx={{ borderColor: "#ef5350", borderWidth: 2, background: "#fff5f5" }}>
                <CardContent sx={{ pb: "12px !important" }}>
                  <Stack divider={<Divider />}>
                    {criticalAlerts.map((a) => (
                      <AlertRow key={a.id} alert={a} onResolve={handleResolve} onDismiss={handleDismiss} />
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Box>
          )}

          {/* ── Pond status grid ── */}
          {data.ponds?.length > 0 && (
            <Box>
              <SectionTitle>Pond Status</SectionTitle>
              <Grid container spacing={2}>
                {data.ponds.map((pond) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={pond.pond_id}>
                    <PondCard pond={pond} />
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {/* ── Other alerts ── */}
          {otherAlerts.length > 0 && (
            <Box>
              <SectionTitle>Active Alerts</SectionTitle>
              <Card variant="outlined">
                <CardContent sx={{ pb: "12px !important" }}>
                  <Stack divider={<Divider />}>
                    {otherAlerts.map((a) => (
                      <AlertRow key={a.id} alert={a} onResolve={handleResolve} onDismiss={handleDismiss} />
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Box>
          )}

          {/* ── Tasks ── */}
          {data.tasks?.length > 0 && (
            <Box>
              <SectionTitle>Tasks Due Today</SectionTitle>
              <Card variant="outlined">
                <CardContent sx={{ pb: "12px !important" }}>
                  <Stack divider={<Divider />}>
                    {data.tasks.map((t) => (
                      <TaskRow key={t.id} task={t} onComplete={handleComplete} />
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            </Box>
          )}

          {criticalAlerts.length === 0 && otherAlerts.length === 0 && data.tasks?.length === 0 && (
            <Alert severity="success" icon={<MdCheckCircleOutline />}>
              All clear — no urgent alerts or tasks due today.
            </Alert>
          )}
        </Stack>
      )}
    </Box>
  );
};

export default TodayView;
