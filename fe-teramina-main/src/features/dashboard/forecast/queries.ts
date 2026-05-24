import { useQuery } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const useConfidenceBands = (cycle_id: string | null) =>
  useQuery({
    queryKey: ["confidence-bands", cycle_id],
    queryFn: () =>
      axios.get("/dashboard/confidence-bands", { params: { cycle_id } }).then((r: any) => r?.payload || null),
    enabled: !!cycle_id,
  });

export const useProphetForecast = (cycle_id: string | null) =>
  useQuery({
    queryKey: ["prophet-forecast", cycle_id],
    queryFn: () =>
      axios.get("/dashboard/prophet-forecast", { params: { cycle_id } }).then((r: any) => r?.payload || null),
    enabled: !!cycle_id,
  });
