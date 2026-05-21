import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";
import type { AgentAlert, AgentMemory, AgentMemoryGraph, AgentMessage, AgentPageContext, AgentTask, ChatPayload } from "components/agent-chat/types";

export const useAgentAlerts = (enabled: boolean) =>
  useQuery<AgentAlert[]>({
    queryKey: ["agent-alerts"],
    queryFn: () => axios.get("/agent/alerts").then((r: any) => r?.payload?.alerts ?? []),
    enabled,
  });

export const useInvalidateAgentAlerts = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["agent-alerts"] });
};

export const useGetAgentHistory = (session_id: string | null) =>
  useQuery<AgentMessage[]>({
    queryKey: ["agent-history", session_id],
    queryFn: () =>
      axios.get(`/agent/history?session_id=${session_id}`).then((r: any) => r?.payload?.messages ?? []),
    enabled: !!session_id,
  });

export const useSendAgentMessage = () =>
  useMutation<ChatPayload, Error, {
    message: string;
    session_id: string;
    farm_id?: string;
    pond_id?: string;
    cycle_id?: string;
    page_context?: AgentPageContext;
  }>({
    mutationFn: ({ message, session_id, farm_id, pond_id, cycle_id, page_context }) =>
      axios.post("/agent/chat", { message, session_id, farm_id, pond_id, cycle_id, page_context }).then((r: any) => r?.payload),
  });

export const useDeleteAgentSession = () =>
  useMutation<void, Error, string>({
    mutationFn: (session_id) => axios.delete(`/agent/session?session_id=${session_id}`),
  });

export const useDismissAlert = () => {
  const invalidate = useInvalidateAgentAlerts();
  return useMutation<void, Error, string>({
    mutationFn: (alertId) => axios.delete(`/agent/alerts/${alertId}`),
    onSuccess: () => invalidate(),
  });
};

export const useResolveAlert = () => {
  const invalidate = useInvalidateAgentAlerts();
  return useMutation<void, Error, string>({
    mutationFn: (alertId) => axios.patch(`/agent/alerts/${alertId}/resolve`),
    onSuccess: () => invalidate(),
  });
};

export const useGetAgentTasks = (enabled: boolean) =>
  useQuery<AgentTask[]>({
    queryKey: ["agent-tasks"],
    queryFn: () => axios.get("/agent/tasks").then((r: any) => r?.payload?.tasks ?? []),
    enabled,
  });

export const useInvalidateAgentTasks = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["agent-tasks"] });
};

export const useCompleteAgentTask = () => {
  const invalidate = useInvalidateAgentTasks();
  return useMutation<void, Error, string>({
    mutationFn: (taskId) => axios.patch(`/agent/tasks/${taskId}/complete`),
    onSuccess: () => invalidate(),
  });
};

export const useAgentMemories = ({
  enabled,
  farm_id,
  pond_id,
}: {
  enabled: boolean;
  farm_id?: string;
  pond_id?: string;
}) =>
  useQuery<AgentMemory[]>({
    queryKey: ["agent-memories", farm_id || "", pond_id || ""],
    queryFn: () =>
      axios
        .get("/agent/memories", { params: { farm_id, pond_id } })
        .then((r: any) => r?.payload?.memories ?? []),
    enabled,
  });

export const useAgentMemoryGraph = ({
  enabled,
  farm_id,
  pond_id,
}: {
  enabled: boolean;
  farm_id?: string;
  pond_id?: string;
}) =>
  useQuery<AgentMemoryGraph>({
    queryKey: ["agent-memory-graph", farm_id || "", pond_id || ""],
    queryFn: () =>
      axios
        .get("/agent/memories/graph", { params: { farm_id, pond_id } })
        .then((r: any) => r?.payload ?? { entities: [], relations: [], observations: [] }),
    enabled,
  });

export const useInvalidateAgentMemories = () => {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["agent-memories"] });
    queryClient.invalidateQueries({ queryKey: ["agent-memory-graph"] });
  };
};

export const useDeleteAgentMemory = () => {
  const invalidate = useInvalidateAgentMemories();
  return useMutation<void, Error, string>({
    mutationFn: (memoryId) => axios.delete(`/agent/memories/${memoryId}`),
    onSuccess: () => invalidate(),
  });
};

export const useVerifyAgentMemory = () => {
  const invalidate = useInvalidateAgentMemories();
  return useMutation<void, Error, string>({
    mutationFn: (memoryId) => axios.patch(`/agent/memories/${memoryId}/verify`),
    onSuccess: () => invalidate(),
  });
};

export const useUpdateAgentMemory = () => {
  const invalidate = useInvalidateAgentMemories();
  return useMutation<void, Error, {
    memoryId: string;
    memory_type?: AgentMemory["memory_type"];
    content?: string;
    tags?: string[];
    confidence?: number;
  }>({
    mutationFn: ({ memoryId, ...payload }) => axios.patch(`/agent/memories/${memoryId}`, payload),
    onSuccess: () => invalidate(),
  });
};

export const useCreateAgentMemory = () => {
  const invalidate = useInvalidateAgentMemories();
  return useMutation<void, Error, {
    farm_id: string;
    pond_id?: string;
    cycle_id?: string;
    memory_type: AgentMemory["memory_type"];
    content: string;
    tags?: string[];
    confidence?: number;
  }>({
    mutationFn: (payload) => axios.post("/agent/memories", payload),
    onSuccess: () => invalidate(),
  });
};

export const useExplainForTeam = () =>
  useMutation<{ explanation: string; farm_id: string; cycle_id: string }, Error, {
    farm_id: string;
    cycle_id?: string;
    pond_id?: string;
  }>({
    mutationFn: (data) =>
      axios.post("/agent/explain", data).then((r: any) => r?.payload),
  });

export const useGetTodaySummary = (farm_id: string | null) =>
  useQuery({
    queryKey: ["agent-today", farm_id],
    queryFn: () =>
      axios.get("/agent/today", { params: { farm_id } }).then((r: any) => r?.payload),
    enabled: !!farm_id,
    refetchInterval: 5 * 60 * 1000, // refresh every 5 minutes
  });

export const useGetPondTimeline = (cycle_id: string | null, limit = 50) =>
  useQuery({
    queryKey: ["agent-pond-timeline", cycle_id],
    queryFn: () =>
      axios.get("/agent/pond-timeline", { params: { cycle_id, limit } }).then((r: any) => r?.payload),
    enabled: !!cycle_id,
  });

export const createAgentSummary = (question: string, model?: string) =>
  axios.post("/agent/summary", { question, model }).then((r: any) => r?.payload);

export const getAgentSummaryStatus = (taskId: string) =>
  axios.get(`/agent/summary/${taskId}`).then((r: any) => r?.payload);
