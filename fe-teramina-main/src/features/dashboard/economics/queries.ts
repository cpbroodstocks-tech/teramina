import { useQuery } from "@tanstack/react-query";
import { axios } from "helper/axios";

type EconomicsParams = {
  farm_id: string;
  pond_id: string;
  cycle_id: string;
  filter_type: string;
  date: string;
};

export const economicsKeys = {
  data: (p: EconomicsParams) => ["economics", p] as const,
};

export const useEconomicsDashboard = (params: EconomicsParams | null) =>
  useQuery({
    queryKey: economicsKeys.data(params ?? ({} as EconomicsParams)),
    queryFn: () =>
      axios
        .get(`/dashboard/economics?${new URLSearchParams(params!).toString()}`)
        .then((r: any) => r.payload as Record<string, unknown>),
    enabled: !!params?.cycle_id,
  });
