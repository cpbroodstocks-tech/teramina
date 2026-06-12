import { useEffect, useMemo, useRef, useState } from "react";
import { Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, LinearProgress, Menu, MenuItem, Stack, Typography } from "@mui/material";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { MdCheck, MdMoreVert } from "react-icons/md";
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

export const DemoExperienceTracker = () => {
  const location = useLocation();
  const { data: farms = [] } = useFarmHierarchy();
  const context = useDashboardContextStore();
  const track = useTrackDemoEvent();
  const lastRoute = useRef("");
  const selectedFarm = farms.find((farm) => farm.id === context.farm_id);
  const isDemo = !!selectedFarm?.is_demo;

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

  return null;
};

export const DemoContextActions = () => {
  const navigate = useNavigate();
  const { data: farms = [] } = useFarmHierarchy();
  const { data: experience } = useDemoExperience();
  const context = useDashboardContextStore();
  const track = useTrackDemoEvent();
  const update = useUpdateDemoExperience();
  const reset = useResetDemoExperience();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [guideOpen, setGuideOpen] = useState(false);
  const selectedFarm = farms.find((farm) => farm.id === context.farm_id);
  const isDemo = !!selectedFarm?.is_demo;
  const completed = useMemo(() => new Set(experience?.completed_steps || []), [experience?.completed_steps]);

  useEffect(() => {
    if (isDemo && experience && !experience.checklist_dismissed) setGuideOpen(true);
  }, [isDemo, experience?.checklist_dismissed]);

  if (!isDemo || !experience) return null;

  const closeGuide = () => {
    setGuideOpen(false);
    update.mutate(true, {
      onSuccess: () => track.mutate({ eventName: "demo_checklist_dismissed" }),
    });
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
    <>
      <Stack direction="row" spacing={0.25} sx={{ alignItems: "center", flexShrink: 0 }}>
        <Chip size="small" color="info" label="Demo" />
        <IconButton size="small" aria-label="Demo options" onClick={(event) => setAnchorEl(event.currentTarget)}>
          <MdMoreVert />
        </IconButton>
      </Stack>
      <Menu anchorEl={anchorEl} open={!!anchorEl} onClose={() => setAnchorEl(null)}>
        <MenuItem onClick={() => {
          setAnchorEl(null);
          setGuideOpen(true);
          track.mutate({ eventName: "demo_checklist_reopened" });
        }}>
          Exploration guide
        </MenuItem>
        <MenuItem component={Link} to="/dashboard/farm-management" onClick={() => setAnchorEl(null)}>Add my farm</MenuItem>
        <MenuItem
          disabled={reset.isPending}
          onClick={() => {
            setAnchorEl(null);
            resetDemo();
          }}
          sx={{ color: "warning.main" }}
        >
          Reset demo data
        </MenuItem>
      </Menu>
      <Dialog open={guideOpen} onClose={closeGuide} maxWidth="md" fullWidth>
        <DialogTitle>Explore Teramina</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Follow these steps using editable sample data. Use the Pond selector to compare Healthy and At Risk scenarios.
          </Typography>
          <Stack direction="row" spacing={2} sx={{ justifyContent: "space-between", alignItems: "center", mb: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Quick start <Typography component="span" variant="caption" color="text.secondary">{completed.size}/{STEPS.length} complete</Typography>
            </Typography>
          </Stack>
          <LinearProgress variant="determinate" value={(completed.size / STEPS.length) * 100} sx={{ mb: 1.5, height: 4, borderRadius: 4 }} />
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" }, gap: 1 }}>
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
                  onClick={() => {
                    closeGuide();
                    if (step.action === "assistant") window.dispatchEvent(new CustomEvent("open-agent-chat"));
                  }}
                  startIcon={isComplete ? <MdCheck /> : <Box component="span" sx={{ fontSize: 12, fontWeight: 700 }}>{index + 1}</Box>}
                  sx={{
                    justifyContent: "flex-start",
                    minHeight: 42,
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
        </DialogContent>
        <DialogActions>
          <Button onClick={closeGuide}>Close guide</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
