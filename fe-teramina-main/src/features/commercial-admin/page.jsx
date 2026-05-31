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
import { useUserProfile } from "features/user/queries";
import {
  useAcceptAdvisoryAssistantBrief,
  useAdminAdvisoryCases,
  useAdminExpertReviews,
  useGenerateAdvisoryAssistantBrief,
  useCreateAdvisoryReport,
  useCreateExpertReview,
  useCreateReportFromAdvisoryAssistantBrief,
  useCreateRetainerCadence,
  useAdminAdvisoryReports,
  useAdminRetainerCadences,
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
const formatIdr = (value) => `Rp ${Number(value || 0).toLocaleString("id-ID")}`;

const AdminSection = ({ title, description, children }) => (
  <Paper variant="outlined" sx={{ p: 3 }}>
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
  const { data: expertReviews = [] } = useAdminExpertReviews(isAdmin);
  const { data: retainerCadences = [] } = useAdminRetainerCadences(isAdmin);
  const { data: invoices = [] } = useAdminInvoices(isAdmin);
  const createContent = useCreateContentItem();
  const [selectedContentId, setSelectedContentId] = useState("");
  const { data: selectedContent } = useAdminContentItem(selectedContentId, isAdmin);
  const { data: contentRevisions = [] } = useAdminContentRevisions(selectedContentId, isAdmin);
  const grantAccess = useGrantContentAccess();
  const updateContent = useUpdateContentItem();
  const transitionContentWorkflow = useTransitionContentWorkflow();
  const updateCase = useUpdateAdvisoryCase();
  const assistantBrief = useGenerateAdvisoryAssistantBrief();
  const acceptAssistantBrief = useAcceptAdvisoryAssistantBrief();
  const createAssistantDraftReport = useCreateReportFromAdvisoryAssistantBrief();
  const createReport = useCreateAdvisoryReport();
  const updateReportWorkflow = useUpdateAdvisoryReportWorkflow();
  const createExpertReview = useCreateExpertReview();
  const createRetainerCadence = useCreateRetainerCadence();
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
      payload: { status: caseForm.status, expert_notes: caseForm.expert_notes },
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

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Stack gap={3}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Commercial Admin</Typography>
          <Typography color="text.secondary">
            Operate paid library access and advisory delivery before automated payment and CMS flows are introduced.
          </Typography>
        </Box>

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

        <AdminSection title="Content Operations" description="Edit existing library content and review recent version history.">
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

        <AdminSection title="Billing" description="Issue manual invoices and convert paid invoices into content access grants.">
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

        <AdminSection title="Advisory Cases" description="Review incoming cases, update workflow status, and keep internal expert notes.">
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
      </Stack>
    </Container>
  );
};

export default CommercialAdminPage;
