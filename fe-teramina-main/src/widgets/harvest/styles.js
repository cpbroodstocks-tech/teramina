import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  sectionWrapper: {
    marginTop: 40,
    "& h3": {
      fontSize: 24,
      fontWeight: 700
    },
    "& p": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
      [theme.breakpoints.down("sm")]: {
        fontSize: 12,
      },
    },
    "& h4": {
      fontSize: 28,
      fontWeight: 700,
      color: "#1E1E1E",
      [theme.breakpoints.down("sm")]: {
        fontSize: 16,
      },
    },
  },
  sectionTitle: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  },
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

}));

export { useStyles }