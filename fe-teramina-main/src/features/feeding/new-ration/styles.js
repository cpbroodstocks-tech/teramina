import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()({
  formContainer: {
    padding: "44px"
  },
  titleForm: {
    marginBottom: "32px",
    fontSize: "22px",
    fontWeight: 700,
  },
  titleField: {
    margin: "12px 0 10px 0",
  },
  requiredLabel: {
    position: "relative",
    "&:after": {
      content: "\" *\"",
      position: "relative",
      color: "#EF3061",
    }
  },
  buttonAction: {
    marginTop: "37px",
    background: "#474DA4",
    fontSize: "16px",
    fontWeight: 800,
    borderRadius: "3px",
    flex: "1 1 auto",
    textTransform: "uppercase",
    padding: "8px",
    color: "#FFFFFF",
    "&:hover": {
      background: "#101558",
      color: "#FFFFFF",
    },
  },
  circular: {
    width: "29px !important",
    height: "29px !important",
  },
})

export { useStyles }