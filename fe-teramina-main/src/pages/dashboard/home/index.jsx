import Sidebar from "components/sidebar";
import { Fragment, Suspense, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Header from "components/header";
import { useStyles } from "pages/dashboard/home/styles";

const Dashboard = () => {
  const { classes: styles } = useStyles();
  const [open, setOpen] = useState(() => false);
  const location = useLocation();

  return (
    <Fragment>
      <Sidebar open={open} setOpen={setOpen} activePath={location.pathname} />
      <div className={styles.pageWrapper}>
        <Header open={open} setOpen={setOpen} />
        <main className={styles.maincontent}>
          <Suspense fallback={null}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </Fragment>
  );
};

export default Dashboard;
