import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  harvestRecordButton: {
    alignSelf: "flex-start",
    padding: "7.82px 12px",
    whiteSpace: "nowrap",
    background: "#474DA4",
    color: "white",
    "&:hover": {
      background: "#101558",
      color: "white"
    }
  },
  title: {
    marginBottom: "32px",
    fontSize: "22px",
    fontWeight: 700,
  },
  formContainer: {
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
  radioContainer: {
    border: "1px solid black",
    padding: 15,
    borderRadius: 4
  },
  formInput: {
    marginBottom: 15
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
  labelField: {
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
}));

export { useStyles }