import { SwipeableDrawer, Typography, Button } from "@mui/material";
import { useStyles } from "components/sidebar/styles";
import { routes } from "routes";
import { Link } from "react-router-dom";
import classNames from "classnames";
import { useTranslation } from "react-i18next";

const dashboardRoutes = routes.filter((r) => r.path === "/dashboard")[0].children;

function getActiveLabelKey(path) {
  for (const route of dashboardRoutes) {
    const fullPath = route.path === "" ? "/dashboard" : `/dashboard/${route.path}`;
    if (!route.path.includes(":")) {
      if (fullPath === path) return route.label;
    } else {
      const tpl = fullPath.split("/");
      const actual = path.split("/");
      if (
        tpl.length === actual.length &&
        tpl.every((s, i) => s.startsWith(":") || s === actual[i])
      )
        return route.label;
    }
  }
  return null;
}

const MenuList = ({ menus, activeLabelKey, styles }) => (
  <>
    <div className={styles.sidebarHeader}>
      <Typography variant="h2">
        <i>
          <img src="/logo.png" alt="Teramina" />
        </i>
        Teramina
      </Typography>
    </div>
    <div className={styles.sidebarContent}>
      {menus.map((menu, key) => {
        const isActive = menu.labelKey === activeLabelKey;
        return (
          <Link
            to={menu.path}
            key={key}
            className={classNames(
              styles.sidebarMenu,
              isActive ? styles.sidebarMenuActive : ""
            )}
          >
            <Button fullWidth>
              {menu.icon}
              {menu.label}
            </Button>
          </Link>
        );
      })}
    </div>
  </>
);

const Sidebar = ({ open, setOpen, activePath }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const activeLabelKey = getActiveLabelKey(activePath);

  const menus = dashboardRoutes
    .filter((route) => route.category !== "children")
    .map((route) => ({
      path: route.path,
      icon: route.icon,
      label: t(route.label),
      labelKey: route.label,
    }));

  return (
    <>
      <SwipeableDrawer
        anchor="left"
        open={open}
        onClose={() => setOpen(false)}
        onOpen={() => setOpen(true)}
        classes={{
          paper: styles.sidebarDrawer,
        }}
      >
        <MenuList menus={menus} activeLabelKey={activeLabelKey} styles={styles} />
      </SwipeableDrawer>
      <div className={styles.sidebar}>
        <MenuList menus={menus} activeLabelKey={activeLabelKey} styles={styles} />
      </div>
    </>
  );
};

export default Sidebar;
