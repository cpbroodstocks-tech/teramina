import { useEffect, useMemo, useState } from "react";
import { SwipeableDrawer, Typography, Button, Collapse } from "@mui/material";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useStyles } from "components/sidebar/styles";
import { routes } from "routes";
import { Link } from "react-router-dom";
import classNames from "classnames";
import { useTranslation } from "react-i18next";
import { useUserProfile } from "features/user/queries";

const dashboardRoutes = routes.filter((r) => r.path === "/dashboard")[0].children;
const GROUP_ORDER = [
  "MENU_GROUP.TODAY",
  "MENU_GROUP.OPERATE",
  "MENU_GROUP.ANALYZE",
  "MENU_GROUP.IMPROVE",
  "MENU_GROUP.ACCOUNT",
  "MENU_GROUP.ADMIN",
  "MENU_GROUP.OTHER",
];

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
        return route.navParent || route.label;
    }
  }
  return null;
}

const MenuList = ({ menus, activeLabelKey, styles, onNavigate }) => {
  const { t } = useTranslation();
  const groupedMenus = useMemo(() => GROUP_ORDER
    .map((groupKey) => ({
      groupKey,
      group: menus.find((menu) => menu.groupKey === groupKey)?.group,
      items: menus.filter((menu) => menu.groupKey === groupKey),
    }))
    .filter((group) => group.items.length), [menus]);
  const activeGroup = menus.find((menu) => menu.labelKey === activeLabelKey)?.groupKey;
  const [expanded, setExpanded] = useState(() => new Set(["MENU_GROUP.OPERATE", activeGroup].filter(Boolean)));

  useEffect(() => {
    if (!activeGroup) return;
    setExpanded((previous) => new Set([...previous, activeGroup]));
  }, [activeGroup]);

  const toggleGroup = (groupKey) => {
    setExpanded((previous) => {
      const next = new Set(previous);
      if (next.has(groupKey)) next.delete(groupKey);
      else next.add(groupKey);
      return next;
    });
  };

  const renderMenu = (menu) => {
    const isActive = menu.labelKey === activeLabelKey;
    return (
      <Button
        key={menu.path}
        component={Link}
        to={menu.path}
        fullWidth
        aria-current={isActive ? "page" : undefined}
        className={classNames(styles.sidebarMenu, isActive && styles.sidebarMenuActive)}
        onClick={onNavigate}
      >
        {menu.icon}
        <span>{menu.label}</span>
      </Button>
    );
  };

  return (
    <>
      <div className={styles.sidebarHeader}>
        <Typography variant="h2">
          <i><img src="/logo.png" alt="" /></i>
          Teramina
        </Typography>
      </div>
      <nav className={styles.sidebarContent} aria-label={t("DASHBOARD_NAVIGATION")}>
        {groupedMenus.map((group) => {
          if (group.groupKey === "MENU_GROUP.TODAY") return group.items.map(renderMenu);
          const isExpanded = expanded.has(group.groupKey);
          return (
            <div key={group.groupKey}>
              <Button
                fullWidth
                className={styles.sidebarGroup}
                onClick={() => toggleGroup(group.groupKey)}
                aria-expanded={isExpanded}
              >
                <span>{group.group}</span>
                {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </Button>
              <Collapse in={isExpanded} timeout="auto">
                {group.items.map(renderMenu)}
              </Collapse>
            </div>
          );
        })}
      </nav>
    </>
  );
};

const Sidebar = ({ open, setOpen, activePath }) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();
  const { data: profile } = useUserProfile();
  const activeLabelKey = getActiveLabelKey(activePath);

  const menus = dashboardRoutes
    .filter((route) => route.category !== "children" && (!route.adminOnly || profile?.role_user === "admin"))
    .map((route) => ({
      path: `/dashboard/${route.path}`,
      icon: route.icon,
      label: t(route.label),
      labelKey: route.label,
      groupKey: route.group || "MENU_GROUP.OTHER",
      group: t(route.group || "MENU_GROUP.OTHER"),
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
        <MenuList menus={menus} activeLabelKey={activeLabelKey} styles={styles} onNavigate={() => setOpen(false)} />
      </SwipeableDrawer>
      <div className={styles.sidebar}>
        <MenuList menus={menus} activeLabelKey={activeLabelKey} styles={styles} />
      </div>
    </>
  );
};

export default Sidebar;
