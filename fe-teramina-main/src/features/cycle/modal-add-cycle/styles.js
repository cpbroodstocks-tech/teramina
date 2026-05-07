import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  modalWrapper: {
    [theme.breakpoints.down("sm")]: {
      width: "320px",
      maxWidth: "100%",
    }
  },
  btnNew: {
    background: "#474DA4",
    fontSize: "16px",
    fontWeight: 500,
    lineHeight: "24px",
    letterSpacing: "-0.02em",
    borderRadius: "3px",
    width: "auto",
    padding: "8px 16px",
    color: "#FFFFFF",
    [theme.breakpoints.down("sm")]: {
      fontSize: "12px",
      lineHeight: "16px",

    },
    "&:hover": {
      background: "#101558",
      color: "#FFFFFF",
    },
  },
}));

export { useStyles }