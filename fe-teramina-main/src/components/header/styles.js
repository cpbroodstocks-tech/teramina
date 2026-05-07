import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  header: {
    position: "absolute",
    width: "100%",
    top: 0,
    right: 0,
    left: 0,
    margin: "auto",
    zIndex: 1064,
    padding: "15px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  toggleButton: {
    [theme.breakpoints.up("sm")]: {
      display: "none",
    },
    display: "flex",
    gap: 15,
  },
  userButton: {
    marginLeft: "auto",
    alignItems: "center",
    "& span:first-child": {
      padding: "2px 10px",
      marginRight: 10,
      borderRadius: "50%",
      background: "#1976d2 !important",
      color: "white",
    },
  },
  avatarContainer: {
    width: "40px",
    height: "40px",
    position: "relative",
    borderRadius: "50%",
    overflow: "hidden",
    marginRight: "10px",
  },
  avatarUser: {
    width: "100%",
    height: "auto",
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
  },
  menuHeader: {
    "& .MuiPaper-root": {
      boxShadow: "0px 4px 24px 0px #AAACB44D",
      borderRadius: "12px",
    },
  },
  labelMenu: {
    fontFamily: "Lato",
    fontSize: "14px",
    lineHeight: "normal",
  },
}));

export { useStyles };
