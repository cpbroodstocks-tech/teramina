import { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { MdDeleteOutline, MdRefresh } from "react-icons/md";
import {
  useAgentMemoryGraph,
  useAgentMemories,
  useCreateAgentMemory,
  useDeleteAgentMemory,
} from "components/agent-chat/queries";
import { useToastStore } from "store/toast.store";

const typeOptions = ["all", "fact", "preference", "event", "advice", "note"];

const formatDate = (value) => {
  if (!value) return "-";
  return new Date(value).toLocaleString();
};

const MemoryPage = () => {
  const { setToast } = useToastStore();
  const [type, setType] = useState("all");
  const [query, setQuery] = useState("");
  const [useCurrentContext, setUseCurrentContext] = useState(true);
  const [newType, setNewType] = useState("note");
  const [newContent, setNewContent] = useState("");
  const [newTags, setNewTags] = useState("");
  const [saveWithContext, setSaveWithContext] = useState(true);
  const farmId = useCurrentContext ? localStorage.getItem("farm_id") || "" : "";
  const pondId = useCurrentContext ? localStorage.getItem("pond_id") || "" : "";
  const currentFarmId = localStorage.getItem("farm_id") || "";
  const currentPondId = localStorage.getItem("pond_id") || "";
  const currentCycleId = localStorage.getItem("cycle_id") || "";
  const farmName = localStorage.getItem("farm_name") || "";
  const pondName = localStorage.getItem("pond_name") || "";

  const { data: memories = [], isLoading, isError, refetch } = useAgentMemories({
    enabled: true,
    farm_id: farmId,
    pond_id: pondId,
  });
  const {
    data: graph = { entities: [], relations: [], observations: [] },
    isLoading: isGraphLoading,
    isError: isGraphError,
    refetch: refetchGraph,
  } = useAgentMemoryGraph({
    enabled: true,
    farm_id: farmId,
    pond_id: pondId,
  });
  const { mutateAsync: deleteMemory, isPending: deleting } = useDeleteAgentMemory();
  const { mutateAsync: createMemory, isPending: creating } = useCreateAgentMemory();

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return memories.filter((memory) => {
      const matchesType = type === "all" || memory.memory_type === type;
      if (!normalized) return matchesType;
      return (
        matchesType &&
        (
          memory.content.toLowerCase().includes(normalized) ||
          memory.tags.some((tag) => tag.toLowerCase().includes(normalized))
        )
      );
    });
  }, [memories, query, type]);

  const recentGraphObservations = useMemo(() => graph.observations.slice(0, 3), [graph.observations]);

  const handleDelete = async (memoryId) => {
    try {
      await deleteMemory(memoryId);
      setToast({ open: true, variant: "success", text: "Memory deleted" });
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to delete memory" });
    }
  };

  const handleCreate = async () => {
    const content = newContent.trim();
    if (!content) {
      setToast({ open: true, variant: "error", text: "Memory content is required" });
      return;
    }
    if (saveWithContext && !currentFarmId) {
      setToast({ open: true, variant: "error", text: "Select a farm before saving contextual memory" });
      return;
    }

    const tags = newTags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    try {
      await createMemory({
        farm_id: saveWithContext ? currentFarmId : "",
        pond_id: saveWithContext ? currentPondId : "",
        cycle_id: saveWithContext ? currentCycleId : "",
        memory_type: newType,
        content,
        tags,
      });
      setNewContent("");
      setNewTags("");
      setNewType("note");
      setToast({ open: true, variant: "success", text: "Memory saved" });
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to save memory" });
    }
  };

  const contextLabel = [farmName || farmId, pondName || pondId].filter(Boolean).join(" / ");

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Farmer Memory
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Review what the assistant can remember for future recommendations.
          </Typography>
        </Box>
        <IconButton
          onClick={() => {
            refetch();
            refetchGraph();
          }}
          title="Refresh"
        >
          <MdRefresh />
        </IconButton>
      </Stack>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600} mb={1.5}>
          Add verified memory
        </Typography>
        <Stack direction={{ xs: "column", md: "row" }} gap={2} sx={{ alignItems: { md: "flex-start" } }}>
          <TextField
            select
            size="small"
            label="Type"
            value={newType}
            onChange={(event) => setNewType(event.target.value)}
            sx={{ minWidth: 170 }}
          >
            {typeOptions.filter((option) => option !== "all").map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            size="small"
            label="What should Teramina remember?"
            value={newContent}
            onChange={(event) => setNewContent(event.target.value)}
            multiline
            minRows={2}
            fullWidth
          />
          <TextField
            size="small"
            label="Tags"
            value={newTags}
            onChange={(event) => setNewTags(event.target.value)}
            placeholder="do, harvest"
            sx={{ minWidth: 180 }}
          />
        </Stack>
        <Stack direction={{ xs: "column", md: "row" }} gap={1.5} sx={{ alignItems: { md: "center" }, mt: 1.5 }}>
          <Button
            variant={saveWithContext ? "contained" : "outlined"}
            onClick={() => setSaveWithContext((value) => !value)}
          >
            {saveWithContext ? "Save to current context" : "Save without context"}
          </Button>
          <Button variant="contained" disabled={creating} onClick={handleCreate}>
            Save memory
          </Button>
          {saveWithContext && contextLabel && (
            <Typography variant="body2" color="text.secondary">
              {contextLabel}
            </Typography>
          )}
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600} mb={1.5}>
          Review memories
        </Typography>
        <Stack direction={{ xs: "column", md: "row" }} gap={2} sx={{ alignItems: { md: "center" } }}>
          <TextField
            size="small"
            label="Search memory"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            sx={{ minWidth: 260 }}
          />
          <TextField
            select
            size="small"
            label="Type"
            value={type}
            onChange={(event) => setType(event.target.value)}
            sx={{ minWidth: 180 }}
          >
            {typeOptions.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
          <Button
            variant={useCurrentContext ? "contained" : "outlined"}
            onClick={() => setUseCurrentContext((value) => !value)}
          >
            {useCurrentContext ? "Current context" : "All memories"}
          </Button>
          {contextLabel && (
            <Typography variant="body2" color="text.secondary">
              {contextLabel}
            </Typography>
          )}
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Stack direction={{ xs: "column", md: "row" }} gap={2} sx={{ justifyContent: "space-between", mb: 1.5 }}>
          <Box>
            <Typography variant="subtitle1" fontWeight={600}>
              Graph memory
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Connected farm, pond, cycle, action, and observation context.
            </Typography>
          </Box>
          <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
            <Chip size="small" label={`${graph.entities.length} entities`} />
            <Chip size="small" label={`${graph.relations.length} links`} />
            <Chip size="small" label={`${graph.observations.length} observations`} />
          </Stack>
        </Stack>

        {isGraphLoading && (
          <Stack direction="row" gap={1} sx={{ alignItems: "center" }}>
            <CircularProgress size={18} />
            <Typography variant="body2">Loading graph memory...</Typography>
          </Stack>
        )}

        {isGraphError && <Alert severity="error">Failed to load graph memory.</Alert>}

        {!isGraphLoading && !isGraphError && recentGraphObservations.length === 0 && (
          <Alert severity="info">No graph observations for the current filters yet.</Alert>
        )}

        {!isGraphLoading && !isGraphError && recentGraphObservations.length > 0 && (
          <Stack gap={1}>
            {recentGraphObservations.map((observation) => (
              <Box key={observation.id} sx={{ borderTop: "1px solid #eeeeee", pt: 1 }}>
                <Stack direction="row" gap={1} sx={{ flexWrap: "wrap", mb: 0.5 }}>
                  <Chip size="small" label={observation.observation_type} />
                  <Chip
                    size="small"
                    color={observation.is_verified ? "success" : "default"}
                    label={observation.is_verified ? "verified" : "unverified"}
                  />
                  <Chip size="small" variant="outlined" label={`confidence ${observation.confidence}`} />
                </Stack>
                <Typography variant="body2">{observation.content}</Typography>
              </Box>
            ))}
          </Stack>
        )}
      </Paper>

      {isLoading && (
        <Stack direction="row" gap={1} sx={{ alignItems: "center" }}>
          <CircularProgress size={18} />
          <Typography variant="body2">Loading memories...</Typography>
        </Stack>
      )}

      {isError && <Alert severity="error">Failed to load memories.</Alert>}

      {!isLoading && !isError && filtered.length === 0 && (
        <Alert severity="info">No memories match the current filters.</Alert>
      )}

      <Stack gap={1.5}>
        {filtered.map((memory) => (
          <Paper key={memory.id} variant="outlined" sx={{ p: 2 }}>
            <Stack direction="row" gap={1.5} sx={{ alignItems: "flex-start" }}>
              <Box flex={1}>
                <Stack direction="row" gap={1} sx={{ flexWrap: "wrap", mb: 1 }}>
                  <Chip size="small" label={memory.memory_type} />
                  <Chip
                    size="small"
                    color={memory.is_verified ? "success" : "default"}
                    label={memory.is_verified ? "verified" : "unverified"}
                  />
                  <Chip size="small" variant="outlined" label={memory.source} />
                  {memory.confidence != null && (
                    <Chip
                      size="small"
                      variant="outlined"
                      label={`${Math.round(memory.confidence * 100)}%`}
                      sx={{
                        color: memory.confidence >= 0.8 ? "#2e7d32" : memory.confidence >= 0.6 ? "#e65100" : "#616161",
                        borderColor: memory.confidence >= 0.8 ? "#66bb6a" : memory.confidence >= 0.6 ? "#ffa726" : "#bdbdbd",
                      }}
                    />
                  )}
                </Stack>
                <Typography variant="body1" mb={1}>
                  {memory.content}
                </Typography>
                {memory.tags.length > 0 && (
                  <Stack direction="row" gap={0.5} sx={{ flexWrap: "wrap", mb: 1 }}>
                    {memory.tags.map((tag) => (
                      <Chip key={tag} size="small" variant="outlined" label={tag} />
                    ))}
                  </Stack>
                )}
                <Typography variant="caption" color="text.secondary">
                  Created {formatDate(memory.created_at)}
                </Typography>
              </Box>
              <IconButton
                size="small"
                disabled={deleting}
                onClick={() => handleDelete(memory.id)}
                title="Delete memory"
              >
                <MdDeleteOutline />
              </IconButton>
            </Stack>
          </Paper>
        ))}
      </Stack>
    </Box>
  );
};

export default MemoryPage;
