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
  column: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gridTemplateRows: "minmax(auto, 1fr) minmax(auto, 1fr)",
    gap: 15,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
      gridTemplateRows: "unset",
    },
  },
  status: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
  },
  adjustment: {
    display: "grid",
    gridTemplateColumns: "1fr 1.5fr 1.5fr",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr",
    },
  },
  dailyFeedingAdjustment: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr",
    gap: 15,
    marginTop: 10,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
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
  cardContent: {
    position: "relative",
    paddingTop: "60px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
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
  cardTitleContainer: {
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
  cardTitle: {
    flex: "1 1 auto",
    fontWeight: 400,
    fontSize: "16px",
    lineHeight: "24px",
    letterSpacing: "-0.02em",
    color: "#1E1E1E",
    whiteSpace: "nowrap",
  },
  cardValue: {
    fontWeight: 700,
    fontSize: "28px",
    lineHeight: "24px",
    color: "#1E1E1E",
    "& span": {
      fontSize: "16px",
      fontWeight: 300,
    }
  },
  feedInfoCardContainer: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gridTemplateRows: "auto 1fr",
    height: "100%",
  },
  feedInfo: {
    fontWeight: 700,
    fontSize: "24px",
    lineHeight: "29px",
    color: "#333333",
    marginBottom: "12px",
  },
  btnAddData: {
    marginTop: 20,
    display: "flex",
    alignItems: "center",
    cursor: "pointer",
  },
  addIconContainer: {
    width: "38px",
    height: "38px",
    background: "rgba(71, 77, 164, 0.98)",
    borderRadius: "13px",
    "&:hover": {
      background: "rgba(71, 77, 164, 0.98)",
      borderRadius: "13px",
    }
  },
  addIcon: {
    fontSize: "18px",
    color: "#FFFFFF",
  },
  addText: {
    marginLeft: 10,
    fontWeight: 300,
    fontSize: "16px",
    lineHeight: "24px",
    color: "#1E1E1E",
  },
  echartsContainer: {
    height: "100%",
  },
  table: {
    fontFamily: "Lato",
    [theme.breakpoints.down("sm")]: {
      width: "1000px",
    },
    "& th": {
      background: "#F8FAFC",
      fontWeight: 600,
      fontFamily: "Lato",
    },
    "& td": {
      fontFamily: "Lato",
    }
  },
  tableCellBorderBottom: {
    textAlign: "center",
    borderBottom: "4px solid rgba(224, 224, 224, 1)",
  },
  tableCellBorderAll: {
    border: "1px solid rgba(224, 224, 224, 1)",
  },
  realizationHeader: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginBottom: "20px",
  },
  realizationHeaderBtnContainer: {
    display: "flex",
    alignItems: "center",
  },
  realizationHeaderBtn: {
    background: "#474DA4",
    fontSize: "16px",
    fontWeight: 500,
    lineHeight: "24px",
    letterSpacing: "-0.02em",
    borderRadius: "3px",
    width: "auto",
    padding: "8px 16px",
    color: "#FFFFFF",
    [theme.breakpoints.down("sm")]: {
      fontSize: "12px",
      lineHeight: "16px",
    },
    "&:hover": {
      background: "#101558",
      color: "#FFFFFF",
    },
    "&:first-child": {
      marginRight: "12px",
    },
  },
  realizationHeaderBtnDisabled: {
    color: "#FFFFFF !important",
    opacity: "0.5 !important"
  },
  tableCellSpaceBetween: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
}));

export { useStyles }