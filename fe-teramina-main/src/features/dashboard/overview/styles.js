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

  performancPlot: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 10,
    marginTop: 10,
    marginBottom: 10,
    borderRadius: 10
  },

  performanceMetric: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr 1fr",
    gap: 10,
    marginTop: 20,
    marginBottom: 10,
    borderRadius: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    "& h4": {
      justifyContent: "center",
      fontSize: 28,
      textAlign: "center",
    },
    "& p": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
    },
    "& span": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
      marginLeft: 5,
    },
  },

  performanceMetricAggregate: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr",
    gap: 10,
    marginTop: 20,
    marginBottom: 10,
    borderRadius: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    "& h4": {
      justifyContent: "center",
      fontSize: 28,
      textAlign: "center",
    },
    "& p": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
    },
    "& span": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
      marginLeft: 5,
    },
  },

  sectionWrapperSummary: {
    marginTop: 40,
    "& h3": {
      fontSize: 24,
      fontWeight: 700
    },
    "& p": {
      fontFamily: "Arial, sans-serif",
      fontSize: 14,
      color: "black",
      fontWeight: 300,
      [theme.breakpoints.down("sm")]: {
        fontSize: 12,
      },
    },
    "& h4": {
      fontFamily: "Arial, sans-serif",
      fontSize: 28,
      fontWeight: 700,
      color: "#1E1E1E",
      [theme.breakpoints.down("sm")]: {
        fontSize: 16,
      },
    },
  },

  tooltipInfo: {
    cursor: "pointer",
  },
  cardToolTip: {
    cursor: "pointer",
    transition: "1s",
    "&:hover": {
      backgroundColor: theme.palette.primary.main,
      color: "#fff",
      "& p,h4,h3,h2,svg": {
        color: "#fff",
      }
    }

  },

  pondInfo: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr",
    gap: 15,
    marginTop: 20,
    borderRadius: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    "& h4": {
      justifyContent: "center",
      fontSize: 28,
      textAlign: "center",
    },
    "& p": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
    },
    "& span": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
      marginLeft: 5,
    },
  },

  wrapPodInfo: {
    position: "relative",
    height: "100%",
    paddingTop: "60px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },

  wrapPondSummary: {
    position: "relative",
    alignItems: "center",
    justifyContent: "center",
    color: "black"
  },

  pondInfoTitle: {
    width: "100%",
    padding: "0 15px",
    position: "absolute",
    left: "0",
    top: "15px",
    display: "flex",
    alignItems: "center",
    flexWrap: "nowrap",
    justifyContent: "space-between",
  },

  performance: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 2fr",
    gridTemplateRows: "1fr auto",
    gridTemplateAreas: "\"a b e\" \"c d e\"",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
      gridTemplateAreas: "\"a b\" \"c c\" \"d d\" \"e e\"",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr 1fr",
      gridTemplateAreas: "\"a b\" \"c d\" \"e e\"",
    },
  },

  summaryPerformance: {
    display: "grid",
    gridTemplateColumns: "2fr 1fr",
    gridTemplateRows: "auto",
    gridTemplateAreas: "\"a e\" \"c e\" \"d e\"",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr",
      gridTemplateAreas: "\"a\" \"b\" \"c\" \"d\" \"e\"",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr",
      gridTemplateAreas: "\"a\" \"b\" \"c\" \"d\" \"e\"",
    },
  },

  infoPerformance: {
    // display: "grid",
  },
  infoPerformanceA: {
    gridArea: "a",
    borderRadius: "10px",

  },
  infoPerformanceSummary: {
    gridArea: "a",
    borderRadius: "5px",
  },
  infoPerformanceB: {
    gridArea: "b",
  },
  infoPerformanceC: {
    gridArea: "c",
  },
  infoPerformanceD: {
    gridArea: "d",
  },
  infoPerformanceE: {
    gridArea: "e",
    "& p": {
      marginBottom: 10,
    },
    "& h3": {
      [theme.breakpoints.down("sm")]: {
        marginBottom: 10,
      },
    },

  },
  infoPerformanceECardContainer: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gridTemplateRows: "auto 1fr",
    height: "100%",
  },
  growthStatus: {
    margin: "0 0 12px 0",
  },
  infoPerformanceContent: {
    position: "relative",
    height: "100%",
    paddingTop: "60px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    "& h4": {
      fontSize: 28,
      fontWeight: 700,
      [theme.breakpoints.down("sm")]: {
        fontSize: 16,
      },
    },
    "& p": {
      fontSize: 14,
      fontWeight: 300,
      [theme.breakpoints.down("sm")]: {
        fontSize: 12,
      },
    },
    "& span": {
      fontSize: 14,
      fontWeight: 300,
      [theme.breakpoints.down("sm")]: {
        fontSize: 12,
      },
    },
  },
  labelPerformance: {
    top: "15px",
    left: "0",
    padding: "0 15px",
    width: "100%",
    position: "absolute",
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  dataPerformance: {
    width: "100%",
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    "& h4": {
      display: "flex",
      alignItems: "baseline",
      fontSize: 28,
      fontWeight: 700,
      marginRight: 20,
      [theme.breakpoints.down("sm")]: {
        fontSize: 20,
      },
      "& span": {
        marginLeft: 5,
        fontSize: 16,
        fontWeight: 300,
        [theme.breakpoints.down("sm")]: {
          fontSize: 16,
        },
      },
    },
    "& h5": {
      fontSize: 24,
      fontWeight: 700,
      display: "flex",
      alignItems: "center",
    },
  },

  infoPerformanceEContent: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gridTemplateRows: "1fr 1fr",
    gap: 10,
    [theme.breakpoints.down("sm")]: {
      padding: 0,
    },
  },

  infoPerformanceEContentItem: {
    borderRadius: 10,
    border: "1px solid #E2E8F0",
  },


  persentaseUp: {
    color: "#14AE5C",
    fontSize: 14,
    fontWeight: 700,

  },

  persentaseDown: {
    color: "red",
    fontSize: 14,
    fontWeight: 700,

  },

  chart: {
    height: "100%",
  },

  infoCard: {
    display: "block",
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



  economics: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr",
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    gap: 10,
    marginTop: 10
  },
  economicsCard: {
    border: "1px solid #E2E8F0",
    borderRadius: 10,
  },
  economicsItems: {
    display: "flex",
    flexDirection: "row",
    gap: 15,
    alignItems: "center",
  },
  economicsIcons: {
    [theme.breakpoints.down("sm")]: {
      width: 40,
      height: 40,
    },
    width: 40,
    height: 40,
    position: "relative",
    backgroundColor: theme.custom.background.main,
    "& svg": {
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
      width: "26px !important",
      height: "auto"
    },
  },
  economicsInfo: {
    "& h4": {
      fontWeight: "bold",
      fontSize: 18
    }
  },
  echartsContainer: {
    height: "100%",
  },

  // report section

  reportECardContainer: {
    display: "flex",
    flexDirection: "row",
  },
  reportEContentItemDescription: {
    flex: "2", // Take up 2/3 of the width
    paddingRight: theme.spacing(2), // Add spacing if needed
    fontFamily: "Lato",
  },
  reportEContentItemButton: {
    flex: "1", // Take up 1/3 of the width
    paddingLeft: theme.spacing(1), // Add spacing if needed
  },

  btnDownload: {
    color: "white",
    minWidth: "unset !important",
    background: "#474DA4",
    marginRight: "5px",
    borderRadius: "6px",
    padding: "10.5px",
    "&:hover": {
      color: "white",
      background: "#101558"
    },
    "& svg": {
      width: "20px",
      height: "20px"
    }
  },
  btnDownloadIcon: {
    paddingRight: "2px"
  }
}));

export { useStyles }