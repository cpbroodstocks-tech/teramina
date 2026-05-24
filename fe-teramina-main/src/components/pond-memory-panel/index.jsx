import { useMemo } from "react";
import { Alert, Box, Button, Chip, CircularProgress, Divider, Paper, Stack, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useAgentMemories } from "components/agent-chat/queries";

const SECTIONS = [
  {
    key: "issues",
    label: "Issues & Events",
    types: ["event"],
    empty: "No pond events recorded yet.",
  },
  {
    key: "advice",
    label: "What Worked / Advice",
    types: ["advice"],
    empty: "No advice outcomes recorded yet.",
  },
  {
    key: "facts",
    label: "Facts & Preferences",
    types: ["fact", "preference"],
    empty: "No facts or preferences recorded yet.",
  },
  {
    key: "notes",
    label: "Notes",
    types: ["note"],
    empty: "No notes recorded yet.",
  },
];

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

  const grouped = useMemo(() => {
    const byType = {};
    memories.forEach((m) => {
      byType[m.memory_type] = byType[m.memory_type] || [];
      byType[m.memory_type].push(m);
    });
    return SECTIONS.map((section) => ({
      ...section,
      items: section.types.flatMap((t) => byType[t] || []).slice(0, 3),
    }));
  }, [memories]);

  const hasAny = memories.length > 0;

  if (!farmId || !pondId) return null;

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Stack direction={{ xs: "column", md: "row" }} gap={1.5} sx={{ justifyContent: "space-between", mb: 1.5 }}>
        <Box>
          <Typography variant="h6" fontWeight={700}>
            Pond Memory
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Remembered context for {pondName || "this pond"}.
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

      {!isLoading && !isError && !hasAny && (
        <Alert severity="info">
          No pond-specific memories yet. Add facts, events, or outcomes from the Memory page.
        </Alert>
      )}

      {!isLoading && !isError && hasAny && (
        <Stack gap={2}>
          {grouped.map((section, idx) => (
            <Box key={section.key}>
              {idx > 0 && <Divider sx={{ mb: 2 }} />}
              <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.5 }}>
                {section.label}
              </Typography>
              {section.items.length === 0 ? (
                <Typography variant="body2" color="text.disabled" sx={{ mt: 0.5 }}>
                  {section.empty}
                </Typography>
              ) : (
                <Stack gap={1} sx={{ mt: 0.5 }}>
                  {section.items.map((memory) => (
                    <Box key={memory.id} sx={{ borderLeft: "3px solid #eeeeee", pl: 1.5 }}>
                      <Stack direction="row" gap={1} sx={{ flexWrap: "wrap", mb: 0.5 }}>
                        <Chip size="small" color={memoryTone[memory.memory_type] || "default"} label={memory.memory_type} />
                        {!memory.is_verified && (
                          <Chip size="small" variant="outlined" color="warning" label="needs review" />
                        )}
                      </Stack>
                      <Typography variant="body2">{memory.content}</Typography>
                    </Box>
                  ))}
                </Stack>
              )}
            </Box>
          ))}
        </Stack>
      )}
    </Paper>
  );
};

export default PondMemoryPanel;
