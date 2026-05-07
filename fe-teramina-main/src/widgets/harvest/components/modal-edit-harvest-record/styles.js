import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
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
  formContainer: {
    width: "444px",
    maxWidth: "100%",
    padding: "40px",
  },
  title: {
    marginBottom: "15px",
    fontSize: "22px",
    fontWeight: 700,
  },
  radioContainer: {
    border: "1px solid black",
    padding: 15,
    borderRadius: 4
  },
  buttonAction: {
    marginTop: "37px",
    background: "#474DA4",
    color: "#FFFFFF",
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
}));

export { useStyles }