import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(theme => ({
  sidebar: {
    backgroundColor: "#474DA4 !important",
    width: 270,
    position: "fixed",
    height: "100%",
    zIndex: 1200,
    [theme.breakpoints.between("sm", "md")]: {
      width: 220,
    },
    [theme.breakpoints.down("sm")]: {
      display: "none"
    },
  },
  sidebarDrawer: {
    backgroundColor: "#474DA4 !important",
    width: 270,
    position: "fixed",
    height: "100%",
  },
  sidebarHeader: {
    padding: "15px",
    marginTop: 40,

    "& h2": {
      display: "flex",
      fontWeight: 900,
      textTransform: "uppercase",
      color: "white",
      textAlign: "center",
      gap: 15,
      alignItems: "center"
    },
    "& h2 i": {
      background: "white",
      display: "flex",
      borderRadius: "50px",
      padding: 10,
      height: 40,
      width: 40,
      alignItems: "center",
      justifyContent: "center",
      overflow: "hidden",
      objectFit: "cover",
      position: "relative"
    },
    "& h2 i img": {
      position: "absolute",
      top: "0px",
      height: 40
    }
  },
  sidebarContent: {
    display: "flex",
    flexDirection: "column",
    padding: "0 15px 20px",
    maxHeight: "calc(100vh - 115px)",
    overflowY: "auto"
  },
  sidebarMenu: {
    marginBottom: 3,
    display: "flex",
    gap: 15,
    color: "white",
    justifyContent: "start",
    alignItems: "center",
    fontFamily: "Lato",
    fontWeight: 700,
    lineHeight: "24px",
    minHeight: 42,
    padding: "8px 12px",
    "& div": {
      display: "flex",
    },
    "& svg": {
      marginLeft: 2,
      width: 18,
      flexShrink: 0,
    },
    "&:hover": {
      backgroundColor: "white",
      color: "#474DA4",
      "& svg path": {
        color: "#474DA4",
        stroke: "#474DA4"
      }
    }

  },
  sidebarGroup: {
    color: "rgba(255,255,255,0.66)",
    fontSize: 11,
    fontWeight: 800,
    letterSpacing: "0.08em",
    margin: "14px 0 5px",
    padding: "6px 10px",
    textTransform: "uppercase",
    justifyContent: "space-between",
    minHeight: 32,
    "&:hover": {
      color: "#fff",
      background: "rgba(255,255,255,0.08)",
    },
    "& svg": {
      width: 16,
    },
  },
  sidebarMenuActive: {
    borderLeft: "3px solid rgba(255,255,255,0.85)",
    backgroundColor: "rgba(255,255,255,0.18)",
    color: "#fff",
    "& svg path": {
      color: "#fff",
      stroke: "#fff"
    }
  }
}))

export { useStyles }
