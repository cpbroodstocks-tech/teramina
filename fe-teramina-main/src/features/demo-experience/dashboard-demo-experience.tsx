import { useEffect, useMemo, useRef } from "react";
import { Alert, Box, Button, Chip, LinearProgress, Paper, Stack, Typography } from "@mui/material";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useFarmHierarchy } from "features/farm/queries";
import { useDashboardContextStore } from "store/dashboard-context.store";
import {
  useDemoExperience,
  useResetDemoExperience,
  useTrackDemoEvent,
  useUpdateDemoExperience,
} from "./queries";
import { trackDemoEvent } from "./analytics";

const STEPS = [
  { key: "review_today", label: "Review today's risks", to: "/dashboard/today" },
  { key: "compare_scenarios", label: "Compare Healthy and At Risk", to: "/dashboard/today" },
  { key: "ask_assistant", label: "Ask the assistant", action: "assistant" },
  { key: "open_memory", label: "Review remembered patterns", to: "/dashboard/memory" },
  { key: "review_forecast", label: "Review the forecast", to: "/dashboard/forecast" },
  { key: "open_advisory_report", label: "Open the advisory report", to: "/dashboard/advisory" },
  { key: "open_library", label: "Open the library", to: "/dashboard/library" },
  { key: "add_real_farm", label: "Add your real farm", to: "/dashboard/farm-management" },
];

const routeEvent = (pathname: string) => {
  if (pathname === "/dashboard/today") return "demo_today_opened";
  if (pathname === "/dashboard/memory") return "demo_memory_opened";
  if (pathname === "/dashboard/forecast") return "demo_forecast_opened";
  if (/^\/dashboard\/advisory\/[^/]+$/.test(pathname)) return "demo_advisory_report_opened";
  if (pathname === "/dashboard/library") return "demo_library_opened";
  return "";
};

export const DashboardDemoInitializer = () => {
  const navigate = useNavigate();
  const { data: farms = [] } = useFarmHierarchy();
  const { data: experience } = useDemoExperience();
  const context = useDashboardContextStore();
  const initialized = useRef(false);

  useEffect(() => {
    if (!experience || !farms.length || initialized.current) return;
    initialized.current = true;
    const validCurrent = farms.some((farm) =>
      farm.id === context.farm_id &&
      farm.ponds.some((pond) => pond.id === context.pond_id && pond.cycles.some((cycle) => cycle.id === context.cycle_id))
    );
    const currentFarm = farms.find((farm) => farm.id === context.farm_id);
    const shouldUseDefault = !validCurrent || (experience.has_real_data && currentFarm?.is_demo);
    if (shouldUseDefault && experience.default_context) {
      context.setContext(experience.default_context);
    }
    if (experience.demo_available && !experience.has_real_data && !experience.first_opened_at) {
      trackDemoEvent("demo_opened").catch(() => undefined);
      navigate("/dashboard/today", { replace: true });
    } else if (experience.has_real_data && !experience.completed_steps?.includes("add_real_farm")) {
      trackDemoEvent("real_data_activated").catch(() => undefined);
    }
  }, [experience, farms]);
  return null;
};

export const DemoExperiencePanel = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { data: farms = [] } = useFarmHierarchy();
  const { data: experience } = useDemoExperience();
  const context = useDashboardContextStore();
  const track = useTrackDemoEvent();
  const update = useUpdateDemoExperience();
  const reset = useResetDemoExperience();
  const lastRoute = useRef("");
  const selectedFarm = farms.find((farm) => farm.id === context.farm_id);
  const selectedPond = selectedFarm?.ponds.find((pond) => pond.id === context.pond_id);
  const isDemo = !!selectedFarm?.is_demo;
  const completed = useMemo(() => new Set(experience?.completed_steps || []), [experience?.completed_steps]);

  useEffect(() => {
    if (!isDemo || lastRoute.current === location.pathname) return;
    lastRoute.current = location.pathname;
    const eventName = routeEvent(location.pathname);
    if (eventName) track.mutate({ eventName, properties: { route: location.pathname } });
  }, [isDemo, location.pathname]);

  useEffect(() => {
    const handler = () => {
      if (isDemo) track.mutate({ eventName: "demo_assistant_question_sent" });
    };
    window.addEventListener("demo-assistant-question-sent", handler);
    return () => window.removeEventListener("demo-assistant-question-sent", handler);
  }, [isDemo]);

  if (!isDemo || !experience) return null;

  const compare = () => {
    const nextScenario = selectedPond?.demo_scenario === "healthy" ? "at_risk" : "healthy";
    const pond = selectedFarm.ponds.find((item) => item.demo_scenario === nextScenario);
    const cycle = pond?.cycles.find((item) => item.dashboard_ready) || pond?.cycles[0];
    if (!pond || !cycle) return;
    context.setContext({
      farm_id: selectedFarm.id,
      farm_name: selectedFarm.name,
      pond_id: pond.id,
      pond_name: pond.name,
      cycle_id: cycle.id,
      cycle_name: cycle.name,
    });
    track.mutate({ eventName: "demo_context_selected", properties: { scenario: nextScenario } });
    window.location.reload();
  };

  const resetDemo = async () => {
    if (!window.confirm("Reset your editable demo farm to the canonical sample data? Your real farms will not be changed.")) return;
    const result = await reset.mutateAsync();
    if (result?.demo_context) {
      context.setContext(result.demo_context);
      navigate("/dashboard/today", { replace: true });
      window.location.reload();
    }
  };

  return (
    <Stack spacing={1.5} sx={{ mb: 2 }}>
      <Alert
        severity="info"
        action={<Chip size="small" color="info" label="Demo Mode" />}
      >
        You are exploring editable sample farm data. Changes do not affect your real farm.
      </Alert>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
        <Button variant="outlined" onClick={compare}>Compare scenarios</Button>
        <Button component={Link} to="/dashboard/farm-management" variant="outlined">Add my farm</Button>
        <Button
          variant="outlined"
          onClick={() => update.mutate(false, {
            onSuccess: () => track.mutate({ eventName: "demo_checklist_reopened" }),
          })}
        >
          Show checklist
        </Button>
        <Button variant="text" color="warning" disabled={reset.isPending} onClick={resetDemo}>Reset demo</Button>
      </Stack>
      {!experience.checklist_dismissed && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack spacing={1.25}>
            <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>Explore Teramina</Typography>
                <Typography variant="body2" color="text.secondary">{completed.size} of {STEPS.length} capabilities explored</Typography>
              </Box>
              <Button
                size="small"
                onClick={() => update.mutate(true, {
                  onSuccess: () => track.mutate({ eventName: "demo_checklist_dismissed" }),
                })}
              >
                Dismiss
              </Button>
            </Stack>
            <LinearProgress variant="determinate" value={(completed.size / STEPS.length) * 100} />
            <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
              {STEPS.map((step) => (
                <Button
                  key={step.key}
                  size="small"
                  variant={completed.has(step.key) ? "contained" : "outlined"}
                  color={completed.has(step.key) ? "success" : "primary"}
                  component={step.to ? Link : "button"}
                  to={step.to}
                  onClick={step.action === "assistant" ? () => window.dispatchEvent(new CustomEvent("open-agent-chat")) : undefined}
                >
                  {step.label}
                </Button>
              ))}
            </Stack>
          </Stack>
        </Paper>
      )}
    </Stack>
  );
};
