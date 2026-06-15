import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  header: {
    position: "sticky",
    top: 0,
    zIndex: 1064,
    minHeight: 68,
    margin: "0 -40px 16px",
    padding: "10px 40px",
    display: "flex",
    alignItems: "center",
    gap: 8,
    backgroundColor: "rgba(255,255,255,0.96)",
    borderBottom: `1px solid ${theme.palette.divider}`,
    backdropFilter: "blur(10px)",
    [theme.breakpoints.down("sm")]: {
      margin: "0 -12px 12px",
      padding: "8px 12px",
    },
    [theme.breakpoints.between("sm", "md")]: {
      margin: "0 -20px 16px",
      padding: "10px 20px",
    },
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
    color: theme.palette.text.primary,
    [theme.breakpoints.down("sm")]: {
      minWidth: 40,
      padding: 4,
      fontSize: 0,
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
    height: "100%",
    objectFit: "cover",
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
