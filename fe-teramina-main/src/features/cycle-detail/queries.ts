import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";

// ─── Benchmark ──────────────────────────────────────────────────────────────

export const benchmarkKeys = {
  performance: (cycle_id: string) => ["benchmark", cycle_id] as const,
};

export const useBenchmarkPerformance = (cycle_id: string) =>
  useQuery({
    queryKey: benchmarkKeys.performance(cycle_id),
    queryFn: () =>
      axios.get("/benchmark/my-performance", { params: { cycle_id } }).then((r: any) => r?.payload ?? null),
    enabled: !!cycle_id,
  });

export const useOptInBenchmark = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => axios.post("/benchmark/opt-in", { cycle_id }).then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: benchmarkKeys.performance(cycle_id) }),
  });
};

export const useOptOutBenchmark = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => axios.post("/benchmark/opt-out", { cycle_id }).then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: benchmarkKeys.performance(cycle_id) }),
  });
};

// ─── Google Sheets ──────────────────────────────────────────────────────────

export const sheetsKeys = {
  status: (cycle_id: string) => ["sheets-status", cycle_id] as const,
  syncLog: (cycle_id: string) => ["sheets-sync-log", cycle_id] as const,
};

export const useGoogleSheetsStatus = (cycle_id: string) =>
  useQuery({
    queryKey: sheetsKeys.status(cycle_id),
    queryFn: () =>
      axios
        .get("/sheets/status", { params: { cycle_id } })
        .then((r: any) => r?.payload ?? { is_active: false })
        .catch(() => ({ is_active: false })),
    enabled: !!cycle_id,
    refetchInterval: (query) =>
      (query.state.data as any)?.last_status === "syncing" ? 3000 : false,
    refetchIntervalInBackground: true,
    retry: false,
  });

export const useConnectSheets = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (spreadsheet_id: string) =>
      axios.post("/sheets/connect", { cycle_id, spreadsheet_id }).then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sheetsKeys.status(cycle_id) }),
  });
};

export const useCreateSheetsTemplate = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      axios.post("/sheets/create-template", null, { params: { cycle_id } }).then((r: any) => r?.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sheetsKeys.status(cycle_id) }),
  });
};

export const useSyncSheets = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      axios.post("/sheets/manual-sync", null, { params: { cycle_id } }).then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sheetsKeys.status(cycle_id) }),
  });
};

export const useDisconnectSheets = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      axios.delete(`/sheets/disconnect?cycle_id=${cycle_id}`).then((r: any) => r.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sheetsKeys.status(cycle_id) }),
  });
};

export const useSyncLog = (cycle_id: string) =>
  useQuery({
    queryKey: sheetsKeys.syncLog(cycle_id),
    queryFn: () =>
      axios
        .get("/sheets/sync-log", { params: { cycle_id } })
        .then((r: any) => r?.payload ?? null)
        .catch(() => null),
    enabled: !!cycle_id,
  });

export const usePreviewSync = (cycle_id: string) =>
  useMutation({
    mutationFn: () =>
      axios
        .post("/sheets/preview-sync", null, { params: { cycle_id } })
        .then((r: any) => r?.payload),
  });

export const useConfirmSync = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (preview_id: string) =>
      axios
        .post("/sheets/confirm-sync", null, { params: { preview_id } })
        .then((r: any) => r?.payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sheetsKeys.status(cycle_id) });
      queryClient.invalidateQueries({ queryKey: sheetsKeys.syncLog(cycle_id) });
    },
  });
};

// ─── Feeding Recommendation ─────────────────────────────────────────────────

export const useFeedingRecommendation = (cycle_id: string) =>
  useQuery({
    queryKey: ["feeding-recommendation", cycle_id],
    queryFn: () =>
      axios.get("/feeding/recommendation", { params: { cycle_id } }).then((r: any) => r?.payload ?? null),
    enabled: !!cycle_id,
  });

export const useOverrideFeedingRecommendation = (cycle_id: string) =>
  useMutation({
    mutationFn: ({
      doc,
      actual_kg,
      override_reason,
    }: {
      doc: number;
      actual_kg: number;
      override_reason: string;
    }) =>
      axios
        .post(
          "/feeding/recommendation/override",
          { actual_kg, override_reason },
          { params: { cycle_id, doc } }
        )
        .then((r: any) => r.payload),
  });

// ─── AI Insights ────────────────────────────────────────────────────────────

export const useGenerateInsight = () =>
  useMutation({
    mutationFn: ({ cycle_id, type }: { cycle_id: string; type: string }) =>
      axios
        .get("/summarize/insight", { params: { cycle_id, type } })
        .then((r: any) => r?.payload?.insight ?? null),
  });

export const useLoadCachedInsight = () =>
  useMutation({
    mutationFn: ({ cycle_id, type }: { cycle_id: string; type: string }) =>
      axios
        .get("/summarize/insight/cached", { params: { cycle_id, type } })
        .then((r: any) => r?.payload?.insight ?? null),
  });

// ─── Populate & Download ────────────────────────────────────────────────────

export const usePopulateCycleData = (cycle_id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, source_type }: { file: File; source_type: "csv" | "xlsx" }) => {
      const formData = new FormData();
      formData.append("file", file);
      return axios
        .post(
          `/cycle-data/populate-cycle-data?cycle_id=${cycle_id}&source_type=${source_type}`,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        )
        .then((r: any) => r.payload);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cycle-data"] }),
  });
};

export const useDownloadCycleData = (cycle_id: string) =>
  useMutation({
    mutationFn: () =>
      axios
        .get(`/cycle-data/download-cycle_data?cycle_id=${cycle_id}`, { responseType: "blob" })
        .then((r: any) => r as Blob),
  });

export const useDownloadDummyData = () =>
  useMutation({
    mutationFn: (start_date: string) =>
      axios
        .get("/dashboard/download-dummy", { params: { start_date }, responseType: "blob" })
        .then((r: any) => r as Blob),
  });
