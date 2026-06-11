import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";
import { trackDemoEvent } from "./analytics";

export const demoExperienceKey = ["demo-experience"] as const;

export const useDemoExperience = () =>
  useQuery({
    queryKey: demoExperienceKey,
    queryFn: () => axios.get("/user/demo-experience").then((response: any) => response?.payload),
  });

export const useTrackDemoEvent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ eventName, properties = {} }: { eventName: string; properties?: Record<string, string> }) =>
      trackDemoEvent(eventName, properties),
    onSuccess: (data) => queryClient.setQueryData(demoExperienceKey, data),
  });
};

export const useUpdateDemoExperience = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (checklist_dismissed: boolean) =>
      axios.patch("/user/demo-experience", { checklist_dismissed }).then((response: any) => response?.payload),
    onSuccess: (data) => queryClient.setQueryData(demoExperienceKey, data),
  });
};

export const useResetDemoExperience = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => axios.post("/user/demo-experience/reset", { confirmed: true }).then((response: any) => response?.payload),
    onSuccess: (data) => {
      queryClient.setQueryData(demoExperienceKey, data);
      queryClient.invalidateQueries({ queryKey: ["farm-hierarchy"] });
      queryClient.invalidateQueries({ queryKey: ["agent"] });
    },
  });
};
