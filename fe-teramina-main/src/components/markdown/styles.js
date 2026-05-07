import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  infoCard: {
    display: "block",
    marginTop:15,
    "& h4": {
      display: "flex",
      gap: 5,
      alignItems: "baseline"
    },
    "& h4 span": {
      fontWeight: 300,
      fontSize: 14
    }
  },
  wrapPondSummary: {
    position: "relative",
    alignItems: "center",
    justifyContent: "center",
    color: "black"
  },
  generateSummaryButton: {
    display: "flex",
    justifyContent: "center",
    width: "100%",
    marginTop: 50,
    marginBottom: 50,
  },
  regenerateSummaryButton: {
    display: "flex",
    justifyContent: "right",
    width: "100%",
  },
}));

export { useStyles };