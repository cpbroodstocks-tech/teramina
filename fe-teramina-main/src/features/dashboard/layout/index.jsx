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

const ContextBar = () => {
  const { farm_name: farmName, pond_name: pondName, cycle_name: cycleName } = useDashboardContextStore();

  const parts = [farmName, pondName, cycleName].filter(Boolean);

  return (
    <Stack spacing={0.75} sx={{ padding: "10px 16px", mb: 2, background: "#f7f8fa", border: "1px solid #e0e3e7", borderRadius: 1 }}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ alignItems: { sm: "center" } }}>
        <ContextSelector />
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

  return (
    <Fragment>
      <Sidebar open={open} setOpen={setOpen} activePath={location.pathname} />
      <div className={styles.pageWrapper}>
        <DashboardDemoInitializer />
        <DemoExperienceTracker />
        <Header open={open} setOpen={setOpen} />
        <ContextBar />
        <RealDataActivation />
        <main className={styles.maincontent}>
          <Suspense fallback={<Loader />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </Fragment>
  );
};

export default Dashboard;
