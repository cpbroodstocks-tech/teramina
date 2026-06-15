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
  harvestRecord: {
    marginTop: "12px",
  },
  table: {
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
      width: "330px",
      [theme.breakpoints.down("sm")]: {
        width: "300px",
      },
    }
  }
}));

export { useStyles }
