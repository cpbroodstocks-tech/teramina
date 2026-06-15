import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  toolbarTable: {
    display: "flex",
    justifyContent: "space-between",
    verticalAlign: "middle",
    marginBottom: "20px",
    gap: 12,
    flexWrap: "wrap",
  },
  table: {
    fontFamily: "Lato",
    "& th": {
      background: "#F8FAFC",
      fontFamily: "Lato",
    },
    "& th:nth-child(1)": {
      width: "auto",
    },
    "& th:nth-child(2)": {
      width: "auto",
    },
    "& th:nth-child(3)": {
      width: "auto",
    },
    "& th:nth-child(4)": {
      width: "auto",
    },
    "& th:nth-child(5)": {
      width: "auto",
    },
    "& th:nth-child(6)": {
      width: "240px",
    },
    "& td": {
      fontFamily: "Lato",
    }
  },
  pageTitle: {
    fontWeight: 700,
    fontSize: "40px",
    color: "#333333",
    textTransform: "uppercase",
    marginBottom: "16px",
    [theme.breakpoints.down("sm")]: {
      fontSize: "24px",
    }
  },
  sectionTitle: {
    fontWeight: 700,
    fontSize: "24px",
    lineHeight: "29px",
    color: "#333333",
    marginBottom: "72px",
    textTransform: "unset",
    [theme.breakpoints.down("sm")]: {
      fontSize: "18px",
      marginBottom: "20px",
    }
  },
  actionContainer: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    flexWrap: "nowrap"
  },
  btnViewMore: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 18px",
    width: "132px",
    color: "#161616",
    background: "rgba(71, 77, 164, 0.32)",
    borderRadius: "6px",
    "&:hover": {
      color: "#161616",
      background: "rgba(71, 77, 164, 0.6)",
    },
  },
  btnViewMoreText: {
    fontWeight: "500",
    fontSize: "14px",
    lineHeight: "17px",
  },
  btnViewMoreIcon: {
    fontSize: "14px",
  },
}));

export { useStyles }
