import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import {
  useAcceptBenchmarkConsent,
  useAddAdvisoryCaseFile,
  useAdvisoryCase,
  useAdvisoryCases,
  useRevokeBenchmarkConsent,
  useServicePackages,
} from "./queries";
import { servicePackageFallbacks } from "./catalog";

const formatLabel = (key) =>
  key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const IntakeSummary = ({ data = {} }) => {
  const hiddenKeys = ["schema_version", "service_slug", "service_name", "case_type"];
  const entries = Object.entries(data).filter(([key, value]) => !hiddenKeys.includes(key) && value);

  if (!entries.length) {
    return <Typography color="text.secondary">No structured intake data was submitted.</Typography>;
  }

  return (
    <Stack gap={1}>
      {entries.map(([key, value]) => (
        <Box key={key}>
          <Typography variant="caption" color="text.secondary">{formatLabel(key)}</Typography>
          <Typography sx={{ whiteSpace: "pre-wrap" }}>{String(value)}</Typography>
        </Box>
      ))}
    </Stack>
  );
};

const ReportList = ({ title, items = [] }) => {
  if (!items.length) return null;
  return (
    <Box>
      <Typography variant="subtitle2">{title}</Typography>
      <Stack component="ul" sx={{ pl: 2, my: 0.5 }}>
        {items.map((item) => (
          <Typography component="li" key={item} variant="body2">{item}</Typography>
        ))}
      </Stack>
    </Box>
  );
};

const FileList = ({ files = [] }) => {
  if (!files.length) return null;
  return (
    <Box>
      <Typography variant="h6" sx={{ mt: 1 }}>Private Files</Typography>
      <Stack gap={1}>
        {files.map((file) => (
          <Paper key={`${file.url}-${file.name}`} variant="outlined" sx={{ p: 1.5 }}>
            <Stack direction={{ xs: "column", sm: "row" }} gap={1} sx={{ justifyContent: "space-between" }}>
              <Box>
                <Typography fontWeight={700}>{file.name}</Typography>
                {file.description && <Typography variant="body2" color="text.secondary">{file.description}</Typography>}
              </Box>
              <Button href={file.url} target="_blank" rel="noreferrer">Open</Button>
            </Stack>
          </Paper>
        ))}
      </Stack>
    </Box>
  );
};

const ExpertReviewList = ({ reviews = [] }) => {
  if (!reviews.length) return null;
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack gap={1.5}>
        <Typography variant="h5" fontWeight={700}>Expert Reviews</Typography>
        {reviews.map((review) => (
          <Box key={review.id}>
            <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
              <Chip size="small" label={review.review_type} />
              <Chip size="small" variant="outlined" label={review.status} />
            </Stack>
            <Typography sx={{ mt: 1 }}>{review.summary}</Typography>
            <ReportList title="Findings" items={review.findings || []} />
            <ReportList title="Recommendations" items={review.recommendations || []} />
            <ReportList title="Next actions" items={review.next_actions || []} />
          </Box>
        ))}
      </Stack>
    </Paper>
  );
};

const RetainerCadenceList = ({ cadences = [] }) => {
  if (!cadences.length) return null;
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack gap={1.5}>
        <Typography variant="h5" fontWeight={700}>Retainer Cadence</Typography>
        {cadences.map((cadence) => (
          <Box key={cadence.id}>
            <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
              <Chip size="small" label={cadence.cadence_type} />
              <Chip size="small" variant="outlined" label={cadence.status} />
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Next review: {cadence.next_review_at ? new Date(cadence.next_review_at).toLocaleString() : "-"}
            </Typography>
            <ReportList title="Agenda" items={cadence.agenda || []} />
            {cadence.notes && <Typography sx={{ whiteSpace: "pre-wrap" }}>{cadence.notes}</Typography>}
          </Box>
        ))}
      </Stack>
    </Paper>
  );
};

const HatcheryIntelligenceList = ({ profiles = [], records = [] }) => {
  if (!profiles.length && !records.length) return null;
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack gap={1.5}>
        <Typography variant="h5" fontWeight={700}>Hatchery Intelligence</Typography>
        {profiles.map((profile) => (
          <Box key={profile.id}>
            <Typography fontWeight={700}>{profile.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {profile.location || "-"} | biosecurity: {profile.biosecurity_level || "-"}
            </Typography>
            {profile.notes && <Typography sx={{ whiteSpace: "pre-wrap" }}>{profile.notes}</Typography>}
          </Box>
        ))}
        {!!records.length && <Typography variant="subtitle2">Operational Records</Typography>}
        {records.map((record) => (
          <Box key={record.id}>
            <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
              <Chip size="small" label={record.record_type} />
              {record.batch_code && <Chip size="small" variant="outlined" label={record.batch_code} />}
            </Stack>
            <Stack gap={0.5} sx={{ mt: 1 }}>
              {Object.entries(record.metrics || {}).map(([key, value]) => (
                <Typography key={key} variant="body2">
                  {formatLabel(key)}: {String(value)}
                </Typography>
              ))}
            </Stack>
            {record.notes && <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{record.notes}</Typography>}
          </Box>
        ))}
      </Stack>
    </Paper>
  );
};

const InvestorScoreList = ({ scores = [] }) => {
  if (!scores.length) return null;
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack gap={1.5}>
        <Typography variant="h5" fontWeight={700}>Investor Due Diligence</Typography>
        {scores.map((score) => (
          <Box key={score.id}>
            <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
              <Chip size="small" label={`${score.overall_score} overall`} />
              <Chip size="small" variant="outlined" label={`${score.risk_level} risk`} />
              <Chip size="small" variant="outlined" label={score.project_type} />
            </Stack>
            <Typography sx={{ mt: 1 }}>{score.location || "-"} | {score.planned_capacity || "-"}</Typography>
            <ReportList title="Red flags" items={score.red_flags || []} />
            <ReportList title="Recommendations" items={score.recommendations || []} />
          </Box>
        ))}
      </Stack>
    </Paper>
  );
};

const CitationList = ({ citations = [] }) => {
  if (!citations.length) return null;
  return (
    <Stack gap={1}>
      <Typography variant="subtitle2">Source Citations</Typography>
      {citations.map((citation) => (
        <Box key={citation.source_ref || citation.document_id || citation.title} sx={{ pl: 1.5, borderLeft: 2, borderColor: "divider" }}>
          <Typography variant="body2" fontWeight={700}>{citation.title || citation.document_id || "Teramina source"}</Typography>
          <Typography variant="caption" color="text.secondary">
            {citation.document_id || citation.source_id || "-"} | {citation.access_scope || "source cited"}
          </Typography>
          {(citation.source_snippet || citation.snippet) && (
            <Typography variant="body2" color="text.secondary">{citation.source_snippet || citation.snippet}</Typography>
          )}
        </Box>
      ))}
    </Stack>
  );
};

const ClientAssistantPreview = ({ citations = [] }) => (
  <Paper variant="outlined" sx={{ p: 3 }}>
    <Stack gap={1.5}>
      <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
        <Typography variant="h5" fontWeight={700}>Ask Teramina Assistant</Typography>
        <Chip size="small" label="disabled" />
      </Stack>
      <Alert severity="info">Client-facing assistant access is not enabled for this case.</Alert>
      <CitationList citations={citations} />
    </Stack>
  </Paper>
);

const BenchmarkConsentPanel = ({ caseId, consent }) => {
  const acceptConsent = useAcceptBenchmarkConsent();
  const revokeConsent = useRevokeBenchmarkConsent();
  if (!consent) return null;
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack gap={1.5}>
        <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", flexWrap: "wrap" }}>
          <Typography variant="h5" fontWeight={700}>Benchmark Consent</Typography>
          <Chip size="small" color={consent.active ? "success" : "default"} label={consent.active ? "active" : "not active"} />
        </Stack>
        <Typography variant="body2" color="text.secondary">{consent.terms_text}</Typography>
        {acceptConsent.isError && <Alert severity="error">Failed to accept benchmark consent.</Alert>}
        {revokeConsent.isError && <Alert severity="error">Failed to revoke benchmark consent.</Alert>}
        <Stack direction={{ xs: "column", sm: "row" }} gap={1}>
          <Button
            variant="contained"
            disabled={consent.active || acceptConsent.isPending}
            onClick={() => acceptConsent.mutate(caseId)}
          >
            {acceptConsent.isPending ? "Accepting..." : "Accept Benchmark Terms"}
          </Button>
          <Button
            variant="outlined"
            disabled={!consent.active || revokeConsent.isPending}
            onClick={() => revokeConsent.mutate(caseId)}
          >
            {revokeConsent.isPending ? "Revoking..." : "Revoke Consent"}
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
};

export const DashboardAdvisoryPage = () => {
  const { data = [], isLoading, isError } = useAdvisoryCases();

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Stack direction={{ xs: "column", md: "row" }} gap={2} sx={{ mb: 3, justifyContent: "space-between" }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Advisory</Typography>
          <Typography color="text.secondary">Track technical reviews, submitted intake, and delivered reports.</Typography>
        </Box>
        <Button component={Link} to="/dashboard/advisory/new" variant="contained">New Advisory Case</Button>
      </Stack>
      {isError && <Alert severity="error">Failed to load advisory cases.</Alert>}
      {isLoading ? (
        <CircularProgress />
      ) : data.length ? (
        <Stack gap={2}>
          {data.map((item) => (
            <Paper key={item.id} variant="outlined" sx={{ p: 2 }}>
              <Stack direction={{ xs: "column", md: "row" }} gap={1} sx={{ justifyContent: "space-between" }}>
                <Box>
                  <Typography variant="h6" fontWeight={700}>{item.title}</Typography>
                  <Typography color="text.secondary">{item.case_type?.replaceAll("_", " ")}</Typography>
                </Box>
                <Stack direction="row" gap={1} sx={{ alignItems: "center" }}>
                  <Chip label={item.status} />
                  <Button component={Link} to={`/dashboard/advisory/${item.id}`}>Open</Button>
                </Stack>
              </Stack>
            </Paper>
          ))}
        </Stack>
      ) : (
        <Alert severity="info">No advisory cases submitted yet.</Alert>
      )}
    </Container>
  );
};

export const DashboardAdvisoryNewPage = () => {
  const { data = [], isLoading, isError } = useServicePackages();
  const packages = data.length ? data : servicePackageFallbacks;

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Stack gap={2} sx={{ mb: 3 }}>
        <Button component={Link} to="/dashboard/advisory" sx={{ alignSelf: "flex-start" }}>Back to Advisory</Button>
        <Typography variant="h4" fontWeight={700}>New Advisory Case</Typography>
        <Typography color="text.secondary">
          Select the review package that best matches the decision or problem you want Teramina to analyze.
        </Typography>
        {isError && <Alert severity="info">Showing starter service packages while the advisory API is unavailable.</Alert>}
      </Stack>

      {isLoading ? (
        <CircularProgress />
      ) : (
        <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" } }}>
          {packages.map((pkg) => (
            <Paper key={pkg.slug} variant="outlined" sx={{ p: 2.5 }}>
              <Stack gap={1.25}>
                <Stack direction="row" gap={1} sx={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                  <Typography variant="h5" fontWeight={700}>{pkg.name}</Typography>
                  <Chip size="small" label={pkg.segment} />
                </Stack>
                <Typography color="text.secondary">{pkg.description}</Typography>
                <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
                  {(pkg.deliverables || []).slice(0, 3).map((item) => <Chip key={item} size="small" variant="outlined" label={item} />)}
                </Stack>
                <Button component={Link} to={`/advisory/intake/${pkg.slug}`} variant="contained" sx={{ alignSelf: "flex-start" }}>
                  Start Intake
                </Button>
              </Stack>
            </Paper>
          ))}
        </Box>
      )}
    </Container>
  );
};

export const DashboardAdvisoryDetailPage = () => {
  const { case_id = "" } = useParams();
  const { data, isLoading, isError } = useAdvisoryCase(case_id);
  const addFile = useAddAdvisoryCaseFile();
  const [fileForm, setFileForm] = useState({
    name: "",
    url: "",
    content_type: "",
    description: "",
  });
  const item = data?.case;
  const report = data?.report;
  const expertReviews = data?.expert_reviews || [];
  const retainerCadences = data?.retainer_cadences || [];
  const hatcheryProfiles = data?.hatchery_profiles || [];
  const hatcheryRecords = data?.hatchery_records || [];
  const investorScores = data?.investor_scores || [];
  const benchmarkConsent = data?.benchmark_consent;
  const submitFile = async (event) => {
    event.preventDefault();
    await addFile.mutateAsync({ caseId: case_id, payload: fileForm });
    setFileForm({ name: "", url: "", content_type: "", description: "" });
  };

  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      <Stack gap={2}>
        <Button component={Link} to="/dashboard/advisory" sx={{ alignSelf: "flex-start" }}>Back to Advisory</Button>
        {isLoading && <CircularProgress />}
        {isError && <Alert severity="error">Failed to load advisory case.</Alert>}
        {item && (
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Stack gap={1.5}>
              <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
                <Chip label={item.status} />
                <Chip variant="outlined" label={item.case_type?.replaceAll("_", " ")} />
              </Stack>
              <Typography variant="h4" fontWeight={700}>{item.title}</Typography>
              <Typography color="text.secondary">Submitted {item.created_at ? new Date(item.created_at).toLocaleString() : "-"}</Typography>
              <Typography variant="h6" sx={{ mt: 1 }}>Intake</Typography>
              <IntakeSummary data={item.intake_data} />
              <FileList files={item.uploaded_files || []} />
              <Stack component="form" gap={1.5} onSubmit={submitFile}>
                <Typography variant="h6">Attach Private File</Typography>
                {addFile.isError && <Alert severity="error">Failed to attach file reference.</Alert>}
                {addFile.isSuccess && <Alert severity="success">File reference attached.</Alert>}
                <TextField
                  label="File name"
                  value={fileForm.name}
                  onChange={(e) => setFileForm((prev) => ({ ...prev, name: e.target.value }))}
                  required
                />
                <TextField
                  label="Private file URL"
                  value={fileForm.url}
                  onChange={(e) => setFileForm((prev) => ({ ...prev, url: e.target.value }))}
                  required
                />
                <TextField
                  label="Description"
                  value={fileForm.description}
                  onChange={(e) => setFileForm((prev) => ({ ...prev, description: e.target.value }))}
                  multiline
                  minRows={2}
                />
                <Button type="submit" variant="outlined" disabled={addFile.isPending}>
                  {addFile.isPending ? "Attaching..." : "Attach File"}
                </Button>
              </Stack>
            </Stack>
          </Paper>
        )}
        <ExpertReviewList reviews={expertReviews} />
        <RetainerCadenceList cadences={retainerCadences} />
        <HatcheryIntelligenceList profiles={hatcheryProfiles} records={hatcheryRecords} />
        <InvestorScoreList scores={investorScores} />
        <BenchmarkConsentPanel caseId={case_id} consent={benchmarkConsent} />
        {report ? (
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Stack gap={1.5}>
              <Typography variant="h5" fontWeight={700}>{report.title}</Typography>
              <Typography>{report.executive_summary}</Typography>
              <ReportList title="Key findings" items={report.key_findings || []} />
              <ReportList title="Corrective action plan" items={report.corrective_action_plan || []} />
              <CitationList citations={report.source_citations || []} />
              {report.file_url && <Button href={report.file_url} target="_blank" rel="noreferrer" variant="contained">Open Report</Button>}
            </Stack>
          </Paper>
        ) : item ? (
          <Alert severity="info">No advisory report has been delivered for this case yet.</Alert>
        ) : null}
        {item && <ClientAssistantPreview citations={report?.source_citations || []} />}
      </Stack>
    </Container>
  );
};
