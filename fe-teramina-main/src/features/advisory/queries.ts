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
  adminExpertReviews: ["advisory-admin-expert-reviews"] as const,
  adminRetainerCadences: ["advisory-admin-retainer-cadences"] as const,
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

export const useUpdateAdvisoryCase = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, payload }: { caseId: string; payload: { status?: string; expert_notes?: string; report_id?: string } }) =>
      axios.patch(`/advisory/cases/${caseId}`, payload).then((r: any) => r?.payload?.case ?? null),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.case(variables.caseId) });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
    },
  });
};

export const useGenerateAdvisoryAssistantBrief = () =>
  useMutation({
    mutationFn: (caseId: string) =>
      axios.get(`/advisory/admin/cases/${caseId}/assistant-brief`).then((r: any) => r?.payload?.brief ?? null),
  });

export const useAcceptAdvisoryAssistantBrief = () =>
  useMutation({
    mutationFn: ({ logId, reportId = "" }: { logId: string; reportId?: string }) =>
      axios.post(`/advisory/admin/assistant-brief-logs/${logId}/accept`, { report_id: reportId }).then((r: any) => r?.payload?.brief_log ?? null),
  });

export const useCreateReportFromAdvisoryAssistantBrief = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ logId, status = "expert_review_required" }: { logId: string; status?: string }) =>
      axios.post(`/advisory/admin/assistant-brief-logs/${logId}/draft-report`, { status }).then((r: any) => r?.payload ?? null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminCases });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.adminReports });
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
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
      queryClient.invalidateQueries({ queryKey: advisoryKeys.cases });
      if (data?.case?.id) {
        queryClient.invalidateQueries({ queryKey: advisoryKeys.case(data.case.id) });
      }
    },
  });
};
