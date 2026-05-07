import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  modalWrapper: {
    padding: 15,
    [theme.breakpoints.down("sm")]: {
      width: "320px",
      maxWidth: "100%",
    }
  },
  modalContent: {
    maxWidth: "100%",
    padding: "15px",
  },
  sectionTitle: {
    fontWeight: 700,
    fontSize: "24px",
    lineHeight: "29px",
    color: "#333333",
    marginBottom: "16px",
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
  btnSubmit: {
    marginTop: "15px",
    background: "#474DA4",
    fontSize: "16px",
    fontWeight: 800,
    borderRadius: "3px",
    width: "100%",
    textTransform: "uppercase",
    padding: "8px",
    "&:hover": {
      background: "#101558",
      color: "#FFFFFF",
    },
  },
  circular: {
    width: "29px !important",
    height: "29px !important",
  },
  titleForm: {
    marginBottom: "32px",
    fontSize: "22px",
    fontWeight: 700,
  },
}));

export { useStyles }