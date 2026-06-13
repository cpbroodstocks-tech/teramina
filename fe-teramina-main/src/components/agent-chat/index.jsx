import { useState, useEffect, useRef } from "react";
import { useLocation, useParams } from "react-router-dom";
import {
  Drawer,
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
} from "@mui/material";
import { MdExpandMore, MdClose, MdSend, MdDeleteOutline, MdDone, MdAlarm, MdGroups } from "react-icons/md";
import ReactMarkdown from "react-markdown";
import { useToastStore } from "store/toast.store";
import {
  useAgentAlerts,
  useGetAgentHistory,
  useDeleteAgentSession,
  useDismissAlert,
  useResolveAlert,
  useGetAgentTasks,
  useCompleteAgentTask,
  useExplainForTeam,
  useCreateAgentMemory,
} from "components/agent-chat/queries";
import { buildAgentContext } from "components/agent-chat/context";
import { getEndpoint } from "helper/axios";
import { useDashboardContextStore } from "store/dashboard-context.store";

const SESSION_KEY = "agent_session_id";

const severityColor = (severity) => {
  if (severity === "critical" || severity === "high") return "error";
  if (severity === "warning" || severity === "medium") return "warning";
  if (severity === "info") return "info";
  return "default";
};

const extractMemoryCandidate = (message) => {
  const trimmed = message.trim();
  const patterns = [
    /^please remember(?: that)?\s+/i,
    /^remember(?: that)?\s+/i,
    /^ingat(?: bahwa)?\s+/i,
    /^tolong ingat(?: bahwa)?\s+/i,
  ];
  for (const pattern of patterns) {
    const content = trimmed.replace(pattern, "").trim();
    if (content !== trimmed && content.length > 5) {
      return { content, memory_type: "note", tags: ["chat_confirmation"] };
    }
  }
  return null;
};

const AgentChat = ({ open, onClose, onAlertsLoaded, initialMessage, onInitialMessageConsumed }) => {
  const { setToast } = useToastStore();
  const params = useParams();
  const location = useLocation();
  const dashboardContext = useDashboardContextStore();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem(SESSION_KEY) || "");
  const messagesEndRef = useRef(null);
  const abortRef = useRef(null);

  const { data: alerts = [] } = useAgentAlerts(open);
  const { data: tasks = [] } = useGetAgentTasks(open);
  const { data: historyMessages } = useGetAgentHistory(open && sessionId ? sessionId : null);
  const { mutateAsync: deleteSession } = useDeleteAgentSession();
  const { mutateAsync: dismissAlert } = useDismissAlert();
  const { mutateAsync: resolveAlert } = useResolveAlert();
  const { mutateAsync: completeTask } = useCompleteAgentTask();
  const { mutateAsync: explainForTeam, isPending: explaining } = useExplainForTeam();
  const { mutateAsync: createMemory, isPending: savingMemory } = useCreateAgentMemory();

  useEffect(() => {
    if (onAlertsLoaded) onAlertsLoaded(alerts.length);
  }, [alerts.length]);

  useEffect(() => {
    if (historyMessages?.length && messages.length === 0) {
      setMessages(historyMessages.map((m) => ({ role: m.role, content: m.content })));
    }
  }, [historyMessages]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, sending]);

  const sendPrompt = async (rawMessage) => {
    if (!rawMessage.trim() || sending) return;
    const userMessage = rawMessage.trim();
    const context = buildAgentContext({
      params,
      search: location.search,
      pathname: location.pathname,
      storage: {
        getItem: (key) => dashboardContext[key] || localStorage.getItem(key),
      },
    });
    const token = localStorage.getItem("authentication") || "";
    const baseURL = getEndpoint() || "";
    const memoryCandidate = extractMemoryCandidate(userMessage);
    window.dispatchEvent(new CustomEvent("demo-assistant-question-sent"));

    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    if (memoryCandidate) {
      if (!context.farm_id) {
        setToast({ open: true, variant: "warning", text: "Select a farm before saving memory" });
        return;
      }
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Should I remember this for future recommendations?\n\n${memoryCandidate.content}`,
          memoryCandidate: {
            ...memoryCandidate,
            farm_id: context.farm_id,
            pond_id: context.pond_id,
            cycle_id: context.cycle_id,
          },
        },
      ]);
      return;
    }
    setMessages((prev) => [...prev, { role: "assistant", content: "", streaming: true }]);
    setSending(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch(`${baseURL}/agent/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId || "",
          farm_id: context.farm_id,
          pond_id: context.pond_id,
          cycle_id: context.cycle_id,
          page_context: context.page_context,
        }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (!controller.signal.aborted) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();
        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(part.slice(6));
            if (event.type === "tool_start") {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last?.role === "assistant") next[next.length - 1] = { ...last, toolStatus: event.name };
                return next;
              });
            } else if (event.type === "tool_done") {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last?.role === "assistant") next[next.length - 1] = { ...last, toolStatus: null };
                return next;
              });
            } else if (event.type === "text") {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last?.role === "assistant") {
                  next[next.length - 1] = { ...last, content: last.content + event.delta, toolStatus: null };
                }
                return next;
              });
            } else if (event.type === "done") {
              if (event.session_id) {
                localStorage.setItem(SESSION_KEY, event.session_id);
                setSessionId(event.session_id);
              }
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last?.role === "assistant") next[next.length - 1] = { ...last, streaming: false, toolStatus: null };
                return next;
              });
            } else if (event.type === "error") {
              setToast({ open: true, variant: "error", text: event.message || "Stream error" });
            }
          } catch {
            // ignore malformed SSE lines
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setToast({ open: true, variant: "error", text: "Failed to send message" });
        setMessages((prev) => prev.slice(0, -1));
      }
    } finally {
      setSending(false);
      abortRef.current = null;
    }
  };

  useEffect(() => {
    if (open && initialMessage) {
      sendPrompt(initialMessage);
      if (onInitialMessageConsumed) onInitialMessageConsumed();
    }
  }, [open]);

  const handleExplainForTeam = async () => {
    const farmId = dashboardContext.farm_id;
    const cycleId = dashboardContext.cycle_id;
    const pondId = dashboardContext.pond_id;
    if (!farmId) {
      setToast({ open: true, variant: "warning", text: "No active farm selected" });
      return;
    }
    try {
      const result = await explainForTeam({ farm_id: farmId, cycle_id: cycleId, pond_id: pondId });
      setMessages((prev) => [
        ...prev,
        { role: "user", content: "Jelaskan kondisi tambak ini untuk tim pekerja (Bahasa Indonesia)" },
        { role: "assistant", content: result?.explanation || "" },
      ]);
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to generate team explanation" });
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = input;
    setInput("");
    await sendPrompt(userMessage);
  };

  const handleNewChat = async () => {
    if (sessionId) {
      try {
        await deleteSession(sessionId);
      } catch {
        // ignore
      }
      localStorage.removeItem(SESSION_KEY);
      setSessionId("");
    }
    setMessages([]);
  };

  const handleDismissAlert = async (alertId) => {
    try {
      await dismissAlert(alertId);
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to dismiss alert" });
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await resolveAlert(alertId);
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to resolve alert" });
    }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      await completeTask(taskId);
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to complete task" });
    }
  };

  const handleMemoryDecision = async (messageIndex, shouldSave) => {
    const candidate = messages[messageIndex]?.memoryCandidate;
    if (!candidate) return;
    if (!shouldSave) {
      setMessages((prev) => prev.map((msg, i) => (
        i === messageIndex ? { ...msg, memoryCandidate: null, content: "Okay, I will not save that memory." } : msg
      )));
      return;
    }
    try {
      await createMemory({
        farm_id: candidate.farm_id,
        pond_id: candidate.pond_id,
        cycle_id: candidate.cycle_id,
        memory_type: candidate.memory_type,
        content: candidate.content.trim(),
        tags: candidate.tags,
        confidence: 0.9,
      });
      setMessages((prev) => prev.map((msg, i) => (
        i === messageIndex ? { ...msg, memoryCandidate: null, content: `Remembered: ${candidate.content}` } : msg
      )));
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to save memory" });
    }
  };

  const handleMemoryCandidateChange = (messageIndex, content) => {
    setMessages((prev) => prev.map((msg, i) => (
      i === messageIndex && msg.memoryCandidate
        ? {
          ...msg,
          content: `Should I remember this for future recommendations?\n\n${content}`,
          memoryCandidate: { ...msg.memoryCandidate, content },
        }
        : msg
    )));
  };

  const formatDue = (dueAt) => {
    if (!dueAt) return null;
    const diffMs = new Date(dueAt) - new Date();
    const hours = Math.round(diffMs / 3600000);
    if (hours < 0) return "Overdue";
    if (hours < 24) return `Due in ${hours}h`;
    return `Due in ${Math.round(hours / 24)}d`;
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{ style: { width: 420, display: "flex", flexDirection: "column" } }}
    >
      <Box
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid #e0e0e0",
        }}
      >
        <Typography variant="h6" style={{ fontWeight: 600 }}>
          AI Assistant
        </Typography>
        <Box style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Button size="small" variant="outlined" onClick={handleNewChat}>
            New Chat
          </Button>
          <IconButton
            size="small"
            onClick={handleExplainForTeam}
            disabled={explaining}
            title="Jelaskan ke Tim (Bahasa Indonesia)"
            aria-label="Explain farm status to the team in Bahasa Indonesia"
            style={{ color: "#474DA4" }}
          >
            {explaining ? <CircularProgress size={14} /> : <MdGroups size={18} />}
          </IconButton>
          <IconButton size="small" onClick={onClose} aria-label="Close assistant">
            <MdClose />
          </IconButton>
        </Box>
      </Box>

      {alerts.length > 0 && (
        <Box style={{ padding: "8px 16px", borderBottom: "1px solid #e0e0e0" }}>
          <Accordion disableGutters elevation={0}>
            <AccordionSummary expandIcon={<MdExpandMore />} style={{ padding: 0, minHeight: 40 }}>
              <Typography variant="body2" style={{ fontWeight: 500 }}>
                Active Alerts{" "}
                <Chip
                  label={alerts.length}
                  size="small"
                  color="error"
                  style={{ marginLeft: 4, height: 18, fontSize: 11 }}
                />
              </Typography>
            </AccordionSummary>
            <AccordionDetails style={{ padding: "0 0 8px 0" }}>
              {alerts.map((alert) => (
                <Box
                  key={alert.id}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 6,
                    marginBottom: 6,
                    padding: "4px 0",
                  }}
                >
                  <Chip
                    label={alert.severity}
                    size="small"
                    color={severityColor(alert.severity)}
                    style={{ flexShrink: 0 }}
                  />
                  <Typography variant="body2" style={{ flex: 1, fontSize: 12 }}>
                    {alert.message}
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={() => handleResolveAlert(alert.id)}
                    style={{ padding: 2, flexShrink: 0, color: "#4caf50" }}
                    title="Mark resolved"
                    aria-label={`Resolve alert: ${alert.message}`}
                  >
                    <MdDone size={14} />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDismissAlert(alert.id)}
                    style={{ padding: 2, flexShrink: 0 }}
                    title="Dismiss"
                    aria-label={`Dismiss alert: ${alert.message}`}
                  >
                    <MdDeleteOutline size={14} />
                  </IconButton>
                </Box>
              ))}
            </AccordionDetails>
          </Accordion>
        </Box>
      )}

      {tasks.length > 0 && (
        <Box style={{ padding: "8px 16px", borderBottom: "1px solid #e0e0e0" }}>
          <Accordion disableGutters elevation={0}>
            <AccordionSummary expandIcon={<MdExpandMore />} style={{ padding: 0, minHeight: 40 }}>
              <Typography variant="body2" style={{ fontWeight: 500 }}>
                Pending Tasks{" "}
                <Chip
                  label={tasks.length}
                  size="small"
                  color="warning"
                  style={{ marginLeft: 4, height: 18, fontSize: 11 }}
                />
              </Typography>
            </AccordionSummary>
            <AccordionDetails style={{ padding: "0 0 8px 0" }}>
              {tasks.map((task) => (
                <Box
                  key={task.id}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 6,
                    marginBottom: 6,
                    padding: "4px 0",
                  }}
                >
                  <MdAlarm size={14} style={{ flexShrink: 0, marginTop: 3, color: "#ff9800" }} />
                  <Box style={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" style={{ fontSize: 12, fontWeight: 500 }}>
                      {task.title}
                    </Typography>
                    {task.due_at && (
                      <Typography variant="caption" style={{ color: formatDue(task.due_at) === "Overdue" ? "#f44336" : "#888" }}>
                        {formatDue(task.due_at)}
                      </Typography>
                    )}
                  </Box>
                  <IconButton
                    size="small"
                    onClick={() => handleCompleteTask(task.id)}
                    style={{ padding: 2, flexShrink: 0, color: "#4caf50" }}
                    title="Mark done"
                    aria-label={`Complete task: ${task.title}`}
                  >
                    <MdDone size={14} />
                  </IconButton>
                </Box>
              ))}
            </AccordionDetails>
          </Accordion>
        </Box>
      )}

      <Box
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        {messages.length === 0 && (
          <Box style={{ display: "flex", flexDirection: "column", alignItems: "center", marginTop: 32, gap: 16 }}>
            <Typography variant="body2" color="textSecondary" style={{ textAlign: "center" }}>
              Ask me anything about your farm — water quality, feeding, harvest timing, costs.
            </Typography>
            <Box style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
              {[
                "Why is DO low?",
                "Should I harvest soon?",
                "What changed this week?",
                "What's my cost/kg?",
              ].map((prompt) => (
                <Chip
                  key={prompt}
                  label={prompt}
                  variant="outlined"
                  size="small"
                  onClick={() => sendPrompt(prompt)}
                  style={{ cursor: "pointer" }}
                />
              ))}
            </Box>
            <Chip
              icon={<MdGroups size={14} />}
              label="Jelaskan ke Tim"
              variant="outlined"
              size="small"
              onClick={handleExplainForTeam}
              disabled={explaining}
              style={{ cursor: "pointer", borderColor: "#474DA4", color: "#474DA4" }}
            />
          </Box>
        )}
        {messages.map((msg, i) => (
          <Box
            key={i}
            style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
            }}
          >
            <Box
              style={{
                maxWidth: "85%",
                padding: "8px 12px",
                borderRadius: 12,
                backgroundColor: msg.role === "user" ? "#474DA4" : "#f5f5f5",
                color: msg.role === "user" ? "#fff" : "inherit",
              }}
            >
              {msg.role === "assistant" ? (
                <Box style={{ fontSize: 13, lineHeight: 1.6 }}>
                  {msg.toolStatus && (
                    <Box style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6, color: "#888" }}>
                      <CircularProgress size={10} />
                      <Typography variant="caption" style={{ fontSize: 11 }}>
                        Checking: {msg.toolStatus}…
                      </Typography>
                    </Box>
                  )}
                  {msg.content ? (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p style={{ margin: "0 0 6px 0" }}>{children}</p>,
                        ul: ({ children }) => <ul style={{ margin: "4px 0", paddingLeft: 18 }}>{children}</ul>,
                        ol: ({ children }) => <ol style={{ margin: "4px 0", paddingLeft: 18 }}>{children}</ol>,
                        li: ({ children }) => <li style={{ marginBottom: 2 }}>{children}</li>,
                        strong: ({ children }) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
                        code: ({ children }) => (
                          <code style={{ backgroundColor: "#e0e0e0", padding: "1px 4px", borderRadius: 3, fontSize: 12 }}>
                            {children}
                          </code>
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : !msg.toolStatus ? (
                    <span style={{ color: "#aaa", fontSize: 12 }}>▋</span>
                  ) : null}
                  {msg.streaming && msg.content && (
                    <span style={{ color: "#474DA4", fontWeight: "bold", fontSize: 14 }}>▋</span>
                  )}
                  {msg.memoryCandidate && (
                    <Box style={{ marginTop: 8 }}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Edit memory before saving"
                        multiline
                        minRows={2}
                        value={msg.memoryCandidate.content}
                        onChange={(event) => handleMemoryCandidateChange(i, event.target.value)}
                      />
                      <Box style={{ display: "flex", gap: 8, marginTop: 8 }}>
                        <Button
                          size="small"
                          variant="contained"
                          onClick={() => handleMemoryDecision(i, true)}
                          disabled={savingMemory || !msg.memoryCandidate.content.trim()}
                        >
                          Remember
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleMemoryDecision(i, false)}
                          disabled={savingMemory}
                        >
                          Not now
                        </Button>
                      </Box>
                    </Box>
                  )}
                </Box>
              ) : (
                <Typography variant="body2">{msg.content}</Typography>
              )}
            </Box>
          </Box>
        ))}
        {/* Streaming state is shown inline in the assistant message bubble */}
        <div ref={messagesEndRef} />
      </Box>

      <Divider />
      <Box style={{ padding: "12px 16px", display: "flex", gap: 8 }}>
        <TextField
          fullWidth
          size="small"
          multiline
          maxRows={3}
          placeholder="Ask about your farm…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sending}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          disabled={sending || !input.trim()}
          style={{ alignSelf: "flex-end" }}
          aria-label="Send message"
        >
          <MdSend />
        </IconButton>
      </Box>
    </Drawer>
  );
};

export default AgentChat;
