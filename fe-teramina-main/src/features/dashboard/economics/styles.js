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

  tooltipInfo: {
    cursor: "pointer",
  },

  economics: {
    display: "grid",
    gap: 10,
    marginTop: 10,
    gridTemplateColumns: "3fr 5fr 5fr",
    gridTemplateRows: "1fr 1fr",
    gridTemplateAreas: "\"a b c\" \"a d e\"",
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
      gridTemplateAreas: "\"a a\" \"b c\" \"d e\"",
    },
    "& > div:nth-child(1)": {
      gridArea: "a",
    },
    "& > div:nth-child(2)": {
      gridArea: "b",
    },
    "& > div:nth-child(3)": {
      gridArea: "c",
    },
    "& > div:nth-child(4)": {
      gridArea: "d",
    },
    "& > div:nth-child(5)": {
      gridArea: "e",
    }
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
    height: "100%",
  },
  economicsIcons: {
    [theme.breakpoints.down("sm")]: {
      width: 40,
      height: 40,
    },
    width: 60,
    height: 60,
    backgroundColor: theme.custom.background.main,
    "& svg": {
      fontSize: 30,
    },
  },

  costBreakdown: {
    display: "grid",
    gridTemplateColumns: "3fr 2fr",
    width: "100%",
    gap: 10,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr",
      gridTemplateRows: "1fr",
      width: "100%",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      width: "100%",
      gridTemplateColumns: "330px 1fr",
    }
  },

  dataDiagram: {
    [theme.breakpoints.down("sm")]: {
      height: 300,
    },
  },

  harvestRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr",
    gap: 10,
    marginTop: 15,
    borderRadius: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    "& h4": {
      fontSize: 28,
      textAlign: "left",
    },
    "& p": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
      marginBottom: 17,
    },
    "& span": {
      fontSize: 14,
      color: "#8f8f8f",
      fontWeight: 300,
      marginLeft: 5,
    },
  },

  wrapInfoCard: {
    padding: "15px 20px",
    [theme.breakpoints.down("sm")]: {
      padding: "10px 20px",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      padding: "10px 20px",
    },
  },

  productionStatus: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 2fr",
    gridTemplateRows: "1fr 1fr",
    gridTemplateAreas: "\"a b e\" \"c d e\"",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
      gridTemplateAreas: "\"a b\" \"c d\" \"e e\"",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr 1fr",
      gridTemplateAreas: "\"a b\" \"c d\" \"e e\"",
    },
    "& > div:nth-child(1)": {
      gridArea: "a",
    },
    "& > div:nth-child(2)": {
      gridArea: "b",
    },
    "& > div:nth-child(3)": {
      gridArea: "c",
    },
    "& > div:nth-child(4)": {
      gridArea: "d",
    },
    "& > div:nth-child(5)": {
      gridArea: "e",
      "& p": {
        marginBottom: 10,
      },
      "& h3": {
        [theme.breakpoints.down("sm")]: {
          marginBottom: 10,
        },
      },
    }
  },

  productionStatusSummary: {
    display: "grid",
    gridTemplateColumns: "1fr 2fr",
    gridTemplateRows: "1fr 1fr 1fr",
    gridTemplateAreas: "\"a d\" \"b d\" \"c d\"",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr",
      gridTemplateAreas: "\"a\" \"b\" \"c\" \"d\"",
    },
    [theme.breakpoints.between("sm", "lg")]: {
      gridTemplateColumns: "1fr",
      gridTemplateAreas: "\"a\" \"b\" \"c\" \"d\"",
    },
    "& > div:nth-child(1)": {
      gridArea: "a",
    },
    "& > div:nth-child(2)": {
      gridArea: "b",
    },
    "& > div:nth-child(3)": {
      gridArea: "c",
    },
    "& > div:nth-child(4)": {
      gridArea: "d",
    },
    "& > div:nth-child(5)": {
      gridArea: "e",
      "& p": {
        marginBottom: 10,
      },
      "& h3": {
        [theme.breakpoints.down("sm")]: {
          marginBottom: 10,
        },
      },
    }
  },

  infoProductionStatus: {
    // display: "grid",
  },

  infoProductionStatusContent: {
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

  infoProductionStatusEContent: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gridTemplateRows: "1fr 1fr",
    gap: 5,
    [theme.breakpoints.down("sm")]: {
      padding: 0,
    },
  },

  infoProductionStatusEContentItem: {
    borderRadius: 10,
    border: "1px solid #E2E8F0",
  },


  persentaseUp: {
    color: "#14AE5C",
    fontSize: 24,
    fontWeight: 700,

  },

  persentaseDown: {
    color: "red",
    fontSize: 24,
    fontWeight: 700,

  },

  chart: {
    height: "100%",
  },

  InfoCard: {
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
  echartsContainer: {
    height: "100%",
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
}));

export { useStyles }