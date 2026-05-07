import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  container: {
    width: "444px",
    maxWidth: "100%",
    background: "#FFFFFF",
    boxShadow: "0px 6px 8px rgba(0, 0, 0, 0.05)",
    borderRadius: "7px",
    padding: "40px",
    [theme.breakpoints.down("sm")]: {
      width: "100%",
      padding: "20px",
      marginTop: "60px",
    },
  },
  title: {
    marginBottom: "32px",
    fontSize: "22px",
    fontWeight: 700,
  },
  input: {
    width: "100%",
  },
  label: {
    margin: "16px 0 8px 0",
    fontSize: "14px",
  },
  requiredLabel: {
    position: "relative",
    "&:after": {
      content: "\" *\"",
      position: "relative",
      color: "#EF3061",
    }
  },
  btnContainer: {
    marginTop: "37px",
    display: "flex",
    alignItems: "center",
    flexWrap: "nowrap",
  },
  btnBack: {
    boxShadow: "unset !important",
    color: "#474DA4",
    background: "transparent",
    fontSize: "16px",
    fontWeight: 800,
    flex: "0 0 auto",
    textTransform: "uppercase",
    padding: "8px 24px",
    "&:hover": {
      boxShadow: "unset !important",
      background: "transparent",
      color: "#474DA4",
    },
  },
  btnSubmit: {
    background: "#474DA4",
    fontSize: "16px",
    fontWeight: 800,
    borderRadius: "3px",
    flex: "1 1 auto",
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
}));

export { useStyles };