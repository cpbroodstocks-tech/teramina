import Sidebar from "components/sidebar";
import { Fragment, Suspense, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Header from "components/header";
import Loader from "components/loader";
import { Typography } from "@mui/material";
import { useStyles } from "pages/dashboard/home/styles";

const ContextBar = () => {
  const farmName = localStorage.getItem("farm_name");
  const pondName = localStorage.getItem("pond_name");
  const cycleName = localStorage.getItem("cycle_name");

  if (!farmName) return null;

  const parts = [farmName, pondName, cycleName].filter(Boolean);

  return (
    <div style={{ padding: "4px 20px", background: "#f5f5f5", borderBottom: "1px solid #e0e0e0" }}>
      <Typography variant="caption" color="textSecondary">
        {parts.join(" › ")}
      </Typography>
    </div>
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
        <Header open={open} setOpen={setOpen} />
        <ContextBar />
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
