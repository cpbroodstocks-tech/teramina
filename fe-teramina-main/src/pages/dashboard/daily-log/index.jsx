import { useState, useRef } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  IconButton,
  TextField,
  Typography,
} from "@mui/material";
import { MdMic, MdStop, MdSave } from "react-icons/md";
import { useToastStore } from "store/toast.store";
import { useCreateVoiceNote, useGetFarmerNotes } from "components/agent-chat/queries";
import { axios } from "helper/axios";
import { useMutation, useQueryClient } from "@tanstack/react-query";

// Queue a text-note write to IndexedDB when offline; flush via Background Sync
async function queueOfflineNote(content, farm_id, pond_id, cycle_id) {
  const db = await new Promise((resolve, reject) => {
    const req = indexedDB.open("teramina-offline", 1);
    req.onupgradeneeded = (e) =>
      e.target.result.createObjectStore("pending-notes", { keyPath: "id", autoIncrement: true });
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = (e) => reject(e.target.error);
  });
  await new Promise((resolve, reject) => {
    const tx = db.transaction("pending-notes", "readwrite");
    const baseURL = import.meta.env.VITE_ENDPOINT || "";
    const token = localStorage.getItem("authentication") || "";
    const fd = new FormData();
    fd.append("content", content);
    fd.append("farm_id", farm_id);
    fd.append("pond_id", pond_id);
    fd.append("cycle_id", cycle_id);
    tx.objectStore("pending-notes").add({
      url: `${baseURL}/agent/text-note`,
      headers: { Authorization: `Bearer ${token}` },
      body: content,
      farm_id,
      pond_id,
      cycle_id,
    });
    tx.oncomplete = () => resolve();
    tx.onerror = (e) => reject(e.target.error);
  });
  if ("serviceWorker" in navigator && "SyncManager" in window) {
    const reg = await navigator.serviceWorker.ready;
    await reg.sync.register("daily-log-sync").catch(() => {});
  }
}

const useCreateTextNote = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (fd) => {
      if (!navigator.onLine) {
        const content = fd.get("content");
        await queueOfflineNote(content, fd.get("farm_id"), fd.get("pond_id"), fd.get("cycle_id"));
        return { offline: true };
      }
      return axios.post("/agent/text-note", fd, { headers: { "Content-Type": "multipart/form-data" } });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["farmer-notes"] }),
  });
};

const farmId = () => localStorage.getItem("farm_id") || "";
const pondId = () => localStorage.getItem("pond_id") || "";
const cycleId = () => localStorage.getItem("cycle_id") || "";

const DailyLog = () => {
  const { setToast } = useToastStore();
  const [textNote, setTextNote] = useState("");
  const [recording, setRecording] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // track connectivity changes
  useState(() => {
    const up = () => setIsOnline(true);
    const down = () => setIsOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => { window.removeEventListener("online", up); window.removeEventListener("offline", down); };
  });
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const { data: notes = [], isLoading } = useGetFarmerNotes(farmId(), true);
  const { mutateAsync: createVoiceNote, isPending: transcribing } = useCreateVoiceNote();
  const { mutateAsync: createTextNote, isPending: savingText } = useCreateTextNote();

  const handleSaveText = async () => {
    if (!textNote.trim()) return;
    const fd = new FormData();
    fd.append("content", textNote.trim());
    fd.append("farm_id", farmId());
    fd.append("pond_id", pondId());
    fd.append("cycle_id", cycleId());
    try {
      const result = await createTextNote(fd);
      setTextNote("");
      if (result?.offline) {
        setToast({ open: true, variant: "info", text: "Offline — note queued, will sync when connected" });
      } else {
        setToast({ open: true, variant: "success", text: "Note saved" });
      }
    } catch {
      setToast({ open: true, variant: "error", text: "Failed to save note" });
    }
  };

  const handleVoiceRecord = async () => {
    if (recording) {
      mediaRecorderRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;
      audioChunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const fd = new FormData();
        fd.append("audio", blob, "note.webm");
        fd.append("farm_id", farmId());
        fd.append("pond_id", pondId());
        fd.append("cycle_id", cycleId());
        try {
          await createVoiceNote(fd);
          setToast({ open: true, variant: "success", text: "Voice note saved" });
        } catch {
          setToast({ open: true, variant: "error", text: "Transcription failed" });
        }
      };
      mr.start();
      setRecording(true);
    } catch {
      setToast({ open: true, variant: "error", text: "Microphone access denied" });
    }
  };

  const formatTime = (iso) => {
    if (!iso) return "";
    return new Date(iso).toLocaleString("id-ID", { dateStyle: "short", timeStyle: "short" });
  };

  return (
    <Box style={{ padding: 24, maxWidth: 720, margin: "0 auto" }}>
      <Box style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <Typography variant="h5" style={{ fontWeight: 600 }}>
          Daily Farm Log
        </Typography>
        {!isOnline && (
          <Chip label="Offline — notes will sync when connected" color="warning" size="small" />
        )}
      </Box>

      <Card variant="outlined" style={{ marginBottom: 24 }}>
        <CardContent>
          <Typography variant="subtitle2" style={{ marginBottom: 12 }}>
            Record a Note
          </Typography>
          <Box style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
            <TextField
              fullWidth
              multiline
              minRows={2}
              maxRows={5}
              size="small"
              placeholder="Describe what you observed today — water color, feed leftover, shrimp behavior…"
              value={textNote}
              onChange={(e) => setTextNote(e.target.value)}
              disabled={savingText}
            />
            <Box style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <Button
                variant="contained"
                size="small"
                startIcon={savingText ? <CircularProgress size={14} /> : <MdSave />}
                onClick={handleSaveText}
                disabled={!textNote.trim() || savingText}
                style={{ whiteSpace: "nowrap" }}
              >
                Save
              </Button>
              <IconButton
                size="small"
                onClick={handleVoiceRecord}
                disabled={transcribing}
                style={{ color: recording ? "#f44336" : "#757575" }}
                title={recording ? "Stop recording" : "Record voice note"}
              >
                {transcribing ? (
                  <CircularProgress size={18} />
                ) : recording ? (
                  <MdStop size={22} />
                ) : (
                  <MdMic size={22} />
                )}
              </IconButton>
            </Box>
          </Box>
          {recording && (
            <Typography variant="caption" style={{ color: "#f44336", display: "block", marginTop: 8 }}>
              Recording… tap Stop when done.
            </Typography>
          )}
          {transcribing && (
            <Typography variant="caption" style={{ color: "#757575", display: "block", marginTop: 8 }}>
              Transcribing audio…
            </Typography>
          )}
        </CardContent>
      </Card>

      <Typography variant="subtitle2" style={{ marginBottom: 12, fontWeight: 500 }}>
        Recent Notes
      </Typography>

      {isLoading && <CircularProgress size={24} />}

      {!isLoading && notes.length === 0 && (
        <Typography variant="body2" color="textSecondary">
          No notes yet. Start recording observations above.
        </Typography>
      )}

      {notes.map((note) => (
        <Card key={note.id} variant="outlined" style={{ marginBottom: 12 }}>
          <CardContent style={{ paddingBottom: 12 }}>
            <Box style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <Chip
                label={note.source === "voice" ? "Voice" : "Text"}
                size="small"
                color={note.source === "voice" ? "primary" : "default"}
                variant="outlined"
              />
              {note.saved_to_memory && (
                <Chip label="In Memory" size="small" color="success" variant="outlined" />
              )}
              <Typography variant="caption" style={{ marginLeft: "auto", color: "#888" }}>
                {formatTime(note.created_at)}
              </Typography>
            </Box>
            <Typography variant="body2" style={{ whiteSpace: "pre-wrap" }}>
              {note.content}
            </Typography>
            {note.tags?.length > 0 && (
              <Box style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap" }}>
                {note.tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" />
                ))}
              </Box>
            )}
          </CardContent>
          <Divider />
        </Card>
      ))}
    </Box>
  );
};

export default DailyLog;
