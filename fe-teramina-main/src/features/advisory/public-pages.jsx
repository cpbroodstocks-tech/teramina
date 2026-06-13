import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
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
import { useCreateAdvisoryCase, useServicePackage, useServicePackages } from "./queries";
import { caseTypeByServiceSlug, servicePackageFallbacks } from "./catalog";
import { useFarmHierarchy } from "features/farm/queries";

const formatPrice = (min, max) => {
  if (!min && !max) return "Custom scope";
  const fmt = (value) => `Rp ${Number(value).toLocaleString("id-ID")}`;
  if (min && max) return `${fmt(min)} - ${fmt(max)}`;
  return fmt(min || max);
};

const commonLinkedFields = [
  { key: "farm_id", label: "Farm ID" },
  { key: "pond_id", label: "Pond ID" },
  { key: "cycle_id", label: "Cycle ID" },
];

const genericIntakeFields = [
  { key: "profile", label: "Farm, hatchery, or project profile", required: true, minRows: 3 },
  { key: "main_problem", label: "Main problem or decision", required: true, minRows: 3 },
  { key: "available_data", label: "Available data", minRows: 3 },
];

const intakeFieldsByCaseType = {
  farm_diagnostic: [
    ...commonLinkedFields,
    { key: "farm_name_location", label: "Farm name and location", required: true },
    { key: "stocking_date", label: "Stocking date" },
    { key: "pond_size", label: "Pond size" },
    { key: "stocking_density", label: "Stocking density" },
    { key: "pl_source", label: "PL source" },
    { key: "water_source", label: "Water source" },
    { key: "feed_data_summary", label: "Feed data summary", minRows: 3 },
    { key: "water_quality_summary", label: "Water quality summary", minRows: 3 },
    { key: "mortality_timeline", label: "Mortality timeline", minRows: 3 },
    { key: "disease_test_results", label: "Disease test results", minRows: 3 },
    { key: "harvest_result", label: "Harvest result if available", minRows: 2 },
    { key: "main_question", label: "Main question or problem", required: true, minRows: 3 },
  ],
  crop_planning: [
    ...commonLinkedFields,
    { key: "farm_pond_details", label: "Farm and pond details", required: true, minRows: 3 },
    { key: "planned_stocking_date", label: "Planned stocking date" },
    { key: "pond_size_depth", label: "Pond size and depth" },
    { key: "target_density", label: "Target density" },
    { key: "pl_source", label: "PL source" },
    { key: "target_size_doc", label: "Target size and DOC" },
    { key: "survival_fcr_assumptions", label: "Expected survival and FCR assumptions", minRows: 3 },
    { key: "cost_assumptions", label: "Feed, electricity, and labor cost assumptions", minRows: 3 },
    { key: "market_price_assumptions", label: "Market price assumptions", minRows: 3 },
    { key: "main_planning_concern", label: "Main planning concern", required: true, minRows: 3 },
  ],
  hatchery_review: [
    { key: "hatchery_name_location", label: "Hatchery name and location", required: true },
    { key: "broodstock_source", label: "Broodstock source" },
    { key: "quarantine_acclimation_summary", label: "Quarantine and acclimation summary", minRows: 3 },
    { key: "ablation_timing", label: "Ablation timing" },
    { key: "mating_rate", label: "Mating rate" },
    { key: "spawning_rate", label: "Spawning rate" },
    { key: "nauplii_per_spawn", label: "Nauplii per spawn" },
    { key: "hatching_rate", label: "Hatching rate" },
    { key: "larval_survival", label: "Larval survival" },
    { key: "pl_quality_testing_notes", label: "PL quality and testing notes", minRows: 3 },
    { key: "main_performance_concern", label: "Main performance concern", required: true, minRows: 3 },
  ],
  investor_due_diligence: [
    {
      key: "project_type",
      label: "Project type",
      required: true,
      options: ["farm", "hatchery", "integrated"],
    },
    { key: "location", label: "Location", required: true },
    { key: "planned_capacity", label: "Planned capacity" },
    { key: "capex_estimate", label: "Capex estimate" },
    { key: "opex_estimate", label: "Opex estimate" },
    { key: "management_team_background", label: "Management or team background", minRows: 3 },
    { key: "technical_assumptions", label: "Technical assumptions", minRows: 3 },
    { key: "target_roi_payback", label: "Target ROI or payback" },
    { key: "documents_available", label: "Documents available", minRows: 3 },
    { key: "main_investment_question", label: "Main investment question", required: true, minRows: 3 },
  ],
  procurement_advisory: [
    { key: "buyer_profile", label: "Buyer profile", required: true, minRows: 3 },
    { key: "material_needed", label: "Broodstock or PL material needed" },
    { key: "target_supplier_options", label: "Target supplier options", minRows: 3 },
    { key: "genetic_trait_priority", label: "Genetic trait priority" },
    { key: "biosecurity_requirements", label: "Biosecurity requirements", minRows: 3 },
    { key: "procurement_timeline", label: "Procurement timeline" },
    { key: "main_procurement_question", label: "Main procurement question", required: true, minRows: 3 },
  ],
  retainer: [
    { key: "organization_profile", label: "Organization profile", required: true, minRows: 3 },
    { key: "sites_scope", label: "Sites or scope to support", minRows: 3 },
    { key: "support_cadence", label: "Expected support cadence" },
    { key: "active_problem", label: "Active problem or management priority", required: true, minRows: 3 },
    { key: "data_available", label: "Data available", minRows: 3 },
    { key: "monthly_goals", label: "Monthly goals", minRows: 3 },
  ],
};

const buildInitialForm = (servicePackage) => ({
  title: servicePackage?.name || "Advisory Review",
  farm_id: localStorage.getItem("farm_id") || "",
  pond_id: localStorage.getItem("pond_id") || "",
  cycle_id: localStorage.getItem("cycle_id") || "",
});

export const ServicesPage = () => {
  const { data = [], isLoading, isError } = useServicePackages();
  const packages = data.length ? data : servicePackageFallbacks;

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Stack gap={2} sx={{ mb: 4 }}>
        <Typography variant="h3" fontWeight={700}>Shrimp Aquaculture Operating Intelligence</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 760 }}>
          Technical reviews, decision tools, and structured reports for shrimp farms, hatcheries, investors, and aquaculture businesses.
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
                <Typography fontWeight={700}>{formatPrice(pkg.price_min_idr, pkg.price_max_idr)}</Typography>
                <Stack direction="row" gap={1} sx={{ flexWrap: "wrap" }}>
                  {(pkg.deliverables || []).slice(0, 3).map((item) => <Chip key={item} size="small" variant="outlined" label={item} />)}
                </Stack>
                <Button component={Link} to={`/advisory/intake/${pkg.slug}`} variant="contained" sx={{ alignSelf: "flex-start" }}>
                  Request Review
                </Button>
              </Stack>
            </Paper>
          ))}
        </Box>
      )}
    </Container>
  );
};

export const AdvisoryIntakePage = () => {
  const { service_slug = "" } = useParams();
  const { data: apiPackage } = useServicePackage(service_slug);
  const fallbackPackage = servicePackageFallbacks.find((pkg) => pkg.slug === service_slug) || servicePackageFallbacks[0];
  const servicePackage = apiPackage || fallbackPackage;
  const token = localStorage.getItem("authentication");
  const { data: farms = [] } = useFarmHierarchy(false, !!token);
  const [submittedCase, setSubmittedCase] = useState(null);
  const [form, setForm] = useState(() => buildInitialForm(servicePackage));
  const { mutateAsync, isPending, isError } = useCreateAdvisoryCase();

  const caseType = useMemo(
    () => caseTypeByServiceSlug[service_slug] || "farm_diagnostic",
    [service_slug],
  );
  const intakeFields = intakeFieldsByCaseType[caseType] || genericIntakeFields;
  const selectedFarm = farms.find((item) => item.id === form.farm_id);
  const ponds = selectedFarm?.ponds || [];
  const selectedPond = ponds.find((item) => item.id === form.pond_id);
  const cycles = selectedPond?.cycles || [];
  const hasLinkedContext = intakeFields.some((field) => field.key === "farm_id");

  const update = (key) => (event) => setForm((prev) => ({ ...prev, [key]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    const intakeData = intakeFields.reduce(
      (payload, field) => ({ ...payload, [field.key]: form[field.key] || "" }),
      {
        schema_version: "v1",
        service_slug,
        service_name: servicePackage?.name || "",
        case_type: caseType,
      },
    );
    const created = await mutateAsync({
      service_package_id: apiPackage?.id || "",
      case_type: caseType,
      farm_id: form.farm_id,
      pond_id: form.pond_id,
      cycle_id: form.cycle_id,
      title: form.title,
      intake_data: intakeData,
      uploaded_files: [],
    });
    setSubmittedCase(created);
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Stack gap={2} sx={{ mb: 3 }}>
        <Button component={Link} to="/services" sx={{ alignSelf: "flex-start" }}>Back to Services</Button>
        <Typography variant="h3" fontWeight={700}>{servicePackage?.name || "Advisory Intake"}</Typography>
        <Typography color="text.secondary">{servicePackage?.description}</Typography>
      </Stack>

      {!token ? (
        <Alert
          severity="info"
          action={<Button component={Link} to="/signin" color="inherit">Sign In</Button>}
        >
          Sign in to submit an advisory case and track the review in your dashboard.
        </Alert>
      ) : submittedCase ? (
        <Alert
          severity="success"
          action={<Button component={Link} to={`/dashboard/advisory/${submittedCase.id}`} color="inherit">Track Case</Button>}
        >
          Advisory case submitted. Case ID: {submittedCase.id}
        </Alert>
      ) : (
        <Paper variant="outlined" sx={{ p: 3 }} component="form" onSubmit={submit}>
          <Stack gap={2}>
            {isError && <Alert severity="error">Failed to submit advisory case.</Alert>}
            <TextField label="Case title" value={form.title} onChange={update("title")} required />
            <TextField
              select
              label="Review type"
              value={caseType}
              disabled
            >
              <MenuItem value={caseType}>{caseType.replaceAll("_", " ")}</MenuItem>
            </TextField>
            {hasLinkedContext && (
              <Stack direction={{ xs: "column", md: "row" }} gap={2}>
                <TextField
                  select
                  label="Farm"
                  value={form.farm_id || ""}
                  onChange={(event) => {
                    const farm = farms.find((item) => item.id === event.target.value);
                    const pond = farm?.ponds[0];
                    const cycle = pond?.cycles[0];
                    setForm((prev) => ({
                      ...prev,
                      farm_id: farm?.id || "",
                      pond_id: pond?.id || "",
                      cycle_id: cycle?.id || "",
                    }));
                  }}
                  fullWidth
                >
                  <MenuItem value="">Not linked</MenuItem>
                  {farms.map((farm) => <MenuItem key={farm.id} value={farm.id}>{farm.name}</MenuItem>)}
                </TextField>
                <TextField
                  select
                  label="Pond"
                  value={form.pond_id || ""}
                  onChange={(event) => {
                    const pond = ponds.find((item) => item.id === event.target.value);
                    setForm((prev) => ({ ...prev, pond_id: pond?.id || "", cycle_id: pond?.cycles[0]?.id || "" }));
                  }}
                  disabled={!ponds.length}
                  fullWidth
                >
                  <MenuItem value="">Not linked</MenuItem>
                  {ponds.map((pond) => <MenuItem key={pond.id} value={pond.id}>{pond.name}</MenuItem>)}
                </TextField>
                <TextField
                  select
                  label="Cycle"
                  value={form.cycle_id || ""}
                  onChange={update("cycle_id")}
                  disabled={!cycles.length}
                  fullWidth
                >
                  <MenuItem value="">Not linked</MenuItem>
                  {cycles.map((cycle) => <MenuItem key={cycle.id} value={cycle.id}>{cycle.name}</MenuItem>)}
                </TextField>
              </Stack>
            )}
            {intakeFields.filter((field) => !commonLinkedFields.some((linked) => linked.key === field.key)).map((field) => (
              <TextField
                key={field.key}
                select={!!field.options}
                label={field.label}
                value={form[field.key] || ""}
                onChange={update(field.key)}
                multiline={!field.options && !!field.minRows}
                minRows={field.minRows}
                required={field.required}
              >
                {(field.options || []).map((option) => (
                  <MenuItem key={option} value={option}>{option}</MenuItem>
                ))}
              </TextField>
            ))}
            <Button type="submit" variant="contained" disabled={isPending}>
              {isPending ? "Submitting..." : "Submit Advisory Case"}
            </Button>
          </Stack>
        </Paper>
      )}
    </Container>
  );
};
