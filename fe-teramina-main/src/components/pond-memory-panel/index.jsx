import { Alert, Box, Button, Chip, CircularProgress, Paper, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useAgentMemories } from "components/agent-chat/queries";

const memoryTone = {
  fact: "default",
  preference: "primary",
  event: "warning",
  advice: "success",
  note: "default",
};

const PondMemoryPanel = ({ farmId, pondId, pondName }) => {
  const navigate = useNavigate();
  const { data: memories = [], isLoading, isError } = useAgentMemories({
    enabled: !!farmId && !!pondId,
    farm_id: farmId,
    pond_id: pondId,
  });

  const recent = memories.slice(0, 4);

  if (!farmId || !pondId) return null;

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Stack direction={{ xs: "column", md: "row" }} gap={1.5} sx={{ justifyContent: "space-between", mb: 1.5 }}>
        <Box>
          <Typography variant="h6" fontWeight={700}>
            Pond Memory
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Recent remembered context for {pondName || "this pond"}.
          </Typography>
        </Box>
        <Button size="small" variant="outlined" onClick={() => navigate("/dashboard/memory")}>
          Manage memory
        </Button>
      </Stack>

      {isLoading && (
        <Stack direction="row" gap={1} sx={{ alignItems: "center" }}>
          <CircularProgress size={16} />
          <Typography variant="body2">Loading pond memory...</Typography>
        </Stack>
      )}

      {isError && <Alert severity="error">Failed to load pond memory.</Alert>}

      {!isLoading && !isError && recent.length === 0 && (
        <Alert severity="info">
          No pond-specific memories yet. Add facts, events, or outcomes from the Memory page.
        </Alert>
      )}

      {!isLoading && !isError && recent.length > 0 && (
        <Stack gap={1}>
          {recent.map((memory) => (
            <Box key={memory.id} sx={{ borderTop: "1px solid #eeeeee", pt: 1 }}>
              <Stack direction="row" gap={1} sx={{ flexWrap: "wrap", mb: 0.5 }}>
                <Chip size="small" color={memoryTone[memory.memory_type] || "default"} label={memory.memory_type} />
                <Chip
                  size="small"
                  variant="outlined"
                  label={memory.is_verified ? "verified" : "unverified"}
                />
              </Stack>
              <Typography variant="body2">{memory.content}</Typography>
            </Box>
          ))}
        </Stack>
      )}
    </Paper>
  );
};

export default PondMemoryPanel;
