import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  filterWrapper: {
    display: "grid",
    gridTemplateColumns: "2fr 2fr 2fr 2fr 1fr 1fr",
    gap: 18,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    }
  },

  cardCheckboxContainer: {
    display: "flex",
    alignItems: "center",
    flexWrap: "nowrap",
    justifyContent: "space-between",
    marginBottom: "15px",
    width: "294px",
  },
  sectionContainer: {
    marginTop: 40,
  },
  sectionTitle: {
    fontWeight: 700,
    fontSize: "24px",
    lineHeight: "29px",
    color: "#333333",
  },

  wrapperCycleSelected: {
    display: "flex",
    alignItems: "center",
    flexWrap: "nowrap",

    [theme.breakpoints.down("sm")]: {
      flexDirection: "column",
      marginBottom: "15px",
    }
  },

  itemCycleSelected: {
    display: "flex",
    alignItems: "center",
    marginRight: "30px",
    color: "#737373",
    fontSize: "14px",
    [theme.breakpoints.down("sm")]: {
      marginBottom: "15px",
    }
  },
  iconSquare: {
    width: "18px",
    height: "18px",
    borderRadius: "4px",
    marginRight: "6px",
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
    paddingLeft: "8px",
    paddingRight: "20px",
  },

  cardContent: {
    padding: "0px 20px 20px 20px",
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

  itemChart: {
    marginBottom: "8px",
    padding: "10px 20px",
  },

  echartsContainer: {
    height: "100%",
  },

  btnDownload: {
    border: "1px #00B1A9 solid",
    color: "#00B1A9",
    "& fieldset": {
      boxShadow: "0px 1px 2px rgba(16, 24, 40, 0.05)",
      border: "none",
      borderRadius: 8,
    },
    [theme.breakpoints.down("sm")]: {
      height: 40,
    },
    "& svg": {
      marginRight: "8px",
    }

  },

  filterSelectOptionCustom: {
    paddingRight: "10px !important",
  },

  sectionBottom: {
    padding: 30,
    [theme.breakpoints.down("sm")]: {
      padding: "20px 0px",
    },
    display: "flex",
    alignItems: "center",
    verticalAlign: "middle",
    justifyContent: "space-between"
  }
}));

export { useStyles }