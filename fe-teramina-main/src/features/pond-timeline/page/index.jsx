import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  IconButton,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import {
  MdArrowBack,
  MdErrorOutline,
  MdMemory,
  MdNotificationsNone,
  MdOpacity,
  MdRefresh,
  MdScience,
  MdSupportAgent,
  MdTaskAlt,
} from "react-icons/md";
import { useGetPondTimeline } from "components/agent-chat/queries";
import { useAdvisoryHistory } from "features/advisory/queries";

const EVENT_CONFIG = {
  observation: {
    icon: <MdOpacity size={16} />,
    color: "#1976d2",
    bg: "#e3f2fd",
    label: "Water",
  },
  alert: {
    icon: <MdNotificationsNone size={16} />,
    color: "#d32f2f",
    bg: "#ffebee",
    label: "Alert",
  },
  memory_advice: {
    icon: <MdScience size={16} />,
    color: "#388e3c",
    bg: "#e8f5e9",
    label: "Advice",
  },
  memory_event: {
    icon: <MdMemory size={16} />,
    color: "#7b1fa2",
    bg: "#f3e5f5",
    label: "Event",
  },
  memory_note: {
    icon: <MdMemory size={16} />,
    color: "#616161",
    bg: "#f5f5f5",
    label: "Note",
  },
  memory_fact: {
    icon: <MdMemory size={16} />,
    color: "#0288d1",
    bg: "#e1f5fe",
    label: "Fact",
  },
  advisory_case: {
    icon: <MdSupportAgent size={16} />,
    color: "#6d4c41",
    bg: "#efebe9",
    label: "Advisory",
  },
  control_action: {
    icon: <MdTaskAlt size={16} />,
    color: "#ed6c02",
    bg: "#fff3e0",
    label: "Action",
  },
  control_outcome: {
    icon: <MdTaskAlt size={16} />,
    color: "#2e7d32",
    bg: "#e8f5e9",
    label: "Outcome",
  },
};

const getEventConfig = (type) => {
  if (EVENT_CONFIG[type]) return EVENT_CONFIG[type];
  if (type?.startsWith("memory_")) return EVENT_CONFIG.memory_note;
  return {
    icon: <MdErrorOutline size={16} />,
    color: "#616161",
    bg: "#f5f5f5",
    label: type || "Event",
  };
};

const FILTER_OPTIONS = [
  { value: "all", label: "All" },
  { value: "observation", label: "Water" },
  { value: "alert", label: "Alerts" },
  { value: "advice", label: "Advice" },
  { value: "advisory", label: "Advisory" },
  { value: "actions", label: "Actions" },
];

const TimelineEvent = ({ event, onOpen }) => {
  const config = getEventConfig(event.type);
  const docOrDate = event.doc != null
    ? `DOC ${event.doc}`
    : event.date
      ? new Date(event.date).toLocaleDateString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
      : null;

  return (
    <Stack direction="row" gap={2} sx={{ py: 1.5 }}>
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0.5, minWidth: 24 }}>
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            background: config.bg,
            color: config.color,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          {config.icon}
        </Box>
        <Box sx={{ width: 2, flex: 1, background: "#e0e0e0", minHeight: 8 }} />
      </Box>

      <Box flex={1} sx={{ pb: 1 }}>
        <Stack direction="row" gap={1} sx={{ mb: 0.5, alignItems: "center" }}>
          <Chip
            label={config.label}
            size="small"
            sx={{ height: 18, fontSize: 11, background: config.bg, color: config.color, fontWeight: 600 }}
          />
          {event.severity && (
            <Chip
              label={event.severity}
              size="small"
              color={event.severity === "critical" ? "error" : event.severity === "warning" ? "warning" : "info"}
              sx={{ height: 18, fontSize: 11 }}
            />
          )}
          {docOrDate && (
            <Typography variant="caption" color="text.secondary" sx={{ ml: "auto", flexShrink: 0 }}>
              {docOrDate}
            </Typography>
          )}
        </Stack>
        <Typography variant="body2" sx={{ fontSize: 13, lineHeight: 1.5 }}>
          {event.description}
        </Typography>
        {event.tags?.length > 0 && (
          <Stack direction="row" gap={0.5} sx={{ mt: 0.5, flexWrap: "wrap" }}>
            {event.tags.map((tag) => (
              <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ height: 16, fontSize: 10 }} />
            ))}
          </Stack>
        )}
        {event.url && (
          <Button size="small" onClick={() => onOpen(event.url)} sx={{ mt: 0.5, px: 0, minWidth: 0 }}>
            Open advisory case
          </Button>
        )}
      </Box>
    </Stack>
  );
};

const formatCaseType = (caseType) => (caseType || "advisory_case").replaceAll("_", " ");

const toAdvisoryTimelineEvent = (event) => ({
  ...event,
  date: event.created_at,
  description: event.description || `${formatCaseType(event.case_type)}: ${event.title}`,
  tags: [event.status, formatCaseType(event.case_type)].filter(Boolean),
});

const PondTimeline = () => {
  const { cycle_id } = useParams();
  const navigate = useNavigate();
  const [filter, setFilter] = useState("all");

  const { data, isLoading, isError, refetch } = useGetPondTimeline(cycle_id || null);
  const {
    data: advisoryHistory,
    isLoading: isAdvisoryLoading,
    isError: isAdvisoryError,
    refetch: refetchAdvisoryHistory,
  } = useAdvisoryHistory({ cycle_id });

  const events = data?.events || [];
  const advisoryEvents = (advisoryHistory?.events || []).map(toAdvisoryTimelineEvent);
  const combinedEvents = [...events, ...advisoryEvents];
  const filtered = combinedEvents.filter((e) => {
    if (filter === "all") return true;
    if (filter === "observation") return e.type === "observation";
    if (filter === "alert") return e.type === "alert";
    if (filter === "advice") return e.type === "memory_advice" || e.type?.startsWith("memory_");
    if (filter === "advisory") return e.type === "advisory_case";
    if (filter === "actions") return e.type === "control_action" || e.type === "control_outcome";
    return true;
  });
  const totalEvents = (data?.total_events ?? events.length) + advisoryEvents.length;

  return (
    <Box>
      <Stack direction="row" gap={1} sx={{ mb: 3, alignItems: "center" }}>
        <IconButton size="small" onClick={() => navigate(-1)} title="Back" aria-label="Go back">
          <MdArrowBack />
        </IconButton>
        <Box flex={1}>
          <Typography variant="h4" fontWeight={700}>
            Pond Timeline
          </Typography>
          {data?.cycle_name && (
            <Typography variant="body2" color="text.secondary">
              {data.cycle_name}
              {data.start_date && ` — started ${new Date(data.start_date).toLocaleDateString()}`}
            </Typography>
          )}
        </Box>
        <IconButton
          onClick={() => {
            refetch();
            refetchAdvisoryHistory();
          }}
          title="Refresh"
          aria-label="Refresh timeline"
        >
          <MdRefresh />
        </IconButton>
      </Stack>

      <ToggleButtonGroup
        value={filter}
        exclusive
        onChange={(_, v) => v && setFilter(v)}
        size="small"
        sx={{ mb: 2 }}
      >
        {FILTER_OPTIONS.map((opt) => (
          <ToggleButton key={opt.value} value={opt.value} sx={{ fontSize: 12, px: 2 }}>
            {opt.label}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>

      {isLoading || isAdvisoryLoading ? (
        <Stack direction="row" gap={1} sx={{ alignItems: "center" }}>
          <CircularProgress size={18} />
          <Typography variant="body2">Loading timeline…</Typography>
        </Stack>
      ) : null}

      {isError && <Alert severity="error">Failed to load pond timeline.</Alert>}
      {isAdvisoryError && <Alert severity="warning" sx={{ mb: 2 }}>Timeline loaded, but advisory history could not be loaded.</Alert>}

      {!isLoading && !isAdvisoryLoading && !isError && filtered.length === 0 && (
        <Alert severity="info">No events found for this filter.</Alert>
      )}

      {!isLoading && !isAdvisoryLoading && filtered.length > 0 && (
        <Card variant="outlined">
          <CardContent sx={{ pb: "12px !important" }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: "block" }}>
              {totalEvents} total events — showing {filtered.length}
            </Typography>
            <Divider sx={{ mb: 1 }} />
            <Stack>
              {filtered.map((event, i) => (
                <TimelineEvent key={`${event.type}-${event.id || event.description}-${i}`} event={event} onOpen={navigate} />
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PondTimeline;
