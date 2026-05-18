import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
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
} from "react-icons/md";
import { useGetPondTimeline } from "components/agent-chat/queries";

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
];

const TimelineEvent = ({ event }) => {
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
        <Stack direction="row" gap={1} alignItems="center" sx={{ mb: 0.5 }}>
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
      </Box>
    </Stack>
  );
};

const PondTimeline = () => {
  const { cycle_id } = useParams();
  const navigate = useNavigate();
  const [filter, setFilter] = useState("all");

  const { data, isLoading, isError, refetch } = useGetPondTimeline(cycle_id || null);

  const events = data?.events || [];
  const filtered = events.filter((e) => {
    if (filter === "all") return true;
    if (filter === "observation") return e.type === "observation";
    if (filter === "alert") return e.type === "alert";
    if (filter === "advice") return e.type === "memory_advice" || e.type?.startsWith("memory_");
    return true;
  });

  return (
    <Box>
      <Stack direction="row" alignItems="center" gap={1} sx={{ mb: 3 }}>
        <IconButton size="small" onClick={() => navigate(-1)} title="Back">
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
        <IconButton onClick={() => refetch()} title="Refresh">
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

      {isLoading && (
        <Stack direction="row" gap={1} alignItems="center">
          <CircularProgress size={18} />
          <Typography variant="body2">Loading timeline…</Typography>
        </Stack>
      )}

      {isError && <Alert severity="error">Failed to load pond timeline.</Alert>}

      {!isLoading && !isError && filtered.length === 0 && (
        <Alert severity="info">No events found for this filter.</Alert>
      )}

      {!isLoading && filtered.length > 0 && (
        <Card variant="outlined">
          <CardContent sx={{ pb: "12px !important" }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: "block" }}>
              {data?.total_events} total events — showing {filtered.length}
            </Typography>
            <Divider sx={{ mb: 1 }} />
            <Stack>
              {filtered.map((event, i) => (
                <TimelineEvent key={i} event={event} />
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PondTimeline;
