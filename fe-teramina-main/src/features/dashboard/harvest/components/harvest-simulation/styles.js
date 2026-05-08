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
  harvestSimulationPlan: {
    marginTop: "10px",
    marginBottom: "40px"
  },
  table: {
    [theme.breakpoints.down("sm")]: {
      width: "1000px",
    },
    "& th": {
      fontFamily: "Lato",
      background: "#F8FAFC",
      width: "auto",
    },
    "& th:nth-child(8)": {
      width: "192px !important",
    },
    "& td": {
      fontFamily: "Lato",
    }
  },
  simulationPlanTitle: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between"
  },
  buttonAction: {
    marginTop: 20,
    marginBottom: 20,
    display: "block",
    marginLeft: "auto",
    background: "rgba(71, 77, 164, 0.32)",
    color: "black"
  },
  contentEmpty: {
    display: "flex",
    alignContent: "center",
    flexDirection: "column",
    verticalAlign: "middle",
    textAlign: "center",
    minHeight: "42vh",
    justifyContent: "center",
  },
  lgEmpty: {
    "& img": {
      width: "514px",
      [theme.breakpoints.down("sm")]: {
        width: "300px",
      },
    }
  }

}));

export { useStyles }