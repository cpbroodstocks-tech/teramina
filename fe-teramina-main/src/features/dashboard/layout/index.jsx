import Sidebar from "components/sidebar";
import { Fragment, Suspense, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Header from "components/header";
import Loader from "components/loader";
import { Stack, Typography } from "@mui/material";
import { useStyles } from "./styles";
import ContextSelector from "components/context-selector";
import { useDashboardContextStore } from "store/dashboard-context.store";
import { DashboardDemoInitializer, DemoContextActions, DemoExperienceTracker, RealDataActivation } from "features/demo-experience/dashboard-demo-experience";
import { routes } from "routes";
import { useTranslation } from "react-i18next";

const dashboardRoutes = routes.find((route) => route.path === "/dashboard")?.children || [];

const getCurrentDashboardRoute = (path) => dashboardRoutes.find((route) => {
  const template = `/dashboard/${route.path}`.split("/");
  const actual = path.split("/");
  return template.length === actual.length && template.every((segment, index) => segment.startsWith(":") || segment === actual[index]);
});

const ContextBar = ({ level }) => {
  const { farm_name: farmName, pond_name: pondName, cycle_name: cycleName } = useDashboardContextStore();

  const parts = [farmName, pondName, cycleName].filter(Boolean);

  return (
    <Stack spacing={0.75} sx={{ p: 1.5, mb: 2, background: "background.paper", border: "1px solid", borderColor: "divider", borderRadius: 1.5 }}>
      <Stack direction={{ xs: "column", xl: "row" }} spacing={1} sx={{ alignItems: { xl: "center" } }}>
        <ContextSelector level={level} />
        <DemoContextActions />
      </Stack>
      {parts.length > 0 && <Typography variant="caption" color="textSecondary">{parts.join(" › ")}</Typography>}
    </Stack>
  );
};

const Dashboard = () => {
  const { classes: styles } = useStyles();
  const [open, setOpen] = useState(() => false);
  const location = useLocation();
  const currentRoute = getCurrentDashboardRoute(location.pathname);
  const { t } = useTranslation();

  return (
    <Fragment>
      <a href="#main-content" className="skip-link">{t("SKIP_TO_MAIN_CONTENT")}</a>
      <Sidebar open={open} setOpen={setOpen} activePath={location.pathname} />
      <div className={styles.pageWrapper}>
        <DashboardDemoInitializer />
        <DemoExperienceTracker />
        <Header open={open} setOpen={setOpen} />
        {currentRoute?.contextLevel && <ContextBar level={currentRoute.contextLevel} />}
        <RealDataActivation />
        <main className={styles.maincontent} id="main-content" tabIndex={-1}>
          <Suspense fallback={<Loader />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </Fragment>
  );
};

export default Dashboard;
