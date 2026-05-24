import { useQuery } from "@tanstack/react-query";
import { axios } from "helper/axios";

type FeedingParams = {
  farm_id: string;
  pond_id: string;
  cycle_id: string;
  filter_type: string;
  date: string;
};

export const feedingKeys = {
  data: (p: FeedingParams) => ["feeding", p] as const,
};

export const useFeedingDashboard = (params: FeedingParams | null) =>
  useQuery({
    queryKey: feedingKeys.data(params ?? ({} as FeedingParams)),
    queryFn: () =>
      axios
        .get(`/dashboard/feeding?${new URLSearchParams(params!).toString()}`)
        .then((r: any) => r.payload as Record<string, unknown>),
    enabled: !!params?.cycle_id && !!params?.date,
  });
