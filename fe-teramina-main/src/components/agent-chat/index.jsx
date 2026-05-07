import { useState, useEffect, useRef } from "react";
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
import { MdExpandMore, MdClose, MdSend, MdDeleteOutline } from "react-icons/md";
import ReactMarkdown from "react-markdown";
import { useToastStore } from "store/toast.store";
import {
  useAgentAlerts,
  useSendAgentMessage,
  useDeleteAgentSession,
  useDismissAlert,
} from "components/agent-chat/queries";

const SESSION_KEY = "agent_session_id";

const severityColor = (severity) => {
  if (severity === "high") return "error";
  if (severity === "medium") return "warning";
  return "default";
};

const AgentChat = ({ open, onClose, onAlertsLoaded }) => {
  const { setToast } = useToastStore();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const { data: alerts = [] } = useAgentAlerts(open);
  const { mutateAsync: sendMessage, isPending: sending } = useSendAgentMessage();
  const { mutateAsync: deleteSession } = useDeleteAgentSession();
  const { mutateAsync: dismissAlert } = useDismissAlert();

  useEffect(() => {
    if (onAlertsLoaded) onAlertsLoaded(alerts.length);
  }, [alerts.length]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, sending]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const sessionId = localStorage.getItem(SESSION_KEY) || "";
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    try {
      const payload = await sendMessage({ message: userMessage, session_id: sessionId });
      const { response, session_id } = payload || {};
      if (session_id) localStorage.setItem(SESSION_KEY, session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: response || "" }]);
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to send message" });
    }
  };

  const handleNewChat = async () => {
    const sessionId = localStorage.getItem(SESSION_KEY);
    if (sessionId) {
      try {
        await deleteSession(sessionId);
      } catch {
        // ignore
      }
      localStorage.removeItem(SESSION_KEY);
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
        <Box style={{ display: "flex", gap: 8 }}>
          <Button size="small" variant="outlined" onClick={handleNewChat}>
            New Chat
          </Button>
          <IconButton size="small" onClick={onClose}>
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
                    onClick={() => handleDismissAlert(alert.id)}
                    style={{ padding: 2, flexShrink: 0 }}
                  >
                    <MdDeleteOutline size={14} />
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
          <Typography
            variant="body2"
            color="textSecondary"
            style={{ textAlign: "center", marginTop: 32 }}
          >
            Ask me anything about your farm — water quality, feeding, harvest timing, costs.
          </Typography>
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
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => (
                        <p style={{ margin: "0 0 6px 0" }}>{children}</p>
                      ),
                      ul: ({ children }) => (
                        <ul style={{ margin: "4px 0", paddingLeft: 18 }}>{children}</ul>
                      ),
                      ol: ({ children }) => (
                        <ol style={{ margin: "4px 0", paddingLeft: 18 }}>{children}</ol>
                      ),
                      li: ({ children }) => (
                        <li style={{ marginBottom: 2 }}>{children}</li>
                      ),
                      strong: ({ children }) => (
                        <strong style={{ fontWeight: 600 }}>{children}</strong>
                      ),
                      code: ({ children }) => (
                        <code
                          style={{
                            backgroundColor: "#e0e0e0",
                            padding: "1px 4px",
                            borderRadius: 3,
                            fontSize: 12,
                          }}
                        >
                          {children}
                        </code>
                      ),
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </Box>
              ) : (
                <Typography variant="body2">{msg.content}</Typography>
              )}
            </Box>
          </Box>
        ))}
        {sending && (
          <Box style={{ display: "flex", justifyContent: "flex-start" }}>
            <Box
              style={{
                padding: "10px 14px",
                borderRadius: 12,
                backgroundColor: "#f5f5f5",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <CircularProgress size={12} />
              <Typography variant="body2" color="textSecondary" style={{ fontSize: 12 }}>
                Thinking…
              </Typography>
            </Box>
          </Box>
        )}
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
        >
          <MdSend />
        </IconButton>
      </Box>
    </Drawer>
  );
};

export default AgentChat;
