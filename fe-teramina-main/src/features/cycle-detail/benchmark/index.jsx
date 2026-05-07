import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  Grid,
  Typography,
} from "@mui/material";
import { useToastStore } from "store/toast.store";
import {
  useBenchmarkPerformance,
  useOptInBenchmark,
  useOptOutBenchmark,
} from "features/cycle-detail/queries";

const MetricBar = ({ myValue, p25, p50, p75, cohortSize }) => {
  if (cohortSize < 5) {
    return (
      <Typography variant="caption" color="textSecondary">
        Insufficient data (need 5+ farms)
      </Typography>
    );
  }

  const max = Math.max(p75 * 1.2, myValue * 1.1) || 1;
  const toPercent = (v) => Math.min(100, (v / max) * 100);

  return (
    <Box style={{ position: "relative", marginTop: 8 }}>
      <Box style={{ height: 12, backgroundColor: "#e0e0e0", borderRadius: 6, position: "relative" }}>
        <Box style={{ position: "absolute", left: `${toPercent(p25)}%`, top: -4, bottom: -4, width: 2, backgroundColor: "#bdbdbd" }} />
        <Box style={{ position: "absolute", left: `${toPercent(p50)}%`, top: -4, bottom: -4, width: 2, backgroundColor: "#9e9e9e" }} />
        <Box style={{ position: "absolute", left: `${toPercent(p75)}%`, top: -4, bottom: -4, width: 2, backgroundColor: "#757575" }} />
        <Box style={{ position: "absolute", left: `${toPercent(myValue)}%`, top: -6, bottom: -6, width: 3, backgroundColor: "#474DA4", borderRadius: 2 }} />
      </Box>
      <Box style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
        <Typography variant="caption" color="textSecondary">p25: {p25}</Typography>
        <Typography variant="caption" color="textSecondary">p50: {p50}</Typography>
        <Typography variant="caption" color="textSecondary">p75: {p75}</Typography>
      </Box>
      <Typography variant="caption" color="textSecondary">{cohortSize} farms</Typography>
    </Box>
  );
};

const BenchmarkSection = () => {
  const { cycle_id } = useParams();
  const { setToast } = useToastStore();
  const [agreed, setAgreed] = useState(false);

  const { data, isLoading } = useBenchmarkPerformance(cycle_id);
  const { mutate: optIn, isPending: optingIn } = useOptInBenchmark(cycle_id);
  const { mutate: optOut } = useOptOutBenchmark(cycle_id);

  const handleOptIn = () => {
    optIn(undefined, {
      onError: () => setToast({ open: true, variant: "error", text: "Failed to opt in" }),
    });
  };

  const handleOptOut = () => {
    optOut(undefined, {
      onError: () => setToast({ open: true, variant: "error", text: "Failed to opt out" }),
    });
  };

  if (isLoading) {
    return (
      <Box style={{ display: "flex", justifyContent: "center", padding: 32 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!data) return null;

  if (!data.opted_in) {
    return (
      <Box style={{ padding: "16px 0" }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Farm Performance Benchmarking</Typography>
            <Typography variant="body2" color="textSecondary" style={{ marginBottom: 16 }}>
              Compare your farm performance with anonymized industry benchmarks
            </Typography>
            <FormControlLabel
              control={<Checkbox checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />}
              label="I agree to share anonymized farm metrics for benchmarking (minimum 5 farms required)"
            />
            <Box style={{ marginTop: 16 }}>
              <Button variant="contained" onClick={handleOptIn} disabled={!agreed || optingIn}>
                {optingIn ? <CircularProgress size={18} /> : "Enable Benchmarking"}
              </Button>
            </Box>
            <Typography variant="caption" color="textSecondary" display="block" style={{ marginTop: 12 }}>
              Your data is anonymized. Individual farm data is never exposed.
            </Typography>
          </CardContent>
        </Card>
      </Box>
    );
  }

  const metrics = data.performance?.metrics || {};

  return (
    <Box style={{ padding: "16px 0" }}>
      <Box style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
        <Button variant="text" size="small" color="error" onClick={handleOptOut}>Opt Out</Button>
      </Box>
      <Grid container spacing={2}>
        {Object.entries(metrics).map(([key, metric]) => {
          const aboveMedian = metric.my_value >= metric.p50;
          return (
            <Grid item xs={12} sm={6} md={4} key={key}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" style={{ textTransform: "capitalize", marginBottom: 4 }}>
                    {key.replace(/_/g, " ")}
                  </Typography>
                  <Typography variant="h6">{metric.my_value}</Typography>
                  <Chip
                    label={aboveMedian ? "Above Average" : "Below Average"}
                    size="small"
                    color={aboveMedian ? "success" : "warning"}
                    style={{ marginBottom: 8 }}
                  />
                  <MetricBar myValue={metric.my_value} p25={metric.p25} p50={metric.p50} p75={metric.p75} cohortSize={metric.cohort_size} />
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default BenchmarkSection;
