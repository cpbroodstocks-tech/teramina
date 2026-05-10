import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { axios } from "helper/axios";

export const cycleDataKeys = {
  list: (params: Record<string, string>) => ["cycle-data", params] as const,
};

export const useInvalidateCycleDataList = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["cycle-data"] });
};

export const useCycleDataList = () => {
  const params = useParams() as Record<string, string>;
  const queryString = new URLSearchParams(params).toString();
  return useQuery({
    queryKey: cycleDataKeys.list(params),
    queryFn: () =>
      axios.get(`/cycle-data/list-cycle-data?${queryString}`).then((r: any) => r.payload),
  });
};

export const useQualityReport = (cycle_id: string) =>
  useQuery({
    queryKey: ["quality-report", cycle_id],
    queryFn: () =>
      axios
        .get("/cycle-data/quality-report", { params: { cycle_id } })
        .then((r: any) => r?.payload ?? null)
        .catch(() => null),
    enabled: !!cycle_id,
    staleTime: 5 * 60 * 1000,  // 5 min — not real-time
  });
