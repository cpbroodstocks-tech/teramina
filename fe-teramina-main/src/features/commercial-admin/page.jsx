import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useAdminAccessRequests, useUpdateAdminAccessRequest, useUserProfile } from "features/user/queries";
import {
  useAcceptAdvisoryAssistantBrief,
  useAdminAssistantAnswerLogs,
  useAdminAssistantBriefLogs,
  useAdminAdvisoryCases,
  useAdminExpertReviews,
  useGenerateAdvisoryAssistantBrief,
  useAskAdvisoryAssistant,
  useAdminHatcheries,
  useAdminHatcheryRecords,
  useAdminInvestorScores,
  useAdminPhaseSixBenchmarks,
  useAdminPhaseSixRevisions,
  useCreateAdvisoryReport,
  useCreateExpertReview,
  useCreateHatcheryProfile,
  useCreateHatcheryRecord,
  useCreateInvestorScore,
  useCreateInvestorScoreReport,
  useCreateReportFromAdvisoryAssistantBrief,
  useCreateRetainerCadence,
  useAdminAdvisoryReports,
  useAdminReportWorkflowEvents,
  useAdminRetainerCadences,
  useUpdateHatcheryProfile,
  useUpdateHatcheryRecord,
  useUpdateInvestorScore,
  useUpdateAdvisoryCase,
  useUpdateAdvisoryReportWorkflow,
} from "features/advisory/queries";
import {
  useAdminContentAccess,
  useAdminContentItem,
  useAdminContentItems,
  useAdminContentRevisions,
  useCreateContentItem,
  useGrantContentAccess,
  useTransitionContentWorkflow,
  useUpdateContentItem,
} from "features/content/queries";
import {
  useAdminInvoices,
  useCreateInvoice,
  useMarkInvoicePaid,
} from "features/billing/queries";

const listFromText = (value) => value.split("\n").map((item) => item.trim()).filter(Boolean);

const slugFromTitle = (value) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

const statusOptions = ["inquiry", "awaiting_data", "in_review", "report_ready", "closed", "cancelled"];
const contentWorkflowStatuses = ["draft", "in_review", "changes_requested", "approved", "published", "archived"];
const contentTypes = ["article", "guide", "sop", "checklist", "template", "calculator", "report_template"];
const contentLanguages = ["en", "id"];
const contentVariantTypes = ["master", "practical"];
const accessLevels = ["free", "paid", "client", "admin"];
const invoiceTypes = ["content_access", "advisory_case", "subscription"];
const expertReviewTypes = ["technical", "disease", "economics", "hatchery", "investment"];
const retainerCadenceTypes = ["weekly", "biweekly", "monthly", "custom"];
const retainerCadenceStatuses = ["active", "paused", "completed", "cancelled"];
const reportStatuses = ["draft", "expert_review_required", "delivered"];
const hatcheryRecordTypes = ["broodstock_batch", "maturation_performance", "spawning_log", "nauplii_output", "pl_quality_test"];
const investorProjectTypes = ["farm", "hatchery", "integrated"];
const investorRiskLevels = ["low", "moderate", "high", "critical"];
const formatIdr = (value) => `Rp ${Number(value || 0).toLocaleString("id-ID")}`;
const numberOrNull = (value) => (value === "" || value === null || value === undefined ? null : Number(value));
const boolFromSelect = (value) => value === "true";
const datetimeInputValue = (value) => (value ? value.slice(0, 16) : "");

const hatcheryMetricFields = {
  broodstock_batch: ["female_count", "male_count", "mortality_count"],
  maturation_performance: ["mating_rate", "spawning_rate"],
  spawning_log: ["spawning_rate", "hatching_rate"],
  nauplii_output: ["nauplii_count", "hatching_rate"],
  pl_quality_test: ["pl_quality_score", "pcr_status"],
};

const buildHatcheryMetrics = (form) => {
  const metrics = {};
  (hatcheryMetricFields[form.record_type] || []).forEach((field) => {
    const value = form[field];
    if (value === "") return;
    const numericValue = Number(value);
    metrics[field] = Number.isNaN(numericValue) ? value : numericValue;
  });
  return metrics;
};

const AdminSection = ({ id, title, description, children }) => (
  <Paper id={id} variant="outlined" sx={{ p: 3, scrollMarginTop: 16 }}>
    <Stack gap={2}>
      <Box>
        <Typography variant="h5" fontWeight={700}>{title}</Typography>
        <Typography color="text.secondary">{description}</Typography>
      </Box>
      {children}
    </Stack>
  </Paper>
);

const CommercialAdminPage = () => {
  const { data: profile, isLoading: profileLoading } = useUserProfile();
  const isAdmin = profile?.role_user === "admin";
  const { data: contentItems = [], isLoading: contentLoading } = useAdminContentItems(isAdmin);
  const { data: accessGrants = [] } = useAdminContentAccess(isAdmin);
  const { data: cases = [], isLoading: casesLoading } = useAdminAdvisoryCases(isAdmin);
  const { data: adminReports = [] } = useAdminAdvisoryReports(isAdmin);
  const { data: assistantBriefLogs = [] } = useAdminAssistantBriefLogs(isAdmin);
  const { data: assistantAnswerLogs = [] } = useAdminAssistantAnswerLogs(isAdmin);
  const { data: reportWorkflowEvents = [] } = useAdminReportWorkflowEvents(isAdmin);
  const { data: expertReviews = [] } = useAdminExpertReviews(isAdmin);
  const { data: retainerCadences = [] } = useAdminRetainerCadences(isAdmin);
  const { data: hatcheries = [] } = useAdminHatcheries(isAdmin);
  const { data: hatcheryRecords = [] } = useAdminHatcheryRecords(isAdmin);
  const { data: investorScores = [] } = useAdminInvestorScores(isAdmin);
  const { data: phaseSixRevisions = [] } = useAdminPhaseSixRevisions(isAdmin);
  const { data: invoices = [] } = useAdminInvoices(isAdmin);
  const { data: accessRequests = [] } = useAdminAccessRequests(isAdmin);
  const updateAccessRequest = useUpdateAdminAccessRequest();
  const createContent = useCreateContentItem();
  const [selectedContentId, setSelectedContentId] = useState("");
  const { data: selectedContent } = useAdminContentItem(selectedContentId, isAdmin);
  const { data: contentRevisions = [] } = useAdminContentRevisions(selectedContentId, isAdmin);
  const grantAccess = useGrantContentAccess();
  const updateContent = useUpdateContentItem();
  const transitionContentWorkflow = useTransitionContentWorkflow();
  const updateCase = useUpdateAdvisoryCase();
  const assistantBrief = useGenerateAdvisoryAssistantBrief();
  const assistantAnswer = useAskAdvisoryAssistant();
  const acceptAssistantBrief = useAcceptAdvisoryAssistantBrief();
  const createAssistantDraftReport = useCreateReportFromAdvisoryAssistantBrief();
  const createReport = useCreateAdvisoryReport();
  const updateReportWorkflow = useUpdateAdvisoryReportWorkflow();
  const createExpertReview = useCreateExpertReview();
  const createRetainerCadence = useCreateRetainerCadence();
  const createHatcheryProfile = useCreateHatcheryProfile();
  const createHatcheryRecord = useCreateHatcheryRecord();
  const createInvestorScore = useCreateInvestorScore();
  const createInvestorScoreReport = useCreateInvestorScoreReport();
  const updateHatcheryProfile = useUpdateHatcheryProfile();
  const updateHatcheryRecord = useUpdateHatcheryRecord();
  const updateInvestorScore = useUpdateInvestorScore();
  const createInvoice = useCreateInvoice();
  const markInvoicePaid = useMarkInvoicePaid();

  const [contentForm, setContentForm] = useState({
    title: "",
    slug: "",
    summary: "",
    category: "Farm",
    tags: "",
    language: "en",
    variant_group_id: "",
    variant_type: "master",
    source_content_id: "",
    content_type: "guide",
    access_level: "paid",
    status: "draft",
    body_markdown: "",
    file_url: "",
  });
  const [grantForm, setGrantForm] = useState({
    user_id: "",
    content_id: "",
    access_source: "manual",
    expires_at: "",
  });
  const [editContentForm, setEditContentForm] = useState({
    title: "",
    summary: "",
    category: "",
    tags: "",
    language: "en",
    variant_group_id: "",
    variant_type: "master",
    source_content_id: "",
    content_type: "guide",
    access_level: "paid",
    status: "draft",
    version: "1.0",
    body_markdown: "",
    file_url: "",
    change_note: "",
  });
  const [workflowForm, setWorkflowForm] = useState({
    status: "draft",
    review_note: "",
  });
  const [caseForm, setCaseForm] = useState({
    caseId: "",
    status: "inquiry",
    expert_notes: "",
  });
  const [assistantCaseId, setAssistantCaseId] = useState("");
  const [assistantAnswerForm, setAssistantAnswerForm] = useState({
    case_id: "",
    question: "",
  });
  const [reportForm, setReportForm] = useState({
    case_id: "",
    title: "",
    executive_summary: "",
    key_findings: "",
    corrective_action_plan: "",
    file_url: "",
    status: "delivered",
  });
  const [reportWorkflowForm, setReportWorkflowForm] = useState({
    report_id: "",
    status: "delivered",
    review_note: "",
  });
  const [expertReviewForm, setExpertReviewForm] = useState({
    case_id: "",
    review_type: "technical",
    summary: "",
    findings: "",
    recommendations: "",
    risk_flags: "",
    next_actions: "",
    status: "delivered",
  });
  const [retainerCadenceForm, setRetainerCadenceForm] = useState({
    case_id: "",
    cadence_type: "monthly",
    status: "active",
    last_review_at: "",
    next_review_at: "",
    agenda: "",
    notes: "",
  });
  const [hatcheryProfileForm, setHatcheryProfileForm] = useState({
    case_id: "",
    user_id: "",
    name: "",
    location: "",
    maturation_capacity: "",
    larval_capacity: "",
    biosecurity_level: "",
    water_source: "",
    notes: "",
    client_visible: "false",
    change_note: "",
  });
  const [editingHatcheryProfileId, setEditingHatcheryProfileId] = useState("");
  const [hatcheryRecordForm, setHatcheryRecordForm] = useState({
    hatchery_id: "",
    record_type: "broodstock_batch",
    record_date: "",
    batch_code: "",
    broodstock_source: "",
    client_visible: "false",
    female_count: "",
    male_count: "",
    mortality_count: "",
    mating_rate: "",
    spawning_rate: "",
    hatching_rate: "",
    nauplii_count: "",
    pl_quality_score: "",
    pcr_status: "",
    notes: "",
    change_note: "",
  });
  const [editingHatcheryRecordId, setEditingHatcheryRecordId] = useState("");
  const [investorScoreForm, setInvestorScoreForm] = useState({
    case_id: "",
    project_type: "farm",
    location: "",
    planned_capacity: "",
    capex_estimate_idr: "",
    opex_estimate_idr: "",
    technical_score: "",
    management_score: "",
    biosecurity_score: "",
    market_score: "",
    financial_score: "",
    red_flags: "",
    recommendations: "",
    assumptions: "",
    client_visible: "false",
    change_note: "",
  });
  const [editingInvestorScoreId, setEditingInvestorScoreId] = useState("");
  const [phaseSixBenchmarkFilters, setPhaseSixBenchmarkFilters] = useState({
    record_type: "",
    risk_level: "",
    project_type: "",
    from_month: "",
    to_month: "",
  });
  const { data: phaseSixBenchmarks } = useAdminPhaseSixBenchmarks(isAdmin, phaseSixBenchmarkFilters);
  const [invoiceForm, setInvoiceForm] = useState({
    user_id: "",
    invoice_type: "content_access",
    description: "",
    amount_idr: "",
    content_id: "",
    advisory_case_id: "",
    service_package_id: "",
    subscription_months: "1",
    access_expires_at: "",
    due_at: "",
    notes: "",
  });
  const [paidForm, setPaidForm] = useState({
    invoice_id: "",
    payment_reference: "",
    notes: "",
    access_expires_at: "",
  });

  const selectedCase = useMemo(
    () => cases.find((item) => item.id === caseForm.caseId || item.id === reportForm.case_id),
    [caseForm.caseId, cases, reportForm.case_id],
  );

  useEffect(() => {
    if (!selectedContentId && contentItems.length) {
      setSelectedContentId(contentItems[0].id);
    }
  }, [contentItems, selectedContentId]);

  useEffect(() => {
    if (!assistantCaseId && cases.length) {
      setAssistantCaseId(cases[0].id);
    }
  }, [assistantCaseId, cases]);

  useEffect(() => {
    if (!hatcheryRecordForm.hatchery_id && hatcheries.length) {
      setHatcheryRecordForm((prev) => ({ ...prev, hatchery_id: hatcheries[0].id }));
    }
  }, [hatcheries, hatcheryRecordForm.hatchery_id]);

  useEffect(() => {
    if (!reportWorkflowForm.report_id && adminReports.length) {
      setReportWorkflowForm((prev) => ({ ...prev, report_id: adminReports[0].id }));
    }
  }, [adminReports, reportWorkflowForm.report_id]);

  useEffect(() => {
    if (!selectedContent) return;
    setEditContentForm({
      title: selectedContent.title || "",
      summary: selectedContent.summary || "",
      category: selectedContent.category || "",
      tags: (selectedContent.tags || []).join("\n"),
      language: selectedContent.language || "en",
      variant_group_id: selectedContent.variant_group_id || "",
      variant_type: selectedContent.variant_type || "master",
      source_content_id: selectedContent.source_content_id || "",
      content_type: selectedContent.content_type || "guide",
      access_level: selectedContent.access_level || "paid",
      status: selectedContent.status || "draft",
      version: selectedContent.version || "1.0",
      body_markdown: selectedContent.body_markdown || "",
      file_url: selectedContent.file_url || "",
      change_note: "",
    });
    setWorkflowForm({
      status: selectedContent.status || "draft",
      review_note: selectedContent.review_notes || "",
    });
  }, [selectedContent]);

  if (profileLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!isAdmin) {
    return (
      <Container maxWidth="md" sx={{ py: 3 }}>
        <Alert severity="warning">Commercial admin is available only to admin users.</Alert>
      </Container>
    );
  }

  const updateContentForm = (key) => (event) => {
    const value = event.target.value;
    setContentForm((prev) => ({
      ...prev,
      [key]: value,
      slug: key === "title" && !prev.slug ? slugFromTitle(value) : prev.slug,
    }));
  };

  const submitContent = async (event) => {
    event.preventDefault();
    await createContent.mutateAsync({
      ...contentForm,
      tags: listFromText(contentForm.tags),
    });
    setContentForm((prev) => ({
      ...prev,
      title: "",
      slug: "",
      summary: "",
      tags: "",
      variant_group_id: "",
      source_content_id: "",
      body_markdown: "",
      file_url: "",
    }));
  };

  const submitGrant = async (event) => {
    event.preventDefault();
    await grantAccess.mutateAsync({
      ...grantForm,
      expires_at: grantForm.expires_at ? new Date(grantForm.expires_at).toISOString() : null,
    });
    setGrantForm((prev) => ({ ...prev, user_id: "", expires_at: "" }));
  };

  const submitContentUpdate = async (event) => {
    event.preventDefault();
    await updateContent.mutateAsync({
      contentId: selectedContentId,
      payload: {
        ...editContentForm,
        tags: listFromText(editContentForm.tags),
        change_note: editContentForm.change_note || "Admin content update",
      },
    });
    setEditContentForm((prev) => ({ ...prev, change_note: "" }));
  };

  const submitWorkflowTransition = async (event) => {
    event.preventDefault();
    await transitionContentWorkflow.mutateAsync({
      contentId: selectedContentId,
      payload: {
        status: workflowForm.status,
        review_note: workflowForm.review_note,
      },
    });
  };

  const submitInvoice = async (event) => {
    event.preventDefault();
    await createInvoice.mutateAsync({
      user_id: invoiceForm.user_id,
      invoice_type: invoiceForm.invoice_type,
      description: invoiceForm.description,
      amount_idr: Number(invoiceForm.amount_idr || 0),
      content_ids: invoiceForm.content_id ? [invoiceForm.content_id] : [],
      advisory_case_id: invoiceForm.advisory_case_id,
      service_package_id: invoiceForm.service_package_id,
      subscription_months: Number(invoiceForm.subscription_months || 1),
      access_expires_at: invoiceForm.access_expires_at ? new Date(invoiceForm.access_expires_at).toISOString() : null,
      due_at: invoiceForm.due_at ? new Date(invoiceForm.due_at).toISOString() : null,
      status: "issued",
      payment_method: "manual_transfer",
      notes: invoiceForm.notes,
    });
    setInvoiceForm((prev) => ({
      ...prev,
      user_id: "",
      description: "",
      amount_idr: "",
      content_id: "",
      advisory_case_id: "",
      service_package_id: "",
      access_expires_at: "",
      due_at: "",
      notes: "",
    }));
  };

  const submitPaid = async (event) => {
    event.preventDefault();
    await markInvoicePaid.mutateAsync({
      invoiceId: paidForm.invoice_id,
      payload: {
        payment_method: "manual_transfer",
        payment_reference: paidForm.payment_reference,
        notes: paidForm.notes,
        access_expires_at: paidForm.access_expires_at ? new Date(paidForm.access_expires_at).toISOString() : null,
      },
    });
    setPaidForm((prev) => ({ ...prev, invoice_id: "", payment_reference: "", notes: "", access_expires_at: "" }));
  };

  const selectCaseForUpdate = (caseId) => {
    const item = cases.find((nextCase) => nextCase.id === caseId);
    setCaseForm({
      caseId,
      status: item?.status || "inquiry",
      expert_notes: item?.expert_notes || "",
    });
  };

  const submitCaseUpdate = async (event) => {
    event.preventDefault();
    await updateCase.mutateAsync({
      caseId: caseForm.caseId,
      payload: {
        status: caseForm.status,
        expert_notes: caseForm.expert_notes,
      },
    });
  };

  const submitAssistantBrief = async (event) => {
    event.preventDefault();
    await assistantBrief.mutateAsync(assistantCaseId);
  };

  const applyAssistantDraft = async () => {
    const draft = assistantBrief.data?.draft_report;
    if (!draft) return;
    if (assistantBrief.data?.brief_log_id) {
      await acceptAssistantBrief.mutateAsync({ logId: assistantBrief.data.brief_log_id });
    }
    setReportForm((prev) => ({
      ...prev,
      case_id: assistantBrief.data.case?.id || assistantCaseId,
      title: draft.title || prev.title,
      executive_summary: draft.executive_summary || "",
      key_findings: (draft.key_findings || []).join("\n"),
      corrective_action_plan: (draft.corrective_action_plan || []).join("\n"),
      status: "draft",
    }));
  };

  const createInternalAssistantDraft = async () => {
    if (!assistantBrief.data?.brief_log_id) return;
    await createAssistantDraftReport.mutateAsync({
      logId: assistantBrief.data.brief_log_id,
      status: "expert_review_required",
    });
  };

  const submitAssistantAnswer = async (event) => {
    event.preventDefault();
    await assistantAnswer.mutateAsync({
      case_id: assistantAnswerForm.case_id,
      question: assistantAnswerForm.question,
      limit: 6,
    });
  };

  const submitReport = async (event) => {
    event.preventDefault();
    await createReport.mutateAsync({
      case_id: reportForm.case_id,
      title: reportForm.title,
      executive_summary: reportForm.executive_summary,
      key_findings: listFromText(reportForm.key_findings),
      corrective_action_plan: listFromText(reportForm.corrective_action_plan),
      file_url: reportForm.file_url,
      status: reportForm.status,
    });
    setReportForm((prev) => ({ ...prev, title: "", executive_summary: "", key_findings: "", corrective_action_plan: "", file_url: "" }));
  };

  const submitReportWorkflow = async (event) => {
    event.preventDefault();
    await updateReportWorkflow.mutateAsync({
      reportId: reportWorkflowForm.report_id,
      payload: {
        status: reportWorkflowForm.status,
        review_note: reportWorkflowForm.review_note,
      },
    });
    setReportWorkflowForm((prev) => ({ ...prev, review_note: "" }));
  };

  const submitExpertReview = async (event) => {
    event.preventDefault();
    await createExpertReview.mutateAsync({
      case_id: expertReviewForm.case_id,
      review_type: expertReviewForm.review_type,
      summary: expertReviewForm.summary,
      findings: listFromText(expertReviewForm.findings),
      recommendations: listFromText(expertReviewForm.recommendations),
      risk_flags: listFromText(expertReviewForm.risk_flags),
      next_actions: listFromText(expertReviewForm.next_actions),
      status: expertReviewForm.status,
    });
    setExpertReviewForm((prev) => ({
      ...prev,
      summary: "",
      findings: "",
      recommendations: "",
      risk_flags: "",
      next_actions: "",
    }));
  };

  const submitRetainerCadence = async (event) => {
    event.preventDefault();
    await createRetainerCadence.mutateAsync({
      case_id: retainerCadenceForm.case_id,
      cadence_type: retainerCadenceForm.cadence_type,
      status: retainerCadenceForm.status,
      last_review_at: retainerCadenceForm.last_review_at ? new Date(retainerCadenceForm.last_review_at).toISOString() : null,
      next_review_at: retainerCadenceForm.next_review_at ? new Date(retainerCadenceForm.next_review_at).toISOString() : null,
      agenda: listFromText(retainerCadenceForm.agenda),
      notes: retainerCadenceForm.notes,
    });
    setRetainerCadenceForm((prev) => ({ ...prev, agenda: "", notes: "" }));
  };

  const hatcheryProfilePayload = () => ({
    case_id: hatcheryProfileForm.case_id,
    user_id: hatcheryProfileForm.user_id,
    name: hatcheryProfileForm.name,
    location: hatcheryProfileForm.location,
    maturation_capacity: numberOrNull(hatcheryProfileForm.maturation_capacity),
    larval_capacity: numberOrNull(hatcheryProfileForm.larval_capacity),
    biosecurity_level: hatcheryProfileForm.biosecurity_level,
    water_source: hatcheryProfileForm.water_source,
    notes: hatcheryProfileForm.notes,
    client_visible: boolFromSelect(hatcheryProfileForm.client_visible),
    change_note: hatcheryProfileForm.change_note,
  });

  const submitHatcheryProfile = async (event) => {
    event.preventDefault();
    if (editingHatcheryProfileId) {
      await updateHatcheryProfile.mutateAsync({
        hatcheryId: editingHatcheryProfileId,
        payload: hatcheryProfilePayload(),
      });
      setEditingHatcheryProfileId("");
    } else {
      await createHatcheryProfile.mutateAsync(hatcheryProfilePayload());
    }
    setHatcheryProfileForm((prev) => ({ ...prev, name: "", location: "", notes: "", change_note: "" }));
  };

  const editHatcheryProfile = (hatchery) => {
    setEditingHatcheryProfileId(hatchery.id);
    setHatcheryProfileForm({
      case_id: hatchery.case_id || "",
      user_id: hatchery.user_id || "",
      name: hatchery.name || "",
      location: hatchery.location || "",
      maturation_capacity: hatchery.maturation_capacity ?? "",
      larval_capacity: hatchery.larval_capacity ?? "",
      biosecurity_level: hatchery.biosecurity_level || "",
      water_source: hatchery.water_source || "",
      notes: hatchery.notes || "",
      client_visible: hatchery.client_visible ? "true" : "false",
      change_note: "",
    });
  };

  const resetHatcheryProfileEdit = () => {
    setEditingHatcheryProfileId("");
    setHatcheryProfileForm((prev) => ({
      ...prev,
      name: "",
      location: "",
      maturation_capacity: "",
      larval_capacity: "",
      biosecurity_level: "",
      water_source: "",
      notes: "",
      client_visible: "false",
      change_note: "",
    }));
  };

  const hatcheryRecordPayload = () => ({
    hatchery_id: hatcheryRecordForm.hatchery_id,
    record_type: hatcheryRecordForm.record_type,
    record_date: hatcheryRecordForm.record_date ? new Date(hatcheryRecordForm.record_date).toISOString() : null,
    batch_code: hatcheryRecordForm.batch_code,
    broodstock_source: hatcheryRecordForm.broodstock_source,
    metrics: buildHatcheryMetrics(hatcheryRecordForm),
    notes: hatcheryRecordForm.notes,
    client_visible: boolFromSelect(hatcheryRecordForm.client_visible),
    change_note: hatcheryRecordForm.change_note,
  });

  const resetHatcheryRecordForm = () => {
    setHatcheryRecordForm((prev) => ({
      ...prev,
      batch_code: "",
      broodstock_source: "",
      female_count: "",
      male_count: "",
      mortality_count: "",
      mating_rate: "",
      spawning_rate: "",
      hatching_rate: "",
      nauplii_count: "",
      pl_quality_score: "",
      pcr_status: "",
      notes: "",
      change_note: "",
    }));
  };

  const submitHatcheryRecord = async (event) => {
    event.preventDefault();
    if (editingHatcheryRecordId) {
      await updateHatcheryRecord.mutateAsync({
        recordId: editingHatcheryRecordId,
        payload: hatcheryRecordPayload(),
      });
      setEditingHatcheryRecordId("");
    } else {
      await createHatcheryRecord.mutateAsync(hatcheryRecordPayload());
    }
    resetHatcheryRecordForm();
  };

  const editHatcheryRecord = (record) => {
    const metrics = record.metrics || {};
    setEditingHatcheryRecordId(record.id);
    setHatcheryRecordForm({
      hatchery_id: record.hatchery_id || "",
      record_type: record.record_type || "broodstock_batch",
      record_date: datetimeInputValue(record.record_date),
      batch_code: record.batch_code || "",
      broodstock_source: record.broodstock_source || "",
      client_visible: record.client_visible ? "true" : "false",
      female_count: metrics.female_count ?? "",
      male_count: metrics.male_count ?? "",
      mortality_count: metrics.mortality_count ?? "",
      mating_rate: metrics.mating_rate ?? "",
      spawning_rate: metrics.spawning_rate ?? "",
      hatching_rate: metrics.hatching_rate ?? "",
      nauplii_count: metrics.nauplii_count ?? "",
      pl_quality_score: metrics.pl_quality_score ?? "",
      pcr_status: metrics.pcr_status ?? "",
      notes: record.notes || "",
      change_note: "",
    });
  };

  const resetHatcheryRecordEdit = () => {
    setEditingHatcheryRecordId("");
    resetHatcheryRecordForm();
  };

  const investorScorePayload = () => ({
    case_id: investorScoreForm.case_id,
    project_type: investorScoreForm.project_type,
    location: investorScoreForm.location,
    planned_capacity: investorScoreForm.planned_capacity,
    capex_estimate_idr: numberOrNull(investorScoreForm.capex_estimate_idr),
    opex_estimate_idr: numberOrNull(investorScoreForm.opex_estimate_idr),
    technical_score: Number(investorScoreForm.technical_score || 0),
    management_score: Number(investorScoreForm.management_score || 0),
    biosecurity_score: Number(investorScoreForm.biosecurity_score || 0),
    market_score: Number(investorScoreForm.market_score || 0),
    financial_score: Number(investorScoreForm.financial_score || 0),
    red_flags: listFromText(investorScoreForm.red_flags),
    recommendations: listFromText(investorScoreForm.recommendations),
    assumptions: listFromText(investorScoreForm.assumptions),
    client_visible: boolFromSelect(investorScoreForm.client_visible),
    change_note: investorScoreForm.change_note,
  });

  const submitInvestorScore = async (event) => {
    event.preventDefault();
    if (editingInvestorScoreId) {
      await updateInvestorScore.mutateAsync({
        scoreId: editingInvestorScoreId,
        payload: investorScorePayload(),
      });
      setEditingInvestorScoreId("");
    } else {
      await createInvestorScore.mutateAsync(investorScorePayload());
    }
    setInvestorScoreForm((prev) => ({ ...prev, red_flags: "", recommendations: "", assumptions: "", change_note: "" }));
  };

  const editInvestorScore = (score) => {
    setEditingInvestorScoreId(score.id);
    setInvestorScoreForm({
      case_id: score.case_id || "",
      project_type: score.project_type || "farm",
      location: score.location || "",
      planned_capacity: score.planned_capacity || "",
      capex_estimate_idr: score.capex_estimate_idr ?? "",
      opex_estimate_idr: score.opex_estimate_idr ?? "",
      technical_score: score.technical_score ?? "",
      management_score: score.management_score ?? "",
      biosecurity_score: score.biosecurity_score ?? "",
      market_score: score.market_score ?? "",
      financial_score: score.financial_score ?? "",
      red_flags: (score.red_flags || []).join("\n"),
      recommendations: (score.recommendations || []).join("\n"),
      assumptions: (score.assumptions || []).join("\n"),
      client_visible: score.client_visible ? "true" : "false",
      change_note: "",
    });
  };

  const resetInvestorScoreEdit = () => {
    setEditingInvestorScoreId("");
    setInvestorScoreForm((prev) => ({
      ...prev,
      location: "",
      planned_capacity: "",
      capex_estimate_idr: "",
      opex_estimate_idr: "",
      red_flags: "",
      recommendations: "",
      assumptions: "",
      change_note: "",
    }));
  };

  const createInvestorDraftReport = async (scoreId) => {
    await createInvestorScoreReport.mutateAsync({ scoreId, status: "expert_review_required" });
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Stack gap={3}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Commercial Admin</Typography>
          <Typography color="text.secondary">
            Operate paid library access and advisory delivery before automated payment and CMS flows are introduced.
          </Typography>
        </Box>

        <Paper variant="outlined" sx={{ p: 1, position: "sticky", top: 8, zIndex: 2 }}>
          <Stack direction="row" gap={0.5} sx={{ flexWrap: "wrap" }}>
            <Button href="#access-requests" size="small">Access</Button>
            <Button href="#content-operations" size="small">Content</Button>
            <Button href="#billing-operations" size="small">Billing</Button>
            <Button href="#advisory-operations" size="small">Advisory</Button>
            <Button href="#audit-trail" size="small">Audit</Button>
          </Stack>
        </Paper>

        <AdminSection id="access-requests" title="Closed Beta Access" description="Approve or reject requests before users can create an account.">
          {updateAccessRequest.isError && <Alert severity="error">Failed to update access request.</Alert>}
          {accessRequests.length ? (
            <Stack gap={1}>
              {accessRequests.slice(0, 20).map((item) => (
                <Paper key={item.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction={{ xs: "column", sm: "row" }} gap={1} sx={{ alignItems: { sm: "center" } }}>
                    <Box flex={1}>
                      <Typography fontWeight={700}>{item.name || item.email}</Typography>
                      <Typography variant="body2" color="text.secondary">{item.email} · {item.source}</Typography>
                    </Box>
                    <Chip size="small" label={item.status} color={item.status === "approved" ? "success" : "default"} />
                    {item.status === "pending" && (
                      <>
                        <Button
                          size="small"
                          variant="contained"
                          onClick={() => updateAccessRequest.mutate({ requestId: item.id, status: "approved" })}
                        >
                          Approve
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => updateAccessRequest.mutate({ requestId: item.id, status: "rejected" })}
                        >
                          Reject
                        </Button>
                      </>
                    )}
                  </Stack>
                </Paper>
              ))}
            </Stack>
          ) : (
            <Alert severity="info">No beta access requests yet.</Alert>
          )}
        </AdminSection>

        <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
          <AdminSection title="Create Content" description="Add a draft or published library document for the paid knowledge base.">
            {createContent.isError && <Alert severity="error">Failed to create content.</Alert>}
            {createContent.isSuccess && <Alert severity="success">Content item created.</Alert>}
            <Stack component="form" gap={2} onSubmit={submitContent}>
              <TextField label="Title" value={contentForm.title} onChange={updateContentForm("title")} required />
              <TextField label="Slug" value={contentForm.slug} onChange={updateContentForm("slug")} required />
              <TextField label="Summary" value={contentForm.summary} onChange={updateContentForm("summary")} multiline minRows={2} />
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField label="Category" value={contentForm.category} onChange={updateContentForm("category")} required fullWidth />
                <TextField select label="Type" value={contentForm.content_type} onChange={updateContentForm("content_type")} fullWidth>
                  {contentTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField select label="Language" value={contentForm.language} onChange={updateContentForm("language")} fullWidth>
                  {contentLanguages.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField select label="Variant" value={contentForm.variant_type} onChange={updateContentForm("variant_type")} fullWidth>
                  {contentVariantTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  label="Variant group ID"
                  value={contentForm.variant_group_id}
                  onChange={updateContentForm("variant_group_id")}
                  fullWidth
                />
                <TextField
                  label="Source content ID"
                  value={contentForm.source_content_id}
                  onChange={updateContentForm("source_content_id")}
                  fullWidth
                />
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField select label="Access" value={contentForm.access_level} onChange={updateContentForm("access_level")} fullWidth>
                  {accessLevels.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField select label="Status" value={contentForm.status} onChange={updateContentForm("status")} fullWidth>
                  {contentWorkflowStatuses.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
              </Stack>
              <TextField label="Tags, one per line" value={contentForm.tags} onChange={updateContentForm("tags")} multiline minRows={3} />
              <TextField label="Body markdown" value={contentForm.body_markdown} onChange={updateContentForm("body_markdown")} multiline minRows={5} />
              <TextField label="File URL" value={contentForm.file_url} onChange={updateContentForm("file_url")} />
              <Button type="submit" variant="contained" disabled={createContent.isPending}>
                {createContent.isPending ? "Creating..." : "Create Content"}
              </Button>
            </Stack>
          </AdminSection>

          <AdminSection title="Grant Library Access" description="Manually unlock paid or client documents after payment or advisory engagement.">
            {grantAccess.isError && <Alert severity="error">Failed to grant access.</Alert>}
            {grantAccess.isSuccess && <Alert severity="success">Access granted.</Alert>}
            <Stack component="form" gap={2} onSubmit={submitGrant}>
              <TextField label="User ID" value={grantForm.user_id} onChange={(e) => setGrantForm((prev) => ({ ...prev, user_id: e.target.value }))} required />
              <TextField
                select
                label="Content"
                value={grantForm.content_id}
                onChange={(e) => setGrantForm((prev) => ({ ...prev, content_id: e.target.value }))}
                required
              >
                {contentItems.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <TextField
                label="Expiry"
                type="datetime-local"
                value={grantForm.expires_at}
                onChange={(e) => setGrantForm((prev) => ({ ...prev, expires_at: e.target.value }))}
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <Button type="submit" variant="contained" disabled={grantAccess.isPending || contentLoading}>
                {grantAccess.isPending ? "Granting..." : "Grant Access"}
              </Button>
            </Stack>
            <Stack gap={1}>
              <Typography variant="subtitle2">Recent Grants</Typography>
              {accessGrants.slice(0, 5).map((item) => (
                <Typography key={item.id} variant="body2" color="text.secondary">
                  {item.user_id} {"->"} {item.content_id} ({item.is_valid ? "valid" : "expired"})
                </Typography>
              ))}
            </Stack>
          </AdminSection>
        </Box>

        <AdminSection id="content-operations" title="Content Operations" description="Edit existing library content and review recent version history.">
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack component="form" gap={2} onSubmit={submitContentUpdate}>
              {updateContent.isError && <Alert severity="error">Failed to update content.</Alert>}
              {updateContent.isSuccess && <Alert severity="success">Content updated and revision saved.</Alert>}
              <TextField
                select
                label="Content item"
                value={selectedContentId}
                onChange={(event) => setSelectedContentId(event.target.value)}
              >
                {contentItems.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <TextField
                label="Title"
                value={editContentForm.title}
                onChange={(e) => setEditContentForm((prev) => ({ ...prev, title: e.target.value }))}
                required
              />
              <TextField
                label="Summary"
                value={editContentForm.summary}
                onChange={(e) => setEditContentForm((prev) => ({ ...prev, summary: e.target.value }))}
                multiline
                minRows={2}
              />
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  label="Category"
                  value={editContentForm.category}
                  onChange={(e) => setEditContentForm((prev) => ({ ...prev, category: e.target.value }))}
                  required
                  fullWidth
                />
                <TextField
                  label="Version"
                  value={editContentForm.version}
                  onChange={(e) => setEditContentForm((prev) => ({ ...prev, version: e.target.value }))}
                  fullWidth
                />
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  select
                  label="Language"
                  value={editContentForm.language}
                  onChange={(e) => setEditContentForm((prev) => ({ ...prev, language: e.target.value }))}
                  fullWidth
                >
                  {contentLanguages.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  select
                  label="Variant"
                  value={editContentForm.variant_type}
                  onChange={(e) => setEditContentForm((prev) => ({ ...prev, variant_type: e.target.value }))}
                  fullWidth
                >
                  {contentVariantTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  label="Variant group ID"
                  value={editContentForm.variant_group_id}
                  onChange={(e) => setEditContentForm((prev) => ({ ...prev, variant_group_id: e.target.value }))}
                  fullWidth
                />
                <TextField
                  label="Source content ID"
                  value={editContentForm.source_content_id}
                  onChange={(e) => setEditContentForm((prev) => ({ ...prev, source_content_id: e.target.value }))}
                  fullWidth
                />
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  select
                  label="Access"
                  value={editContentForm.access_level}
                  onChange={(e) => setEditContentForm((prev) => ({ ...prev, access_level: e.target.value }))}
                  fullWidth
                >
                  {accessLevels.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  select
                  label="Status"
                  value={editContentForm.status}
                  onChange={(e) => setEditContentForm((prev) => ({ ...prev, status: e.target.value }))}
                  fullWidth
                >
                  {contentWorkflowStatuses.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
              </Stack>
              <TextField
                label="Tags, one per line"
                value={editContentForm.tags}
                onChange={(e) => setEditContentForm((prev) => ({ ...prev, tags: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                label="Body markdown"
                value={editContentForm.body_markdown}
                onChange={(e) => setEditContentForm((prev) => ({ ...prev, body_markdown: e.target.value }))}
                multiline
                minRows={5}
              />
              <TextField
                label="Change note"
                value={editContentForm.change_note}
                onChange={(e) => setEditContentForm((prev) => ({ ...prev, change_note: e.target.value }))}
                required
              />
              <Button type="submit" variant="contained" disabled={!selectedContentId || updateContent.isPending}>
                {updateContent.isPending ? "Updating..." : "Update Content"}
              </Button>
            </Stack>

            <Stack gap={1.5}>
              <Stack component="form" gap={2} onSubmit={submitWorkflowTransition}>
                <Typography variant="h6" fontWeight={700}>Editorial Workflow</Typography>
                {transitionContentWorkflow.isError && <Alert severity="error">Failed to update workflow status.</Alert>}
                {transitionContentWorkflow.isSuccess && <Alert severity="success">Workflow status updated.</Alert>}
                <TextField
                  select
                  label="Workflow status"
                  value={workflowForm.status}
                  onChange={(e) => setWorkflowForm((prev) => ({ ...prev, status: e.target.value }))}
                >
                  {contentWorkflowStatuses.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  label="Review note"
                  value={workflowForm.review_note}
                  onChange={(e) => setWorkflowForm((prev) => ({ ...prev, review_note: e.target.value }))}
                  multiline
                  minRows={3}
                />
                <Button type="submit" variant="contained" disabled={!selectedContentId || transitionContentWorkflow.isPending}>
                  {transitionContentWorkflow.isPending ? "Updating..." : "Update Workflow"}
                </Button>
              </Stack>

              <Typography variant="h6" fontWeight={700}>Recent Revisions</Typography>
              {contentRevisions.length ? (
                contentRevisions.slice(0, 8).map((revision) => (
                  <Paper key={revision.id} variant="outlined" sx={{ p: 1.5 }}>
                    <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                      <Typography fontWeight={700}>Revision {revision.revision_number}</Typography>
                      <Chip size="small" label={revision.status} />
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      v{revision.version} | {revision.change_note || "No change note"}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {revision.created_at ? new Date(revision.created_at).toLocaleString() : "-"}
                    </Typography>
                  </Paper>
                ))
              ) : (
                <Alert severity="info">No revisions are available for this content item yet.</Alert>
              )}
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection id="billing-operations" title="Billing" description="Issue manual invoices and convert paid invoices into content access grants.">
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack component="form" gap={2} onSubmit={submitInvoice}>
              <Typography variant="h6" fontWeight={700}>Create Invoice</Typography>
              {createInvoice.isError && <Alert severity="error">Failed to create invoice.</Alert>}
              {createInvoice.isSuccess && <Alert severity="success">Invoice created.</Alert>}
              <TextField
                label="User ID"
                value={invoiceForm.user_id}
                onChange={(e) => setInvoiceForm((prev) => ({ ...prev, user_id: e.target.value }))}
                required
              />
              <TextField
                select
                label="Invoice type"
                value={invoiceForm.invoice_type}
                onChange={(e) => setInvoiceForm((prev) => ({ ...prev, invoice_type: e.target.value }))}
              >
                {invoiceTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
              </TextField>
              <TextField
                label="Description"
                value={invoiceForm.description}
                onChange={(e) => setInvoiceForm((prev) => ({ ...prev, description: e.target.value }))}
              />
              <TextField
                label="Amount IDR"
                type="number"
                value={invoiceForm.amount_idr}
                onChange={(e) => setInvoiceForm((prev) => ({ ...prev, amount_idr: e.target.value }))}
                required
              />
              <TextField
                select
                label="Content to unlock"
                value={invoiceForm.content_id}
                onChange={(e) => setInvoiceForm((prev) => ({ ...prev, content_id: e.target.value }))}
              >
                <MenuItem value="">None</MenuItem>
                {contentItems.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <TextField
                label="Access expiry"
                type="datetime-local"
                value={invoiceForm.access_expires_at}
                onChange={(e) => setInvoiceForm((prev) => ({ ...prev, access_expires_at: e.target.value }))}
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <TextField
                label="Due date"
                type="datetime-local"
                value={invoiceForm.due_at}
                onChange={(e) => setInvoiceForm((prev) => ({ ...prev, due_at: e.target.value }))}
                slotProps={{ inputLabel: { shrink: true } }}
              />
              <Button type="submit" variant="contained" disabled={createInvoice.isPending}>
                {createInvoice.isPending ? "Creating..." : "Create Invoice"}
              </Button>
            </Stack>

            <Stack gap={2}>
              <Stack component="form" gap={2} onSubmit={submitPaid}>
                <Typography variant="h6" fontWeight={700}>Mark Paid</Typography>
                {markInvoicePaid.isError && <Alert severity="error">Failed to mark invoice paid.</Alert>}
                {markInvoicePaid.isSuccess && <Alert severity="success">Invoice paid and access grants processed.</Alert>}
                <TextField
                  select
                  label="Invoice"
                  value={paidForm.invoice_id}
                  onChange={(e) => setPaidForm((prev) => ({ ...prev, invoice_id: e.target.value }))}
                  required
                >
                  {invoices.map((invoice) => (
                    <MenuItem key={invoice.id} value={invoice.id}>
                      {invoice.invoice_number} - {invoice.user_id} - {formatIdr(invoice.amount_idr)}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  label="Payment reference"
                  value={paidForm.payment_reference}
                  onChange={(e) => setPaidForm((prev) => ({ ...prev, payment_reference: e.target.value }))}
                />
                <TextField
                  label="Access expiry override"
                  type="datetime-local"
                  value={paidForm.access_expires_at}
                  onChange={(e) => setPaidForm((prev) => ({ ...prev, access_expires_at: e.target.value }))}
                  slotProps={{ inputLabel: { shrink: true } }}
                />
                <Button type="submit" variant="contained" disabled={!paidForm.invoice_id || markInvoicePaid.isPending}>
                  {markInvoicePaid.isPending ? "Marking..." : "Mark Paid"}
                </Button>
              </Stack>

              <Stack gap={1}>
                <Typography variant="subtitle2">Recent Invoices</Typography>
                {invoices.slice(0, 5).map((invoice) => (
                  <Paper key={invoice.id} variant="outlined" sx={{ p: 1.5 }}>
                    <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                      <Typography variant="body2">{invoice.invoice_number}</Typography>
                      <Chip size="small" label={invoice.status} />
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      {invoice.user_id} | {formatIdr(invoice.amount_idr)}
                    </Typography>
                  </Paper>
                ))}
              </Stack>
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection id="advisory-operations" title="Advisory Cases" description="Review incoming cases, update workflow status, and keep internal expert notes.">
          {casesLoading ? (
            <CircularProgress />
          ) : (
            <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
              <Stack gap={1.5}>
                {cases.map((item) => (
                  <Paper key={item.id} variant="outlined" sx={{ p: 2 }}>
                    <Stack gap={1}>
                      <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                        <Typography fontWeight={700}>{item.title}</Typography>
                        <Chip size="small" label={item.status} />
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        {item.case_type?.replaceAll("_", " ")} | user {item.user_id}
                      </Typography>
                      <Button size="small" onClick={() => selectCaseForUpdate(item.id)} sx={{ alignSelf: "flex-start" }}>
                        Manage
                      </Button>
                    </Stack>
                  </Paper>
                ))}
                {!cases.length && <Alert severity="info">No advisory cases yet.</Alert>}
              </Stack>

              <Stack component="form" gap={2} onSubmit={submitCaseUpdate}>
                {updateCase.isError && <Alert severity="error">Failed to update advisory case.</Alert>}
                {updateCase.isSuccess && <Alert severity="success">Case updated.</Alert>}
                <TextField
                  select
                  label="Case"
                  value={caseForm.caseId}
                  onChange={(event) => selectCaseForUpdate(event.target.value)}
                  required
                >
                  {cases.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
                </TextField>
                <TextField select label="Status" value={caseForm.status} onChange={(e) => setCaseForm((prev) => ({ ...prev, status: e.target.value }))}>
                  {statusOptions.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  label="Expert notes"
                  value={caseForm.expert_notes}
                  onChange={(e) => setCaseForm((prev) => ({ ...prev, expert_notes: e.target.value }))}
                  multiline
                  minRows={5}
                />
                {selectedCase && (
                  <Alert severity="info">
                    Selected case intake: {JSON.stringify(selectedCase.intake_data || {})}
                  </Alert>
                )}
                <Button type="submit" variant="contained" disabled={!caseForm.caseId || updateCase.isPending}>
                  {updateCase.isPending ? "Updating..." : "Update Case"}
                </Button>
              </Stack>
            </Box>
          )}
        </AdminSection>

        <AdminSection title="Assistant Brief" description="Generate an internal first-pass case brief before writing the advisory report.">
          {assistantBrief.isError && <Alert severity="error">Failed to generate assistant brief.</Alert>}
          {acceptAssistantBrief.isError && <Alert severity="error">Failed to record assistant draft acceptance.</Alert>}
          {createAssistantDraftReport.isError && <Alert severity="error">Failed to create internal draft report.</Alert>}
          {createAssistantDraftReport.isSuccess && <Alert severity="success">Internal draft report created with expert review required.</Alert>}
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack component="form" gap={2} onSubmit={submitAssistantBrief}>
              <TextField
                select
                label="Case"
                value={assistantCaseId}
                onChange={(e) => setAssistantCaseId(e.target.value)}
                required
              >
                {cases.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <Button type="submit" variant="contained" disabled={!assistantCaseId || assistantBrief.isPending}>
                {assistantBrief.isPending ? "Generating..." : "Generate Assistant Brief"}
              </Button>
              <Alert severity="info">
                Internal drafting only. Review assumptions, data gaps, and technical claims before client delivery.
              </Alert>
            </Stack>

            <Stack gap={1.5}>
              {assistantBrief.data ? (
                <>
                  <Typography variant="h6" fontWeight={700}>{assistantBrief.data.draft_report?.title}</Typography>
                  <Typography variant="body2">{assistantBrief.data.draft_report?.executive_summary}</Typography>
                  <Typography variant="subtitle2">Missing Data</Typography>
                  <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
                    {(assistantBrief.data.missing_data || []).map((item) => <Chip key={item} size="small" label={item} />)}
                    {!assistantBrief.data.missing_data?.length && <Chip size="small" color="success" label="No required gaps detected" />}
                  </Stack>
                  <Typography variant="subtitle2">Draft Findings</Typography>
                  <Stack component="ul" sx={{ pl: 2, my: 0 }}>
                    {(assistantBrief.data.draft_report?.key_findings || []).map((item) => (
                      <Typography key={item} component="li" variant="body2">{item}</Typography>
                    ))}
                  </Stack>
                  <Typography variant="subtitle2">Reference Documents</Typography>
                  {(assistantBrief.data.reference_documents || []).map((item) => (
                    <Typography key={item.id || item.source_ref || item.source_id} variant="body2" color="text.secondary">
                      {item.title} ({item.category}, {item.language}){item.source_ref ? ` - ${item.source_ref}` : ""}
                    </Typography>
                  ))}
                  <Typography variant="subtitle2">Document Isolation</Typography>
                  <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
                    <Chip size="small" label={`Files: ${assistantBrief.data.uploaded_file_checks?.total_files || 0}`} />
                    <Chip size="small" color="success" label={`Passed: ${assistantBrief.data.uploaded_file_checks?.passed || 0}`} />
                    {!!assistantBrief.data.uploaded_file_checks?.needs_review && (
                      <Chip size="small" color="warning" label={`Needs review: ${assistantBrief.data.uploaded_file_checks.needs_review}`} />
                    )}
                  </Stack>
                  <Stack direction={{ xs: "column", sm: "row" }} gap={1}>
                    <Button variant="outlined" disabled={acceptAssistantBrief.isPending} onClick={applyAssistantDraft}>
                      {acceptAssistantBrief.isPending ? "Recording..." : "Use Draft In Report Form"}
                    </Button>
                    <Button
                      variant="contained"
                      disabled={createAssistantDraftReport.isPending}
                      onClick={createInternalAssistantDraft}
                    >
                      {createAssistantDraftReport.isPending ? "Creating..." : "Create Internal Draft Report"}
                    </Button>
                  </Stack>
                </>
              ) : (
                <Alert severity="info">Select a case and generate a brief to see draft report sections.</Alert>
              )}
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection title="Controlled Assistant" description="Ask an internal source-cited question against Teramina advisory knowledge.">
          {assistantAnswer.isError && <Alert severity="error">Failed to generate assistant answer.</Alert>}
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack component="form" gap={2} onSubmit={submitAssistantAnswer}>
              <TextField
                select
                label="Case scope"
                value={assistantAnswerForm.case_id}
                onChange={(e) => setAssistantAnswerForm((prev) => ({ ...prev, case_id: e.target.value }))}
              >
                <MenuItem value="">Knowledge only</MenuItem>
                {cases.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <TextField
                id="assistant-question"
                label="Assistant question"
                value={assistantAnswerForm.question}
                onChange={(e) => setAssistantAnswerForm((prev) => ({ ...prev, question: e.target.value }))}
                multiline
                minRows={3}
                slotProps={{ htmlInput: { "data-testid": "assistant-question" } }}
                required
              />
              <Button type="submit" variant="contained" disabled={!assistantAnswerForm.question || assistantAnswer.isPending}>
                {assistantAnswer.isPending ? "Asking..." : "Ask Assistant"}
              </Button>
              <Alert severity="info">
                Internal source-cited drafting only. Do not use for disease diagnosis or client delivery without expert review.
              </Alert>
            </Stack>

            <Stack gap={1.5}>
              {assistantAnswer.data ? (
                <>
                  <Typography variant="h6" fontWeight={700}>{assistantAnswer.data.status}</Typography>
                  <Typography variant="body2">{assistantAnswer.data.answer}</Typography>
                  <Typography variant="subtitle2">Answer Draft</Typography>
                  <Stack component="ul" sx={{ pl: 2, my: 0 }}>
                    {(assistantAnswer.data.answer_bullets || []).map((item) => (
                      <Typography key={item} component="li" variant="body2">{item}</Typography>
                    ))}
                  </Stack>
                  <Typography variant="subtitle2">Citations</Typography>
                  {(assistantAnswer.data.source_citations || []).map((item) => (
                    <Typography key={item.source_ref} variant="body2" color="text.secondary">
                      {item.title} | {item.document_id} | {item.source_snippet}
                    </Typography>
                  ))}
                  {!!assistantAnswer.data.safety_flags?.length && (
                    <Alert severity="warning">{assistantAnswer.data.safety_flags.join(" ")}</Alert>
                  )}
                </>
              ) : (
                <Alert severity="info">Ask a question to generate a controlled source-cited internal answer.</Alert>
              )}
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection title="Expert Review Forms" description="Capture structured technical review notes before or alongside the final advisory report.">
          {createExpertReview.isError && <Alert severity="error">Failed to create expert review.</Alert>}
          {createExpertReview.isSuccess && <Alert severity="success">Expert review created.</Alert>}
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack component="form" gap={2} onSubmit={submitExpertReview}>
              <TextField
                select
                label="Case"
                value={expertReviewForm.case_id}
                onChange={(e) => setExpertReviewForm((prev) => ({ ...prev, case_id: e.target.value }))}
                required
              >
                {cases.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  select
                  label="Review type"
                  value={expertReviewForm.review_type}
                  onChange={(e) => setExpertReviewForm((prev) => ({ ...prev, review_type: e.target.value }))}
                  fullWidth
                >
                  {expertReviewTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  select
                  label="Status"
                  value={expertReviewForm.status}
                  onChange={(e) => setExpertReviewForm((prev) => ({ ...prev, status: e.target.value }))}
                  fullWidth
                >
                  {["draft", "delivered"].map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
              </Stack>
              <TextField
                label="Review summary"
                value={expertReviewForm.summary}
                onChange={(e) => setExpertReviewForm((prev) => ({ ...prev, summary: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                label="Findings, one per line"
                value={expertReviewForm.findings}
                onChange={(e) => setExpertReviewForm((prev) => ({ ...prev, findings: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                label="Recommendations, one per line"
                value={expertReviewForm.recommendations}
                onChange={(e) => setExpertReviewForm((prev) => ({ ...prev, recommendations: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                label="Risk flags, one per line"
                value={expertReviewForm.risk_flags}
                onChange={(e) => setExpertReviewForm((prev) => ({ ...prev, risk_flags: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                label="Next actions, one per line"
                value={expertReviewForm.next_actions}
                onChange={(e) => setExpertReviewForm((prev) => ({ ...prev, next_actions: e.target.value }))}
                multiline
                minRows={3}
              />
              <Button type="submit" variant="contained" disabled={!expertReviewForm.case_id || createExpertReview.isPending}>
                {createExpertReview.isPending ? "Creating..." : "Create Expert Review"}
              </Button>
            </Stack>
            <Stack gap={1}>
              <Typography variant="subtitle2">Recent Expert Reviews</Typography>
              {expertReviews.slice(0, 5).map((review) => (
                <Paper key={review.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2">{review.review_type}</Typography>
                    <Chip size="small" label={review.status} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">{review.case_id}</Typography>
                </Paper>
              ))}
              {!expertReviews.length && <Alert severity="info">No expert reviews yet.</Alert>}
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection title="Retainer Cadence" description="Schedule recurring review rhythm for monthly advisory retainer cases.">
          {createRetainerCadence.isError && <Alert severity="error">Failed to create retainer cadence.</Alert>}
          {createRetainerCadence.isSuccess && <Alert severity="success">Retainer cadence created.</Alert>}
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack component="form" gap={2} onSubmit={submitRetainerCadence}>
              <TextField
                select
                label="Case"
                value={retainerCadenceForm.case_id}
                onChange={(e) => setRetainerCadenceForm((prev) => ({ ...prev, case_id: e.target.value }))}
                required
              >
                {cases.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  select
                  label="Cadence"
                  value={retainerCadenceForm.cadence_type}
                  onChange={(e) => setRetainerCadenceForm((prev) => ({ ...prev, cadence_type: e.target.value }))}
                  fullWidth
                >
                  {retainerCadenceTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  select
                  label="Status"
                  value={retainerCadenceForm.status}
                  onChange={(e) => setRetainerCadenceForm((prev) => ({ ...prev, status: e.target.value }))}
                  fullWidth
                >
                  {retainerCadenceStatuses.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  label="Last review"
                  type="datetime-local"
                  value={retainerCadenceForm.last_review_at}
                  onChange={(e) => setRetainerCadenceForm((prev) => ({ ...prev, last_review_at: e.target.value }))}
                  slotProps={{ inputLabel: { shrink: true } }}
                  fullWidth
                />
                <TextField
                  label="Next review"
                  type="datetime-local"
                  value={retainerCadenceForm.next_review_at}
                  onChange={(e) => setRetainerCadenceForm((prev) => ({ ...prev, next_review_at: e.target.value }))}
                  slotProps={{ inputLabel: { shrink: true } }}
                  fullWidth
                />
              </Stack>
              <TextField
                label="Agenda, one per line"
                value={retainerCadenceForm.agenda}
                onChange={(e) => setRetainerCadenceForm((prev) => ({ ...prev, agenda: e.target.value }))}
                multiline
                minRows={4}
              />
              <TextField
                label="Notes"
                value={retainerCadenceForm.notes}
                onChange={(e) => setRetainerCadenceForm((prev) => ({ ...prev, notes: e.target.value }))}
                multiline
                minRows={3}
              />
              <Button type="submit" variant="contained" disabled={!retainerCadenceForm.case_id || createRetainerCadence.isPending}>
                {createRetainerCadence.isPending ? "Creating..." : "Create Cadence"}
              </Button>
            </Stack>
            <Stack gap={1}>
              <Typography variant="subtitle2">Upcoming Cadences</Typography>
              {retainerCadences.slice(0, 5).map((cadence) => (
                <Paper key={cadence.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2">{cadence.cadence_type}</Typography>
                    <Chip size="small" label={cadence.status} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    Next: {cadence.next_review_at ? new Date(cadence.next_review_at).toLocaleString() : "-"}
                  </Typography>
                </Paper>
              ))}
              {!retainerCadences.length && <Alert severity="info">No retainer cadence records yet.</Alert>}
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection title="Hatchery Intelligence" description="Capture hatchery profiles and operational KPI records for advisory cases.">
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack gap={2}>
              {createHatcheryProfile.isError && <Alert severity="error">Failed to create hatchery profile.</Alert>}
              {createHatcheryProfile.isSuccess && <Alert severity="success">Hatchery profile created.</Alert>}
              {updateHatcheryProfile.isError && <Alert severity="error">Failed to update hatchery profile.</Alert>}
              {updateHatcheryProfile.isSuccess && <Alert severity="success">Hatchery profile updated.</Alert>}
              <Stack component="form" gap={2} onSubmit={submitHatcheryProfile}>
                <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                  <Typography variant="h6" fontWeight={700}>{editingHatcheryProfileId ? "Edit Hatchery Profile" : "Create Hatchery Profile"}</Typography>
                  {editingHatcheryProfileId && <Button size="small" onClick={resetHatcheryProfileEdit}>Cancel Edit</Button>}
                </Stack>
                <TextField
                  select
                  label="Linked case"
                  value={hatcheryProfileForm.case_id}
                  onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, case_id: e.target.value }))}
                  disabled={!!editingHatcheryProfileId}
                >
                  <MenuItem value="">No case</MenuItem>
                  {cases.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
                </TextField>
                <TextField
                  label="Owner user ID"
                  value={hatcheryProfileForm.user_id}
                  onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, user_id: e.target.value }))}
                  helperText="Required only when no case is linked."
                  disabled={!!editingHatcheryProfileId}
                />
                <TextField
                  label="Hatchery name"
                  value={hatcheryProfileForm.name}
                  onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, name: e.target.value }))}
                  required
                />
                <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                  <TextField
                    label="Location"
                    value={hatcheryProfileForm.location}
                    onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, location: e.target.value }))}
                    fullWidth
                  />
                  <TextField
                    label="Biosecurity level"
                    value={hatcheryProfileForm.biosecurity_level}
                    onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, biosecurity_level: e.target.value }))}
                    fullWidth
                  />
                </Stack>
                <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                  <TextField
                    label="Maturation capacity"
                    type="number"
                    value={hatcheryProfileForm.maturation_capacity}
                    onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, maturation_capacity: e.target.value }))}
                    fullWidth
                  />
                  <TextField
                    label="Larval capacity"
                    type="number"
                    value={hatcheryProfileForm.larval_capacity}
                    onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, larval_capacity: e.target.value }))}
                    fullWidth
                  />
                </Stack>
                <TextField
                  label="Water source"
                  value={hatcheryProfileForm.water_source}
                  onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, water_source: e.target.value }))}
                />
                <TextField
                  select
                  label="Client visibility"
                  value={hatcheryProfileForm.client_visible}
                  onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, client_visible: e.target.value }))}
                >
                  <MenuItem value="false">Internal only</MenuItem>
                  <MenuItem value="true">Visible to case owner</MenuItem>
                </TextField>
                <TextField
                  label="Hatchery notes"
                  value={hatcheryProfileForm.notes}
                  onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, notes: e.target.value }))}
                  multiline
                  minRows={3}
                />
                {editingHatcheryProfileId && (
                  <TextField
                    label="Change note"
                    value={hatcheryProfileForm.change_note}
                    onChange={(e) => setHatcheryProfileForm((prev) => ({ ...prev, change_note: e.target.value }))}
                  />
                )}
                <Button
                  type="submit"
                  variant="contained"
                  disabled={!hatcheryProfileForm.name || createHatcheryProfile.isPending || updateHatcheryProfile.isPending}
                >
                  {editingHatcheryProfileId ? "Update Hatchery" : "Create Hatchery"}
                </Button>
              </Stack>

              <Stack component="form" gap={2} onSubmit={submitHatcheryRecord}>
                <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                  <Typography variant="h6" fontWeight={700}>{editingHatcheryRecordId ? "Edit Hatchery Record" : "Add Hatchery Record"}</Typography>
                  {editingHatcheryRecordId && <Button size="small" onClick={resetHatcheryRecordEdit}>Cancel Edit</Button>}
                </Stack>
                {createHatcheryRecord.isError && <Alert severity="error">Failed to create hatchery record.</Alert>}
                {createHatcheryRecord.isSuccess && <Alert severity="success">Hatchery record created.</Alert>}
                {updateHatcheryRecord.isError && <Alert severity="error">Failed to update hatchery record.</Alert>}
                {updateHatcheryRecord.isSuccess && <Alert severity="success">Hatchery record updated.</Alert>}
                <TextField
                  select
                  label="Hatchery"
                  value={hatcheryRecordForm.hatchery_id}
                  onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, hatchery_id: e.target.value }))}
                  required
                  disabled={!!editingHatcheryRecordId}
                >
                  {hatcheries.map((item) => <MenuItem key={item.id} value={item.id}>{item.name}</MenuItem>)}
                </TextField>
                <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                  <TextField
                    select
                    label="Record type"
                    value={hatcheryRecordForm.record_type}
                    onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, record_type: e.target.value }))}
                    fullWidth
                  >
                    {hatcheryRecordTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                  </TextField>
                  <TextField
                    label="Record date"
                    type="datetime-local"
                    value={hatcheryRecordForm.record_date}
                    onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, record_date: e.target.value }))}
                    slotProps={{ inputLabel: { shrink: true } }}
                    fullWidth
                  />
                </Stack>
                <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                  <TextField
                    label="Batch code"
                    value={hatcheryRecordForm.batch_code}
                    onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, batch_code: e.target.value }))}
                    fullWidth
                  />
                  <TextField
                    label="Broodstock source"
                    value={hatcheryRecordForm.broodstock_source}
                    onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, broodstock_source: e.target.value }))}
                    fullWidth
                  />
                </Stack>
                {hatcheryRecordForm.record_type === "broodstock_batch" && (
                  <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                    <TextField
                      label="Female count"
                      type="number"
                      value={hatcheryRecordForm.female_count}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, female_count: e.target.value }))}
                      fullWidth
                    />
                    <TextField
                      label="Male count"
                      type="number"
                      value={hatcheryRecordForm.male_count}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, male_count: e.target.value }))}
                      fullWidth
                    />
                    <TextField
                      label="Mortality count"
                      type="number"
                      value={hatcheryRecordForm.mortality_count}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, mortality_count: e.target.value }))}
                      fullWidth
                    />
                  </Stack>
                )}
                {["maturation_performance", "spawning_log"].includes(hatcheryRecordForm.record_type) && (
                  <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                    <TextField
                      label="Mating rate"
                      type="number"
                      value={hatcheryRecordForm.mating_rate}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, mating_rate: e.target.value }))}
                      fullWidth
                    />
                    <TextField
                      label="Spawning rate"
                      type="number"
                      value={hatcheryRecordForm.spawning_rate}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, spawning_rate: e.target.value }))}
                      fullWidth
                    />
                    <TextField
                      label="Hatching rate"
                      type="number"
                      value={hatcheryRecordForm.hatching_rate}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, hatching_rate: e.target.value }))}
                      fullWidth
                    />
                  </Stack>
                )}
                {hatcheryRecordForm.record_type === "nauplii_output" && (
                  <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                    <TextField
                      label="Nauplii count"
                      type="number"
                      value={hatcheryRecordForm.nauplii_count}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, nauplii_count: e.target.value }))}
                      fullWidth
                    />
                    <TextField
                      label="Hatching rate"
                      type="number"
                      value={hatcheryRecordForm.hatching_rate}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, hatching_rate: e.target.value }))}
                      fullWidth
                    />
                  </Stack>
                )}
                {hatcheryRecordForm.record_type === "pl_quality_test" && (
                  <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                    <TextField
                      label="PL quality score"
                      type="number"
                      value={hatcheryRecordForm.pl_quality_score}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, pl_quality_score: e.target.value }))}
                      fullWidth
                    />
                    <TextField
                      label="PCR status"
                      value={hatcheryRecordForm.pcr_status}
                      onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, pcr_status: e.target.value }))}
                      fullWidth
                    />
                  </Stack>
                )}
                <TextField
                  select
                  label="Record visibility"
                  value={hatcheryRecordForm.client_visible}
                  onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, client_visible: e.target.value }))}
                >
                  <MenuItem value="false">Internal only</MenuItem>
                  <MenuItem value="true">Visible to case owner</MenuItem>
                </TextField>
                <TextField
                  label="Record notes"
                  value={hatcheryRecordForm.notes}
                  onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, notes: e.target.value }))}
                  multiline
                  minRows={3}
                />
                {editingHatcheryRecordId && (
                  <TextField
                    label="Change note"
                    value={hatcheryRecordForm.change_note}
                    onChange={(e) => setHatcheryRecordForm((prev) => ({ ...prev, change_note: e.target.value }))}
                  />
                )}
                <Button
                  type="submit"
                  variant="contained"
                  disabled={!hatcheryRecordForm.hatchery_id || createHatcheryRecord.isPending || updateHatcheryRecord.isPending}
                >
                  {editingHatcheryRecordId ? "Update Hatchery Record" : "Create Hatchery Record"}
                </Button>
              </Stack>
            </Stack>

            <Stack gap={1.5}>
              <Typography variant="subtitle2">Hatchery Profiles</Typography>
              {hatcheries.slice(0, 5).map((hatchery) => (
                <Paper key={hatchery.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2" fontWeight={700}>{hatchery.name}</Typography>
                    <Button size="small" onClick={() => editHatcheryProfile(hatchery)}>Edit Hatchery</Button>
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    {hatchery.location || "-"} | biosecurity: {hatchery.biosecurity_level || "-"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Maturation {hatchery.maturation_capacity || "-"} | larval {hatchery.larval_capacity || "-"}
                  </Typography>
                </Paper>
              ))}
              {!hatcheries.length && <Alert severity="info">No hatchery profiles yet.</Alert>}
              <Typography variant="subtitle2">Recent Hatchery Records</Typography>
              {hatcheryRecords.slice(0, 5).map((record) => (
                <Paper key={record.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2" fontWeight={700}>{record.record_type}</Typography>
                    <Chip size="small" label={record.batch_code || record.hatchery_id} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">{record.notes || "-"}</Typography>
                  <Button size="small" onClick={() => editHatcheryRecord(record)}>Edit Record</Button>
                </Paper>
              ))}
              {!hatcheryRecords.length && <Alert severity="info">No hatchery records yet.</Alert>}
              <Typography variant="subtitle2">Phase 6 Revisions</Typography>
              {phaseSixRevisions.slice(0, 5).map((revision) => (
                <Paper key={revision.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2" fontWeight={700}>{revision.record_kind}</Typography>
                    <Chip size="small" label={`Revision ${revision.revision_number}`} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">{revision.change_note || "Updated record"}</Typography>
                </Paper>
              ))}
              {!phaseSixRevisions.length && <Alert severity="info">No Phase 6 revisions yet.</Alert>}
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection title="Investor Due Diligence" description="Score technical, management, biosecurity, market, and financial risk for investment cases.">
          {createInvestorScore.isError && <Alert severity="error">Failed to create investor score.</Alert>}
          {createInvestorScore.isSuccess && <Alert severity="success">Investor score created.</Alert>}
          {updateInvestorScore.isError && <Alert severity="error">Failed to update investor score.</Alert>}
          {updateInvestorScore.isSuccess && <Alert severity="success">Investor score updated.</Alert>}
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack component="form" gap={2} onSubmit={submitInvestorScore}>
              <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                <Typography variant="h6" fontWeight={700}>{editingInvestorScoreId ? "Edit Investor Score" : "Create Investor Score"}</Typography>
                {editingInvestorScoreId && <Button size="small" onClick={resetInvestorScoreEdit}>Cancel Edit</Button>}
              </Stack>
              <TextField
                select
                label="Investor case"
                value={investorScoreForm.case_id}
                onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, case_id: e.target.value }))}
                required
                disabled={!!editingInvestorScoreId}
              >
                {cases
                  .filter((item) => item.case_type === "investor_due_diligence")
                  .map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  select
                  label="Project type"
                  value={investorScoreForm.project_type}
                  onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, project_type: e.target.value }))}
                  fullWidth
                >
                  {investorProjectTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  label="Location"
                  value={investorScoreForm.location}
                  onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, location: e.target.value }))}
                  fullWidth
                />
              </Stack>
              <TextField
                label="Planned capacity"
                value={investorScoreForm.planned_capacity}
                onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, planned_capacity: e.target.value }))}
              />
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                <TextField
                  label="Capex estimate IDR"
                  type="number"
                  value={investorScoreForm.capex_estimate_idr}
                  onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, capex_estimate_idr: e.target.value }))}
                  fullWidth
                />
                <TextField
                  label="Opex estimate IDR"
                  type="number"
                  value={investorScoreForm.opex_estimate_idr}
                  onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, opex_estimate_idr: e.target.value }))}
                  fullWidth
                />
              </Stack>
              <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
                {["technical_score", "management_score", "biosecurity_score", "market_score", "financial_score"].map((field) => (
                  <TextField
                    key={field}
                    label={field.replace("_", " ")}
                    type="number"
                    value={investorScoreForm[field]}
                    onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, [field]: e.target.value }))}
                    fullWidth
                  />
                ))}
              </Stack>
              <TextField
                label="Red flags, one per line"
                value={investorScoreForm.red_flags}
                onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, red_flags: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                label="Recommendations, one per line"
                value={investorScoreForm.recommendations}
                onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, recommendations: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                label="Assumptions, one per line"
                value={investorScoreForm.assumptions}
                onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, assumptions: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                select
                label="Score visibility"
                value={investorScoreForm.client_visible}
                onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, client_visible: e.target.value }))}
              >
                <MenuItem value="false">Internal only</MenuItem>
                <MenuItem value="true">Visible to case owner</MenuItem>
              </TextField>
              {editingInvestorScoreId && (
                <TextField
                  label="Change note"
                  value={investorScoreForm.change_note}
                  onChange={(e) => setInvestorScoreForm((prev) => ({ ...prev, change_note: e.target.value }))}
                />
              )}
              <Button
                type="submit"
                variant="contained"
                disabled={!investorScoreForm.case_id || createInvestorScore.isPending || updateInvestorScore.isPending}
              >
                {editingInvestorScoreId ? "Update Investor Score" : "Create Investor Score"}
              </Button>
            </Stack>

            <Stack gap={1.5}>
              <Typography variant="subtitle2">Recent Investor Scores</Typography>
              {investorScores.slice(0, 5).map((score) => (
                <Paper key={score.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2" fontWeight={700}>{score.project_type} | {score.location || "-"}</Typography>
                    <Chip size="small" label={`${score.overall_score} / ${score.risk_level}`} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">{score.planned_capacity || "-"}</Typography>
                  {!!score.red_flags?.length && <Typography variant="body2">{score.red_flags[0]}</Typography>}
                  <Stack direction="row" gap={1} sx={{ mt: 1, flexWrap: "wrap" }}>
                    <Chip size="small" variant="outlined" label={score.client_visible ? "client visible" : "internal"} />
                    <Button size="small" onClick={() => editInvestorScore(score)}>Edit Score</Button>
                    <Button size="small" onClick={() => createInvestorDraftReport(score.id)} disabled={createInvestorScoreReport.isPending}>
                      Create DD Report
                    </Button>
                  </Stack>
                </Paper>
              ))}
              {!investorScores.length && <Alert severity="info">No investor due-diligence scores yet.</Alert>}
              {createInvestorScoreReport.isError && <Alert severity="error">Failed to create investor report draft.</Alert>}
              {createInvestorScoreReport.isSuccess && <Alert severity="success">Investor report draft created.</Alert>}
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection title="Phase 6 Benchmarks" description="Aggregate only hatchery and investor records from cases with anonymized benchmark consent.">
          {phaseSixBenchmarks ? (
            <Stack gap={2}>
              <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(5, 1fr)" } }}>
                <TextField
                  select
                  label="Hatchery type"
                  value={phaseSixBenchmarkFilters.record_type}
                  onChange={(e) => setPhaseSixBenchmarkFilters((prev) => ({ ...prev, record_type: e.target.value }))}
                >
                  <MenuItem value="">All</MenuItem>
                  {hatcheryRecordTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  select
                  label="Investor risk"
                  value={phaseSixBenchmarkFilters.risk_level}
                  onChange={(e) => setPhaseSixBenchmarkFilters((prev) => ({ ...prev, risk_level: e.target.value }))}
                >
                  <MenuItem value="">All</MenuItem>
                  {investorRiskLevels.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  select
                  label="Project type"
                  value={phaseSixBenchmarkFilters.project_type}
                  onChange={(e) => setPhaseSixBenchmarkFilters((prev) => ({ ...prev, project_type: e.target.value }))}
                >
                  <MenuItem value="">All</MenuItem>
                  {investorProjectTypes.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  label="From month"
                  type="month"
                  value={phaseSixBenchmarkFilters.from_month}
                  onChange={(e) => setPhaseSixBenchmarkFilters((prev) => ({ ...prev, from_month: e.target.value }))}
                  slotProps={{ inputLabel: { shrink: true } }}
                />
                <TextField
                  label="To month"
                  type="month"
                  value={phaseSixBenchmarkFilters.to_month}
                  onChange={(e) => setPhaseSixBenchmarkFilters((prev) => ({ ...prev, to_month: e.target.value }))}
                  slotProps={{ inputLabel: { shrink: true } }}
                />
              </Box>
              <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(3, 1fr)" } }}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">Filtered source cases</Typography>
                  <Typography variant="h5" fontWeight={700}>{phaseSixBenchmarks.source_case_count || 0}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total consented: {phaseSixBenchmarks.total_consented_case_count ?? phaseSixBenchmarks.source_case_count ?? 0}
                  </Typography>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">Hatchery records</Typography>
                  <Typography variant="h5" fontWeight={700}>{phaseSixBenchmarks.hatchery?.record_count || 0}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg PL score: {phaseSixBenchmarks.hatchery?.average_pl_quality_score ?? "-"}
                  </Typography>
                  <Stack direction="row" gap={0.5} sx={{ mt: 1, flexWrap: "wrap" }}>
                    {Object.entries(phaseSixBenchmarks.hatchery?.record_type_counts || {}).map(([type, count]) => (
                      <Chip key={type} size="small" variant="outlined" label={`${type}: ${count}`} />
                    ))}
                  </Stack>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">Investor scores</Typography>
                  <Typography variant="h5" fontWeight={700}>{phaseSixBenchmarks.investor?.score_count || 0}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg score: {phaseSixBenchmarks.investor?.average_overall_score ?? "-"}
                  </Typography>
                  <Stack direction="row" gap={0.5} sx={{ mt: 1, flexWrap: "wrap" }}>
                    {Object.entries(phaseSixBenchmarks.investor?.risk_level_counts || {}).map(([level, count]) => (
                      <Chip key={level} size="small" variant="outlined" label={`${level}: ${count}`} />
                    ))}
                  </Stack>
                </Paper>
              </Box>
              <Stack gap={1}>
                <Typography variant="subtitle2">Benchmark Trend</Typography>
                {(phaseSixBenchmarks.trend || []).map((item) => (
                  <Paper key={item.month} variant="outlined" sx={{ p: 1.5 }}>
                    <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                      <Typography variant="body2" fontWeight={700}>{item.month}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Hatchery {item.hatchery_record_count} | Investor {item.investor_score_count}
                      </Typography>
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      Avg PL {item.average_pl_quality_score ?? "-"} | Avg DD {item.average_overall_score ?? "-"}
                    </Typography>
                  </Paper>
                ))}
                {!phaseSixBenchmarks.trend?.length && <Alert severity="info">No benchmark trend rows for the selected filters.</Alert>}
              </Stack>
            </Stack>
          ) : (
            <Alert severity="info">No consented Phase 6 benchmark data is available yet.</Alert>
          )}
        </AdminSection>

        <AdminSection title="Deliver Report" description="Create a structured advisory report and mark it delivered when ready for the client.">
          {createReport.isError && <Alert severity="error">Failed to create report.</Alert>}
          {createReport.isSuccess && <Alert severity="success">Report created.</Alert>}
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "1fr 1fr" } }}>
            <Stack component="form" gap={2} onSubmit={submitReport}>
              <Typography variant="h6" fontWeight={700}>Create Report</Typography>
              <TextField
                select
                label="Case"
                value={reportForm.case_id}
                onChange={(e) => setReportForm((prev) => ({ ...prev, case_id: e.target.value }))}
                required
              >
                {cases.map((item) => <MenuItem key={item.id} value={item.id}>{item.title}</MenuItem>)}
              </TextField>
              <TextField
                label="Report title"
                value={reportForm.title}
                onChange={(e) => setReportForm((prev) => ({ ...prev, title: e.target.value }))}
                required
              />
              <TextField
                label="Executive summary"
                value={reportForm.executive_summary}
                onChange={(e) => setReportForm((prev) => ({ ...prev, executive_summary: e.target.value }))}
                multiline
                minRows={3}
              />
              <TextField
                label="Key findings, one per line"
                value={reportForm.key_findings}
                onChange={(e) => setReportForm((prev) => ({ ...prev, key_findings: e.target.value }))}
                multiline
                minRows={4}
              />
              <TextField
                label="Corrective action plan, one per line"
                value={reportForm.corrective_action_plan}
                onChange={(e) => setReportForm((prev) => ({ ...prev, corrective_action_plan: e.target.value }))}
                multiline
                minRows={4}
              />
              <TextField
                label="Report file URL"
                value={reportForm.file_url}
                onChange={(e) => setReportForm((prev) => ({ ...prev, file_url: e.target.value }))}
              />
              <TextField select label="Status" value={reportForm.status} onChange={(e) => setReportForm((prev) => ({ ...prev, status: e.target.value }))}>
                {reportStatuses.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
              </TextField>
              <Button type="submit" variant="contained" disabled={!reportForm.case_id || createReport.isPending}>
                {createReport.isPending ? "Creating..." : "Create Report"}
              </Button>
            </Stack>

            <Stack gap={2}>
              <Stack component="form" gap={2} onSubmit={submitReportWorkflow}>
                <Typography variant="h6" fontWeight={700}>Review Draft Report</Typography>
                {updateReportWorkflow.isError && <Alert severity="error">Failed to update report workflow.</Alert>}
                {updateReportWorkflow.isSuccess && <Alert severity="success">Report workflow updated.</Alert>}
                <TextField
                  select
                  label="Report"
                  value={reportWorkflowForm.report_id}
                  onChange={(e) => setReportWorkflowForm((prev) => ({ ...prev, report_id: e.target.value }))}
                  required
                >
                  {adminReports.map((item) => (
                    <MenuItem key={item.id} value={item.id}>
                      {item.title} - {item.status}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  select
                  label="Workflow status"
                  value={reportWorkflowForm.status}
                  onChange={(e) => setReportWorkflowForm((prev) => ({ ...prev, status: e.target.value }))}
                >
                  {reportStatuses.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                </TextField>
                <TextField
                  label="Review note"
                  value={reportWorkflowForm.review_note}
                  onChange={(e) => setReportWorkflowForm((prev) => ({ ...prev, review_note: e.target.value }))}
                  multiline
                  minRows={3}
                />
                <Button type="submit" variant="contained" disabled={!reportWorkflowForm.report_id || updateReportWorkflow.isPending}>
                  {updateReportWorkflow.isPending ? "Updating..." : "Update Report Workflow"}
                </Button>
              </Stack>

              <Stack gap={1}>
                <Typography variant="subtitle2">Recent Reports</Typography>
                {adminReports.slice(0, 5).map((report) => (
                  <Paper key={report.id} variant="outlined" sx={{ p: 1.5 }}>
                    <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                      <Typography variant="body2">{report.title}</Typography>
                      <Chip size="small" label={report.status} />
                    </Stack>
                    <Typography variant="body2" color="text.secondary">{report.case_id}</Typography>
                  </Paper>
                ))}
                {!adminReports.length && <Alert severity="info">No advisory reports yet.</Alert>}
              </Stack>
            </Stack>
          </Box>
        </AdminSection>

        <AdminSection id="audit-trail" title="Advisory Audit Trail" description="Browse assistant usage and report workflow events for operator review.">
          <Box sx={{ display: "grid", gap: 3, gridTemplateColumns: { xs: "1fr", lg: "repeat(3, 1fr)" } }}>
            <Stack gap={1.5}>
              <Typography variant="h6" fontWeight={700}>Assistant Brief Logs</Typography>
              {assistantBriefLogs.slice(0, 6).map((log) => (
                <Paper key={log.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2" fontWeight={700}>{log.draft_report?.title || log.case_id}</Typography>
                    <Chip size="small" label={log.status} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    Case {log.case_id} | generated by {log.generated_by || "-"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sources: {(log.source_citations || []).length} | accepted report: {log.accepted_report_id || "-"}
                  </Typography>
                </Paper>
              ))}
              {!assistantBriefLogs.length && <Alert severity="info">No assistant brief logs yet.</Alert>}
            </Stack>

            <Stack gap={1.5}>
              <Typography variant="h6" fontWeight={700}>Assistant Answer Logs</Typography>
              {assistantAnswerLogs.slice(0, 6).map((log) => (
                <Paper key={log.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2" fontWeight={700}>{log.question}</Typography>
                    <Chip size="small" label={log.status} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    Case {log.case_id || "global"} | asked by {log.asked_by || "-"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sources: {(log.source_citations || []).length} | safety flags: {(log.safety_flags || []).length}
                  </Typography>
                </Paper>
              ))}
              {!assistantAnswerLogs.length && <Alert severity="info">No assistant answer logs yet.</Alert>}
            </Stack>

            <Stack gap={1.5}>
              <Typography variant="h6" fontWeight={700}>Report Workflow History</Typography>
              {reportWorkflowEvents.slice(0, 6).map((event) => (
                <Paper key={event.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography variant="body2" fontWeight={700}>{event.report_id}</Typography>
                    <Chip size="small" label={`${event.previous_status || "new"} -> ${event.new_status}`} />
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    Case {event.case_id} | changed by {event.changed_by || "-"}
                  </Typography>
                  {event.review_note && <Typography variant="body2">{event.review_note}</Typography>}
                </Paper>
              ))}
              {!reportWorkflowEvents.length && <Alert severity="info">No report workflow history yet.</Alert>}
            </Stack>
          </Box>
        </AdminSection>
      </Stack>
    </Container>
  );
};

export default CommercialAdminPage;
