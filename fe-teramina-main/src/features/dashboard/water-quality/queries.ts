import { useQuery } from "@tanstack/react-query";
import { axios } from "helper/axios";

type WQParams = {
  cycles: string;
  start_date: string;
  end_date: string;
  variables: string;
};

export const wqKeys = {
  data: (p: WQParams) => ["water-quality", p] as const,
};

export const useWaterQualityDashboard = (params: WQParams | null) =>
  useQuery({
    queryKey: wqKeys.data(params ?? ({} as WQParams)),
    queryFn: () =>
      axios
        .get(`/water_quality/get-water-quality-dashboard?${new URLSearchParams(params!).toString()}`)
        .then((r: any) => r.payload as Record<string, unknown>),
    enabled: !!params?.cycles,
  });
