import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { axios } from "helper/axios";

export const advisoryKeys = {
  packages: ["advisory-packages"] as const,
  package: (slug: string) => ["advisory-package", slug] as const,
  cases: ["advisory-cases"] as const,
  case: (caseId: string) => ["advisory-case", caseId] as const,
  history: (farmId: string, pondId: string, cycleId: string) => ["advisory-history", farmId, pondId, cycleId] as const,
  adminCases: ["advisory-admin-cases"] as const,
  adminReports: ["advisory-admin-reports"] as const,
  adminAssistantBriefLogs: ["advisory-admin-assistant-brief-logs"] as const,
  adminAssistantAnswerLogs: ["advisory-admin-assistant-answer-logs"] as const,
  adminReportWorkflowEvents: ["advisory-admin-report-workflow-events"] as const,
  adminExpertReviews: ["advisory-admin-expert-reviews"] as const,
  adminRetainerCadences: ["advisory-admin-retainer-cadences"] as const,
  adminHatcheries: ["advisory-admin-hatcheries"] as const,
  adminHatcheryRecords: ["advisory-admin-hatchery-records"] as const,
  adminInvestorScores: ["advisory-admin-investor-scores"] as const,
  adminPhaseSixBenchmarks: ["advisory-admin-phase-six-benchmarks"] as const,
  adminPhaseSixBenchmarksFiltered: (filters: Record<string, string>) => ["advisory-admin-phase-six-benchmarks", filters] as const,
  adminPhaseSixRevisions: ["advisory-admin-phase-six-revisions"] as const,
};

export const useServicePackages = () =>
  useQuery({
    queryKey: advisoryKeys.packages,
    queryFn: () => axios.get("/advisory/packages").then((r: any) => r?.payload?.packages ?? []),
    retry: false,
  });

export const useServicePackage = (slug: string) =>
  useQuery({
    queryKey: advisoryKeys.package(slug),
    queryFn: () => axios.get(`/advisory/packages/${slug}`).then((r: any) => r?.payload?.package ?? null),
    enabled: !!slug,
    retry: false,
  });

export const useCreateAdvisoryCase = () =>
  useMutation({
    mutationFn: (payload: {
      service_package_id?: string;
      case_type: string;
      farm_id?: string;
      pond_id?: string;
      cycle_id?: string;
      title: string;
      intake_data: Record<string, any>;
      uploaded_files?: any[];
    }) => axios.post("/advisory/cases", payload).then((r: any) => r?.payload?.case ?? null),
  });

export const useAdvisoryCases = () =>
  useQuery({
    queryKey: advisoryKeys.cases,
    queryFn: () => axios.get("/advisory/cases").then((r: any) => r?.payload?.cases ?? []),
  });

export const useAdvisoryCase = (caseId: string) =>
  useQuery({
    queryKey: advisoryKeys.case(caseId),
    queryFn: () => axios.get(`/advisory/cases/${caseId}`).then((r: any) => r?.payload ?? null),
    enabled: !!caseId,
  });

export const useAdvisoryHistory = ({
  farm_id,
  pond_id,
  cycle_id,
}: {
  farm_id?: string;
  pond_id?: string;
  cycle_id?: string;
}) =>
  useQuery({
    queryKey: advisoryKeys.history(farm_id || "", pond_id || "", cycle_id || ""),
    queryFn: () =>
      axios
        .get("/advisory/history", { params: { farm_id, pond_id, cycle_id } })
        .then((r: any) => r?.payload ?? { total_events: 0, events: [] }),
    enabled: !!(farm_id || pond_id || cycle_id),
  });

export const useAddAdvisoryCaseFile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, payload }: { caseId: string; payload: { name: string; url: string; content_type?: string; description?: string } }) =>
      axios.post(`/advisory/cases/${caseId}/files`, payload).then((r: any) => r?.payload?.case ?? null),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.case(variables.caseId) });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
    },
  });
};

export const useUploadAdvisoryCaseFile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, file, description }: { caseId: string; file: File; description?: string }) => {
      const formData = new FormData();
      formData.append("file", file);
      return axios
        .post(`/advisory/cases/${caseId}/files/upload`, formData, {
          params: { description: description || "" },
          headers: { "Content-Type": "multipart/form-data" },
        })
        .then((r: any) => r?.payload?.case ?? null);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.case(variables.caseId) });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
    },
  });
};

export const useAcceptBenchmarkConsent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (caseId: string) =>
      axios.post(`/advisory/cases/${caseId}/benchmark-consent`, {}).then((r: any) => r?.payload?.benchmark_consent ?? null),
    onSuccess: (_, caseId) => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.case(caseId) });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixBenchmarks });
    },
  });
};

export const useRevokeBenchmarkConsent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (caseId: string) =>
      axios.post(`/advisory/cases/${caseId}/benchmark-consent/revoke`, {}).then((r: any) => r?.payload?.benchmark_consent ?? null),
    onSuccess: (_, caseId) => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.case(caseId) });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixBenchmarks });
    },
  });
};

export const useAdminAdvisoryCases = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminCases,
    queryFn: () => axios.get("/advisory/admin/cases").then((r: any) => r?.payload?.cases ?? []),
    enabled,
  });

export const useAdminAdvisoryReports = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminReports,
    queryFn: () => axios.get("/advisory/admin/reports").then((r: any) => r?.payload?.reports ?? []),
    enabled,
  });

export const useAdminAssistantBriefLogs = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminAssistantBriefLogs,
    queryFn: () => axios.get("/advisory/admin/assistant-brief-logs").then((r: any) => r?.payload?.logs ?? []),
    enabled,
  });

export const useAdminAssistantAnswerLogs = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminAssistantAnswerLogs,
    queryFn: () => axios.get("/advisory/admin/assistant-answer-logs").then((r: any) => r?.payload?.logs ?? []),
    enabled,
  });

export const useAdminReportWorkflowEvents = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminReportWorkflowEvents,
    queryFn: () => axios.get("/advisory/admin/report-workflow-events").then((r: any) => r?.payload?.events ?? []),
    enabled,
  });

export const useAdminExpertReviews = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminExpertReviews,
    queryFn: () => axios.get("/advisory/admin/expert-reviews").then((r: any) => r?.payload?.reviews ?? []),
    enabled,
  });

export const useAdminRetainerCadences = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminRetainerCadences,
    queryFn: () => axios.get("/advisory/admin/retainer-cadences").then((r: any) => r?.payload?.cadences ?? []),
    enabled,
  });

export const useAdminHatcheries = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminHatcheries,
    queryFn: () => axios.get("/advisory/admin/hatcheries").then((r: any) => r?.payload?.hatcheries ?? []),
    enabled,
  });

export const useAdminHatcheryRecords = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminHatcheryRecords,
    queryFn: () => axios.get("/advisory/admin/hatchery-records").then((r: any) => r?.payload?.records ?? []),
    enabled,
  });

export const useAdminInvestorScores = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminInvestorScores,
    queryFn: () => axios.get("/advisory/admin/investor-scores").then((r: any) => r?.payload?.scores ?? []),
    enabled,
  });

export const useAdminPhaseSixBenchmarks = (enabled = true, filters: Record<string, string> = {}) =>
  useQuery({
    queryKey: advisoryKeys.adminPhaseSixBenchmarksFiltered(filters),
    queryFn: () => axios.get("/advisory/admin/benchmarks/phase-six", { params: filters }).then((r: any) => r?.payload ?? null),
    enabled,
  });

export const useAdminPhaseSixRevisions = (enabled = true) =>
  useQuery({
    queryKey: advisoryKeys.adminPhaseSixRevisions,
    queryFn: () => axios.get("/advisory/admin/phase-six-revisions").then((r: any) => r?.payload?.revisions ?? []),
    enabled,
  });

export const useUpdateAdvisoryCase = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, payload }: { caseId: string; payload: { status?: string; expert_notes?: string; report_id?: string } }) =>
      axios.patch(`/advisory/cases/${caseId}`, payload).then((r: any) => r?.payload?.case ?? null),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.case(variables.caseId) });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixBenchmarks });
    },
  });
};

export const useGenerateAdvisoryAssistantBrief = () =>
  useMutation({
    mutationFn: (caseId: string) =>
      axios.get(`/advisory/admin/cases/${caseId}/assistant-brief`).then((r: any) => r?.payload?.brief ?? null),
  });

export const useAcceptAdvisoryAssistantBrief = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ logId, reportId = "" }: { logId: string; reportId?: string }) =>
      axios.post(`/advisory/admin/assistant-brief-logs/${logId}/accept`, { report_id: reportId }).then((r: any) => r?.payload?.brief_log ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminAssistantBriefLogs });
    },
  });
};

export const useCreateReportFromAdvisoryAssistantBrief = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ logId, status = "expert_review_required" }: { logId: string; status?: string }) =>
      axios.post(`/advisory/admin/assistant-brief-logs/${logId}/draft-report`, { status }).then((r: any) => r?.payload ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminAssistantBriefLogs });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReports });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReportWorkflowEvents });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
    },
  });
};

export const useAskAdvisoryAssistant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { question: string; case_id?: string; limit?: number }) =>
      axios.post("/advisory/admin/assistant-answer", payload).then((r: any) => r?.payload?.answer ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminAssistantAnswerLogs });
    },
  });
};

export const useCreateExpertReview = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      case_id: string;
      review_type?: string;
      summary?: string;
      findings?: string[];
      recommendations?: string[];
      risk_flags?: string[];
      next_actions?: string[];
      status?: string;
    }) => axios.post("/advisory/expert-reviews", payload).then((r: any) => r?.payload?.review ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminExpertReviews });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
    },
  });
};

export const useCreateRetainerCadence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      case_id: string;
      cadence_type?: string;
      status?: string;
      last_review_at?: string | null;
      next_review_at?: string | null;
      agenda?: string[];
      notes?: string;
    }) => axios.post("/advisory/retainer-cadences", payload).then((r: any) => r?.payload?.cadence ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminRetainerCadences });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
    },
  });
};

export const useCreateHatcheryProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      case_id?: string;
      user_id?: string;
      name: string;
      location?: string;
      maturation_capacity?: number | null;
      larval_capacity?: number | null;
      biosecurity_level?: string;
      water_source?: string;
      notes?: string;
      client_visible?: boolean;
    }) => axios.post("/advisory/admin/hatcheries", payload).then((r: any) => r?.payload?.hatchery ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminHatcheries });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixBenchmarks });
    },
  });
};

export const useUpdateHatcheryProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ hatcheryId, payload }: {
      hatcheryId: string;
      payload: {
        case_id?: string;
        user_id?: string;
        name: string;
        location?: string;
        maturation_capacity?: number | null;
        larval_capacity?: number | null;
        biosecurity_level?: string;
        water_source?: string;
        notes?: string;
        client_visible?: boolean;
        change_note?: string;
      };
    }) => axios.patch(`/advisory/admin/hatcheries/${hatcheryId}`, payload).then((r: any) => r?.payload ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminHatcheries });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixRevisions });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
    },
  });
};

export const useCreateHatcheryRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      hatchery_id: string;
      case_id?: string;
      record_type: string;
      record_date?: string | null;
      batch_code?: string;
      broodstock_source?: string;
      metrics?: Record<string, any>;
      notes?: string;
      client_visible?: boolean;
    }) => axios.post("/advisory/admin/hatchery-records", payload).then((r: any) => r?.payload?.record ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminHatcheries });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminHatcheryRecords });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixBenchmarks });
    },
  });
};

export const useUpdateHatcheryRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, payload }: {
      recordId: string;
      payload: {
        hatchery_id: string;
        case_id?: string;
        record_type: string;
        record_date?: string | null;
        batch_code?: string;
        broodstock_source?: string;
        metrics?: Record<string, any>;
        notes?: string;
        client_visible?: boolean;
        change_note?: string;
      };
    }) => axios.patch(`/advisory/admin/hatchery-records/${recordId}`, payload).then((r: any) => r?.payload ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminHatcheryRecords });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixBenchmarks });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixRevisions });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
    },
  });
};

export const useCreateInvestorScore = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      case_id: string;
      project_type?: string;
      location?: string;
      planned_capacity?: string;
      capex_estimate_idr?: number | null;
      opex_estimate_idr?: number | null;
      technical_score?: number;
      management_score?: number;
      biosecurity_score?: number;
      market_score?: number;
      financial_score?: number;
      red_flags?: string[];
      recommendations?: string[];
      assumptions?: string[];
      client_visible?: boolean;
    }) => axios.post("/advisory/admin/investor-scores", payload).then((r: any) => r?.payload?.score ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminInvestorScores });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixBenchmarks });
    },
  });
};

export const useUpdateInvestorScore = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ scoreId, payload }: {
      scoreId: string;
      payload: {
        case_id: string;
        project_type?: string;
        location?: string;
        planned_capacity?: string;
        capex_estimate_idr?: number | null;
        opex_estimate_idr?: number | null;
        technical_score?: number;
        management_score?: number;
        biosecurity_score?: number;
        market_score?: number;
        financial_score?: number;
        red_flags?: string[];
        recommendations?: string[];
        assumptions?: string[];
        client_visible?: boolean;
        change_note?: string;
      };
    }) => axios.patch(`/advisory/admin/investor-scores/${scoreId}`, payload).then((r: any) => r?.payload ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminInvestorScores });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixBenchmarks });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminPhaseSixRevisions });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
    },
  });
};

export const useCreateInvestorScoreReport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ scoreId, status = "expert_review_required" }: { scoreId: string; status?: string }) =>
      axios.post(`/advisory/admin/investor-scores/${scoreId}/report`, { status }).then((r: any) => r?.payload ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReports });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReportWorkflowEvents });
    },
  });
};

export const useCreateAdvisoryReport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      case_id: string;
      title: string;
      executive_summary?: string;
      data_received?: string[];
      key_findings?: string[];
      likely_causes?: string[];
      technical_interpretation?: string;
      economic_implication?: string;
      corrective_action_plan?: string[];
      monitoring_plan?: string[];
      assumptions_and_limits?: string[];
      source_citations?: any[];
      generated_from_brief_log_id?: string;
      file_url?: string;
      status?: string;
    }) => axios.post("/advisory/reports", payload).then((r: any) => r?.payload?.report ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReports });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReportWorkflowEvents });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
    },
  });
};

export const useUpdateAdvisoryReportWorkflow = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ reportId, payload }: { reportId: string; payload: { status: string; review_note?: string } }) =>
      axios.patch(`/advisory/admin/reports/${reportId}/workflow`, payload).then((r: any) => r?.payload ?? null),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReports });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReportWorkflowEvents });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
      if (data?.case?.id) {
        queryClient.invalidateQueries({ queryKey: advisoryKeys.case(data.case.id) });
      }
    },
  });
};
