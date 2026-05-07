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
    fontSize: "22px",
    fontWeight: 700,
    marginBottom: "32px",
  },
  formRow: {
    marginBottom: 15
  },
  formGroup: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 15,
    flexDirection: "row"

  },
  formInputGroup: {
    display: "flex",
    flexDirection: "column",

  },
  buttonAction: {
    background: "#474DA4",
    color: "white",
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
  errorMessage: {
    fontSize: 12,
    fontWeight: 500,
    color: "#FF0000",
  },
  titleFieldUppercase: {
    textTransform: "uppercase",
  },
  requiredLabel: {
    position: "relative",
    "&:after": {
      content: "\" *\"",
      position: "relative",
      color: "#EF3061",
    }
  },
  labelField: {
    margin: "16px 0 8px 0",
    fontSize: "14px",
  },
  btnContainer: {
    marginTop: "37px",
    display: "flex",
    alignItems: "center",
    flexWrap: "nowrap",
  },
}));

export { useStyles }