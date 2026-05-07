import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import { useToastStore } from "store/toast.store";
import { useFeedingRecommendation, useOverrideFeedingRecommendation } from "features/cycle-detail/queries";

const FeedingRecommendation = () => {
  const { cycle_id } = useParams();
  const { setToast } = useToastStore();
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [overrideKg, setOverrideKg] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideRecorded, setOverrideRecorded] = useState(false);

  const { data, isLoading } = useFeedingRecommendation(cycle_id);
  const { mutate: override, isPending: submitting } = useOverrideFeedingRecommendation(cycle_id);

  const handleOverrideSubmit = () => {
    override(
      { doc: data?.doc, actual_kg: parseFloat(overrideKg), override_reason: overrideReason },
      {
        onSuccess: () => {
          setOverrideRecorded(true);
          setShowOverrideForm(false);
          setToast({ open: true, variant: "success", text: "Override recorded" });
        },
        onError: () => setToast({ open: true, variant: "error", text: "Failed to record override" }),
      }
    );
  };

  if (isLoading) {
    return (
      <Box style={{ display: "flex", justifyContent: "center", padding: 32 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!data) return null;

  return (
    <Box style={{ padding: "16px 0" }}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Today&apos;s Feeding Recommendation</Typography>

          <Typography variant="h3" style={{ fontWeight: 700, marginBottom: 4 }}>
            {data.recommended_ration_kg} <span style={{ fontSize: 18 }}>kg</span>
          </Typography>

          {data.adjustment_reason && (
            <Typography variant="body2" color="textSecondary" style={{ marginBottom: 8 }}>
              {data.adjustment_reason}
            </Typography>
          )}

          {data.model_layer && (
            <Typography variant="body2" style={{ marginBottom: 8 }}>
              Model: <strong>{data.model_layer}</strong>
            </Typography>
          )}

          {overrideRecorded ? (
            <Typography variant="body2" color="success.main">Override recorded</Typography>
          ) : (
            <Box style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <Button
                variant="outlined"
                color="success"
                onClick={() => setToast({ open: true, variant: "success", text: "Recommendation accepted" })}
              >
                Accept
              </Button>
              <Button variant="text" onClick={() => setShowOverrideForm((prev) => !prev)}>
                Override
              </Button>
            </Box>
          )}

          {showOverrideForm && !overrideRecorded && (
            <Box style={{ marginTop: 16, padding: 12, border: "1px solid #e0e0e0", borderRadius: 8, display: "flex", flexDirection: "column", gap: 12 }}>
              <TextField
                label="Actual kg"
                type="number"
                size="small"
                value={overrideKg}
                onChange={(e) => setOverrideKg(e.target.value)}
                style={{ width: 160 }}
              />
              <TextField
                label="Reason"
                size="small"
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                fullWidth
              />
              <Box style={{ display: "flex", gap: 8 }}>
                <Button variant="contained" size="small" onClick={handleOverrideSubmit} disabled={submitting || !overrideKg}>
                  {submitting ? <CircularProgress size={16} /> : "Submit"}
                </Button>
                <Button variant="text" size="small" onClick={() => setShowOverrideForm(false)}>
                  Cancel
                </Button>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default FeedingRecommendation;
