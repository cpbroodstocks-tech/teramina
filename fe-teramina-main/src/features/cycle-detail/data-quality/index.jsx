import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Collapse,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Tooltip,
  Typography,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { useQualityReport } from "features/cycle-data/queries";

const qualityColor = (pct) => {
  if (pct >= 80) return "success";
  if (pct >= 60) return "warning";
  return "error";
};

const qualityLabel = (pct) => {
  if (pct >= 80) return "Good";
  if (pct >= 60) return "Fair";
  return "Poor";
};

// Simple DOC completeness bar using inline divs (no extra charting dependency)
const CompletenessBar = ({ byDoc }) => {
  if (!byDoc?.length) return null;

  // Show at most 60 DOC bars to keep it compact
  const sample = byDoc.length > 60 ? byDoc.filter((_, i) => i % Math.ceil(byDoc.length / 60) === 0) : byDoc;

  return (
    <Box sx={{ overflowX: "auto", pb: 0.5 }}>
      <Box sx={{ display: "flex", alignItems: "flex-end", gap: "1px", minWidth: sample.length * 6 }}>
        {sample.map((d) => {
          const color =
            d.completeness_pct >= 80
              ? "#4caf50"
              : d.completeness_pct > 0
                ? "#ff9800"
                : "#e0e0e0";
          return (
            <Tooltip
              key={d.doc}
              title={`DOC ${d.doc} (${d.date}): ${d.completeness_pct}% complete`}
              placement="top"
            >
              <Box
                sx={{
                  width: 5,
                  height: Math.max(4, (d.completeness_pct / 100) * 36),
                  backgroundColor: color,
                  borderRadius: "1px",
                  cursor: "default",
                }}
              />
            </Tooltip>
          );
        })}
      </Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mt: 0.25 }}>
        <Typography variant="caption" color="textSecondary">DOC 1</Typography>
        <Typography variant="caption" color="textSecondary">DOC {byDoc[byDoc.length - 1]?.doc}</Typography>
      </Box>
    </Box>
  );
};

const DataQuality = () => {
  const { cycle_id } = useParams();
  const [expanded, setExpanded] = useState(false);
  const { data: report, isLoading } = useQualityReport(cycle_id);

  if (isLoading) {
    return (
      <Card sx={{ mt: 2 }}>
        <CardContent sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <CircularProgress size={16} />
          <Typography variant="body2" color="textSecondary">Loading data quality…</Typography>
        </CardContent>
      </Card>
    );
  }

  if (!report) return null;

  const {
    overall_completeness_pct,
    total_days_with_data,
    total_days_in_cycle,
    gap_windows,
    stale_since,
    anomaly_count,
    completeness_by_doc,
  } = report;

  const color = qualityColor(overall_completeness_pct);
  const label = qualityLabel(overall_completeness_pct);

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        {/* Header row */}
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}>
          <Typography variant="h6">Data Quality</Typography>
          <Chip
            label={`${label} — ${overall_completeness_pct}%`}
            color={color}
            size="small"
          />
          {anomaly_count > 0 && (
            <Chip label={`${anomaly_count} anomalies`} color="error" size="small" variant="outlined" />
          )}
          <IconButton size="small" onClick={() => setExpanded((v) => !v)} sx={{ ml: "auto" }}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        {/* Summary line */}
        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
          {total_days_with_data} of {total_days_in_cycle} days have data
          {gap_windows?.length > 0 && ` · ${gap_windows.length} gap${gap_windows.length > 1 ? "s" : ""} detected`}
        </Typography>

        {/* Stale alert */}
        {stale_since && (
          <Alert severity="warning" sx={{ mb: 1.5, py: 0 }}>
            No new data since {stale_since}
          </Alert>
        )}

        {/* Completeness bar (always visible) */}
        <CompletenessBar byDoc={completeness_by_doc} />

        {/* Expanded section: gap windows */}
        <Collapse in={expanded}>
          <Box sx={{ mt: 1.5 }}>
            {gap_windows?.length > 0 ? (
              <>
                <Typography variant="subtitle2" sx={{ mb: 0.5 }}>Gap Windows</Typography>
                <List dense disablePadding>
                  {gap_windows.map((g, i) => (
                    <ListItem key={i} disablePadding sx={{ py: 0.25 }}>
                      <ListItemText
                        primary={
                          <Typography variant="body2">
                            <strong>{g.days}-day gap</strong>: DOC {g.from_doc}–{g.to_doc}
                            {" "}
                            <Typography component="span" variant="caption" color="textSecondary">
                              ({g.from_date} → {g.to_date})
                            </Typography>
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </>
            ) : (
              <Typography variant="body2" color="success.main">No significant data gaps.</Typography>
            )}

            {anomaly_count > 0 && (
              <Alert severity="error" sx={{ mt: 1.5, py: 0 }}>
                {anomaly_count} physiological anomalies detected (DO, temperature, NH3, or ABW out of valid range). Check your data.
              </Alert>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default DataQuality;
