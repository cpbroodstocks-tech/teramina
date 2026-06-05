import { useState, useRef } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  List,
  ListItem,
  Typography,
} from "@mui/material";
import { useToastStore } from "store/toast.store";
import { useLoadCachedInsight } from "features/cycle-detail/queries";
import { getEndpoint } from "helper/axios";

const TYPES = ["performance", "water_quality", "feeding", "harvest", "economics", "weekly"];

const scoreColor = (score) => {
  if (score > 70) return "#388e3c";
  if (score > 40) return "#f9a825";
  return "#d32f2f";
};

const statusChipColor = (status) => {
  if (status === "good") return "success";
  if (status === "warning") return "warning";
  return "error";
};

const priorityChipColor = (priority) => {
  if (priority === "low") return "default";
  if (priority === "medium") return "warning";
  return "error";
};

const AiInsights = () => {
  const { cycle_id } = useParams();
  const { setToast } = useToastStore();
  const [type, setType] = useState("performance");
  const [insight, setInsight] = useState(null);
  const [cached, setCached] = useState(false);
  const [streamLoading, setStreamLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState("");
  const esRef = useRef(null);

  const { mutateAsync: loadCached, isPending: loadingCached } = useLoadCachedInsight();

  const loading = loadingCached || streamLoading;

  const handleLoadCached = async () => {
    try {
      setInsight(null);
      const result = await loadCached({ cycle_id, type });
      setInsight(result);
      setCached(true);
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to load insight" });
    }
  };

  const handleGenerateStreaming = () => {
    if (esRef.current) esRef.current.close();
    setInsight(null);
    setStreamLoading(true);
    setCached(false);
    setStreamStatus("Analyzing…");

    const baseUrl = getEndpoint() || "";
    const token = localStorage.getItem("authentication") || "";
    const url = `${baseUrl}/summarize/insight/stream?cycle_id=${cycle_id}&type=${type}`;

    let accumulated = "";
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        const processChunk = ({ done, value }) => {
          if (done) {
            setStreamLoading(false);
            setStreamStatus("");
            return;
          }
          const text = decoder.decode(value, { stream: true });
          const lines = text.split("\n");
          lines.forEach((line) => {
            if (!line.startsWith("data: ")) return;
            const raw = line.slice(6).trim();
            if (!raw) return;
            try {
              const event = JSON.parse(raw);
              if (event.type === "tool_call") {
                setStreamStatus(`Fetching ${event.tool}…`);
              } else if (event.type === "chunk") {
                accumulated += event.text;
              } else if (event.type === "done") {
                try {
                  let jsonStr = accumulated.trim();
                  if (jsonStr.startsWith("```")) {
                    jsonStr = jsonStr.split("```")[1];
                    if (jsonStr.startsWith("json")) jsonStr = jsonStr.slice(4);
                  }
                  setInsight(JSON.parse(jsonStr.trim()));
                } catch {
                  setToast({ open: true, variant: "error", text: "Failed to parse streamed insight" });
                }
                setStreamLoading(false);
                setStreamStatus("");
              } else if (event.type === "error") {
                setToast({ open: true, variant: "error", text: event.message || "Stream error" });
                setStreamLoading(false);
                setStreamStatus("");
              }
            } catch {
              // malformed chunk, skip
            }
          });
          return reader.read().then(processChunk);
        };

        return reader.read().then(processChunk);
      })
      .catch(() => {
        setToast({ open: true, variant: "error", text: "Streaming failed" });
        setStreamLoading(false);
        setStreamStatus("");
      });
  };

  return (
    <Box style={{ padding: "16px 0" }}>
      <Box style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
        {TYPES.map((t) => (
          <Button
            key={t}
            variant={type === t ? "contained" : "outlined"}
            size="small"
            onClick={() => setType(t)}
            style={{ textTransform: "capitalize" }}
          >
            {t.replace("_", " ")}
          </Button>
        ))}
      </Box>

      <Box style={{ display: "flex", gap: 8, marginBottom: 24, alignItems: "center", flexWrap: "wrap" }}>
        <Button variant="contained" onClick={handleGenerateStreaming} disabled={loading}>
          {streamLoading && streamStatus ? (
            <>
              <CircularProgress size={14} style={{ marginRight: 6, color: "#fff" }} />
              {streamStatus}
            </>
          ) : "Generate"}
        </Button>
        <Button variant="outlined" onClick={handleLoadCached} disabled={loading}>
          Load Cached
        </Button>
        {cached && <Chip label="Cached" size="small" color="info" />}
        {loading && !streamStatus && <CircularProgress size={18} />}
      </Box>

      {loading && (
        <Box style={{ display: "flex", justifyContent: "center", padding: 32 }}>
          <CircularProgress />
        </Box>
      )}

      {!loading && insight && (
        <Box style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Card>
            <CardContent>
              <Box style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
                <Box style={{ flex: 1 }}>
                  <Typography variant="h6" gutterBottom>Summary</Typography>
                  <Typography variant="body1">{insight.summary}</Typography>
                </Box>
                {insight.performance_score != null && (
                  <Box style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <CircularProgress
                      variant="determinate"
                      value={insight.performance_score}
                      size={72}
                      style={{ color: scoreColor(insight.performance_score) }}
                    />
                    <Typography variant="caption" style={{ marginTop: 4 }}>
                      {insight.performance_score}/100
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>

          {insight.metrics && insight.metrics.length > 0 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom style={{ fontWeight: 600 }}>Metrics</Typography>
              <Box style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
                {insight.metrics.map((m, i) => (
                  <Box key={i}>
                    <Card variant="outlined">
                      <CardContent style={{ paddingBottom: "12px !important" }}>
                        <Typography variant="body2" color="textSecondary">{m.name}</Typography>
                        <Typography variant="h6">
                          {m.current_value}
                          {m.unit && <span style={{ fontSize: 13, marginLeft: 4 }}>{m.unit}</span>}
                        </Typography>
                        {m.status && (
                          <Chip label={m.status} size="small" color={statusChipColor(m.status)} style={{ marginTop: 4 }} />
                        )}
                      </CardContent>
                    </Card>
                  </Box>
                ))}
              </Box>
            </Box>
          )}

          {insight.anomalies && insight.anomalies.length > 0 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom style={{ fontWeight: 600 }}>Anomalies</Typography>
              <List disablePadding>
                {insight.anomalies.map((a, i) => (
                  <ListItem key={i} disablePadding style={{ marginBottom: 8 }}>
                    <Card variant="outlined" style={{ width: "100%" }}>
                      <CardContent style={{ padding: "12px 16px" }}>
                        <Box style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                          <Chip label={a.severity} size="small" color={priorityChipColor(a.severity)} />
                          <Typography variant="body2">{a.description}</Typography>
                        </Box>
                        {a.recommendation && (
                          <Typography variant="caption" color="textSecondary">{a.recommendation}</Typography>
                        )}
                      </CardContent>
                    </Card>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {insight.recommendations && insight.recommendations.length > 0 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom style={{ fontWeight: 600 }}>Recommendations</Typography>
              <List disablePadding>
                {insight.recommendations.map((r, i) => (
                  <ListItem key={i} disablePadding style={{ marginBottom: 8 }}>
                    <Card variant="outlined" style={{ width: "100%" }}>
                      <CardContent style={{ padding: "12px 16px" }}>
                        <Box style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                          <Chip label={r.priority} size="small" color={priorityChipColor(r.priority)} />
                          <Typography variant="body2" style={{ fontWeight: 500 }}>{r.action}</Typography>
                        </Box>
                        {r.reason && (
                          <Typography variant="caption" color="textSecondary">{r.reason}</Typography>
                        )}
                      </CardContent>
                    </Card>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {insight.forecast_outlook && (
            <Typography variant="body2" color="textSecondary" style={{ fontStyle: "italic", marginTop: 8 }}>
              {insight.forecast_outlook}
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default AiInsights;
