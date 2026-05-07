import { useMutation, useQuery } from "@tanstack/react-query";
import { axios } from "helper/axios";

type OverviewReportRequest = {
  farm_id: string | null;
  pond_id: string | null;
  cycle_id: string | null;
  date: string;
  token: string | null;
};

type OverviewReportResponse = {
  task_id: string;
};

export const overviewReportKeys = {
  poll: (taskId: string | null) => ["report-poll", taskId] as const,
};

export const useCreateOverviewReport = () =>
  useMutation({
    mutationFn: ({ farm_id, pond_id, cycle_id, date, token }: OverviewReportRequest) =>
      axios
        .post(
          "/dashboard/create-report",
          { farm_id, pond_id, cycle_id, date },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        .then((response) => (response as unknown as OverviewReportResponse).task_id),
  });

export const useOverviewReportPoll = (reportTaskId: string | null) =>
  useQuery<Blob>({
    queryKey: overviewReportKeys.poll(reportTaskId),
    enabled: !!reportTaskId,
    queryFn: () => {
      const token = localStorage.getItem("authentication") || "";
      return axios.get(`/dashboard/get-report/${reportTaskId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
        validateStatus: () => true,
      }) as unknown as Promise<Blob>;
    },
    refetchInterval: (query) => {
      const data = query.state.data as Blob | undefined;
      if (!data) return 10000;
      return data.type === "application/pdf" ? false : 10000;
    },
  });
