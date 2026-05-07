import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()({
  stepper: {
    display: "none",
    flex: "0 0 100%",
    margin: 0,
    padding: 0,
    "&:nth-child(1)": {
      justifyContent: "center"
    }
  },
  stepperActive: {
    display: "flex"
  },
  iconStepper: {
    display: "none"
  }
})

export { useStyles }