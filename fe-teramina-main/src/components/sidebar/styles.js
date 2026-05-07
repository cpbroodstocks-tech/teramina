import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(theme => ({
  sidebar: {
    backgroundColor: "#474DA4 !important",
    width: 270,
    position: "fixed",
    height: "100%",
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
    padding: 15
  },
  sidebarMenu: {
    textDecoration: "none",

    "& button": {
      marginBottom: 3,
      display: "flex",
      gap: 15,
      color: "white",
      justifyContent: "start",
      alignItems: "center",
      fontFamily: "Lato",
      fontWeight: 700,
      lineHeight: "24px",
      "& div": {
        display: "flex",
      },
      "& svg": {
        marginLeft: 5,
        width: 16,
      }
    },

    "& button:hover": {
      backgroundColor: "white",
      color: "#474DA4",
      "& svg path": {
        color: "#474DA4",
        stroke: "#474DA4"
      }
    }

  },
  sidebarMenuActive: {
    borderLeft: "3px solid rgba(255,255,255,0.85)",
    "& button": {
      backgroundColor: "rgba(255,255,255,0.18)",
      color: "#fff",
      "& div": {
        display: "flex",
      }
    },
    "& svg path": {
      color: "#fff",
      stroke: "#fff"
    }
  }
}))

export { useStyles }