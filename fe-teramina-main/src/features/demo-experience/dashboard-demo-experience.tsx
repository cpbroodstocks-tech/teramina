import { useEffect, useMemo, useRef } from "react";
import { Box, Button, Chip, LinearProgress, Paper, Stack, Typography } from "@mui/material";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { MdCheck, MdOutlineExplore } from "react-icons/md";
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
    <Paper
      variant="outlined"
      sx={{
        mb: 2.5,
        p: { xs: 1.5, md: 2 },
        borderColor: "rgba(71, 77, 164, 0.24)",
        borderRadius: 2,
        background: "linear-gradient(135deg, rgba(71, 77, 164, 0.06), rgba(255, 255, 255, 0.96) 45%)",
      }}
    >
      <Stack direction={{ xs: "column", lg: "row" }} spacing={1.5} sx={{ justifyContent: "space-between", alignItems: { lg: "center" } }}>
        <Stack direction="row" spacing={1.25} sx={{ alignItems: "center" }}>
          <Box sx={{ display: "grid", placeItems: "center", width: 36, height: 36, borderRadius: 1.5, color: "primary.main", bgcolor: "rgba(71, 77, 164, 0.08)" }}>
            <MdOutlineExplore size={22} />
          </Box>
          <Box>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Explore with sample data</Typography>
              <Chip size="small" color="info" label="Demo mode" />
            </Stack>
            <Typography variant="body2" color="text.secondary">Editable sample farm. Your real farm is not affected.</Typography>
          </Box>
        </Stack>
        <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
          <Button size="small" variant="contained" onClick={compare}>Compare scenarios</Button>
          <Button size="small" component={Link} to="/dashboard/farm-management" variant="outlined">Add my farm</Button>
          {experience.checklist_dismissed && (
            <Button
              size="small"
              variant="text"
              onClick={() => update.mutate(false, {
                onSuccess: () => track.mutate({ eventName: "demo_checklist_reopened" }),
              })}
            >
              Show guide
            </Button>
          )}
          <Button size="small" variant="text" color="warning" disabled={reset.isPending} onClick={resetDemo}>Reset</Button>
        </Stack>
      </Stack>
      {!experience.checklist_dismissed && (
        <Box sx={{ mt: 1.75, pt: 1.5, borderTop: "1px solid", borderColor: "divider" }}>
          <Stack direction="row" spacing={2} sx={{ justifyContent: "space-between", alignItems: "center", mb: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Quick start <Typography component="span" variant="caption" color="text.secondary">{completed.size}/{STEPS.length} complete</Typography>
            </Typography>
            <Button
              size="small"
              color="inherit"
              onClick={() => update.mutate(true, {
                onSuccess: () => track.mutate({ eventName: "demo_checklist_dismissed" }),
              })}
            >
              Hide guide
            </Button>
          </Stack>
          <LinearProgress variant="determinate" value={(completed.size / STEPS.length) * 100} sx={{ mb: 1.25, height: 4, borderRadius: 4 }} />
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" }, gap: 0.75 }}>
            {STEPS.map((step, index) => {
              const isComplete = completed.has(step.key);
              return (
                <Button
                  key={step.key}
                  size="small"
                  variant="text"
                  color={isComplete ? "success" : "primary"}
                  component={step.to ? Link : "button"}
                  to={step.to}
                  onClick={step.action === "assistant" ? () => window.dispatchEvent(new CustomEvent("open-agent-chat")) : undefined}
                  startIcon={isComplete ? <MdCheck /> : <Box component="span" sx={{ fontSize: 12, fontWeight: 700 }}>{index + 1}</Box>}
                  sx={{
                    justifyContent: "flex-start",
                    minHeight: 38,
                    px: 1,
                    textAlign: "left",
                    bgcolor: isComplete ? "rgba(46, 125, 50, 0.08)" : "rgba(71, 77, 164, 0.05)",
                    "&:hover": { bgcolor: isComplete ? "rgba(46, 125, 50, 0.14)" : "rgba(71, 77, 164, 0.11)" },
                  }}
                >
                  {step.label}
                </Button>
              );
            })}
          </Box>
        </Box>
      )}
    </Paper>
  );
};
