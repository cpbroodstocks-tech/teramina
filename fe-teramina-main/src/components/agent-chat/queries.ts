import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const useAgentAlerts = (enabled: boolean) =>
  useQuery({
    queryKey: ["agent-alerts"],
    queryFn: () => axios.get("/agent/alerts").then((r: any) => r?.payload?.alerts || []),
    enabled,
  });

export const useInvalidateAgentAlerts = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["agent-alerts"] });
};

export const useSendAgentMessage = () =>
  useMutation({
    mutationFn: ({ message, session_id }: { message: string; session_id: string }) =>
      axios.post("/agent/chat", { message, session_id }).then((r: any) => r?.payload),
  });

export const useDeleteAgentSession = () =>
  useMutation({
    mutationFn: (session_id: string) =>
      axios.delete(`/agent/session?session_id=${session_id}`),
  });

export const useDismissAlert = () => {
  const invalidate = useInvalidateAgentAlerts();
  return useMutation({
    mutationFn: (alertId: string) => axios.delete(`/agent/alerts/${alertId}`),
    onSuccess: () => invalidate(),
  });
};
