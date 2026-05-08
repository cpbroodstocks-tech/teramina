import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  sectionContainer: {
    marginTop: 40
  },
  sectionTitle: {
    fontWeight: 700,
    fontSize: "24px",
    lineHeight: "29px",
    color: "#333333",
  },
  feedingForecast: {
    display: "grid",
    gridTemplateColumns: "2fr 5fr",
    marginTop: 10,
    gap: 15,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr",
    },
  },
  feedingForecastLeft: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 15,
    paddingRight: "15px",
    borderRight: "1px solid #E2E8F0",
    [theme.breakpoints.down("sm")]: {
      paddingRight: "unset",
      borderRight: "unset",
      paddingBottom: "15px",
      borderBottom: "1px solid #E2E8F0",
    },
  },
  feedingForecastRight: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr",
    gap: 15,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
  },
  productionEconomicForecast: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr",
    gridTemplateRows: "1fr auto",
    gridTemplateAreas: "\"a b c d\" \"e e f f\"",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
      gridTemplateAreas: "\"a b\" \"c d\" \"e e\" \"f f\"",
    },
  },
  productionEconomicForecastA: {
    gridArea: "a"
  },
  productionEconomicForecastB: {
    gridArea: "b"
  },
  productionEconomicForecastC: {
    gridArea: "c"
  },
  productionEconomicForecastD: {
    gridArea: "d"
  },
  productionEconomicForecastE: {
    gridArea: "e"
  },
  productionEconomicForecastF: {
    gridArea: "f"
  },


  productionFeedingForecast: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr",
    gridTemplateRows: "1fr auto",
    gridTemplateAreas: "\"a b c d\" \"e e f f\"",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
      gridTemplateAreas: "\"a b\" \"c d\" \"e e\" \"f f\"",
    },
  },
  productionFeedingForecastA: {
    gridArea: "a"
  },
  productionFeedingForecastB: {
    gridArea: "b"
  },
  productionFeedingForecastC: {
    gridArea: "c"
  },
  productionFeedingForecastD: {
    gridArea: "d"
  },
  productionFeedingForecastE: {
    gridArea: "e"
  },
  productionFeedingForecastF: {
    gridArea: "f"
  },

  infoIconContainer: {
    flex: "0 0 20px",
    padding: 0,
  },
  infoIcon: {
    fontSize: "16px",
  },
  card: {
    borderRadius: "10px",
  },
  cardTitleContainer: {
    display: "flex",
    alignItems: "center",
    flexWrap: "nowrap",
    justifyContent: "space-between",
  },
  cardTitleLabelContainer: {
    display: "flex",
    flexWrap: "nowrap",
    alignItems: "center",
    width: "100%",
  },
  cardTitleLabelColor: {
    flex: "0 0 21px",
    height: "21px",
    marginRight: "8px",
  },
  cardTitle: {
    flex: "1 1 auto",
    fontWeight: 400,
    fontSize: "16px",
    lineHeight: "24px",
    letterSpacing: "-0.02em",
    color: "#1E1E1E",
    paddingRight: "20px",
  },
  cardValue: {
    marginTop: 22,
    fontWeight: 700,
    fontSize: "28px",
    lineHeight: "24px",
    color: "#1E1E1E",
    "& span": {
      fontSize: "16px",
      fontWeight: 300,
    }
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
  echartsContainer: {
    height: "100%",
  },
}));

export { useStyles }