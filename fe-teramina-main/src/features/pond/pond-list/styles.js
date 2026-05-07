import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  toolbarTable: {
    display: "flex",
    justifyContent: "space-between",
    verticalAlign: "middle",
    marginBottom: "20px",
  },
  leftSection: {
    display: "flex",
    // alignItems: "center", /* This aligns items in the left section vertically */
  },
  table: {
    [theme.breakpoints.down("sm")]: {
      width: "1000px",
    },
    "& th": {
      fontFamily: "Lato",
      background: "#F8FAFC",
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
  btnBack: {
    padding: "0",
    display: "flex",
    alignItems: "center",
    color: "#333333",
    background: "transparent",
    marginBottom: "24px",
    borderRadius: "50px",
    "&:hover": {
      color: "#333333",
      background: "transparent",
    },
  },
  btnUploadDownload: {
    padding: "0",
    display: "flex",
    alignItems: "center",
    color: "#333333",
    background: "transparent",
    "&:hover": {
      color: "#333333",
      background: "transparent",
    },
  },
  btnBackText: {
    fontWeight: "500",
    fontSize: "14px",
    lineHeight: "17px",
    marginLeft: "8px",
  },
  btnBackIcon: {
    width: "38px",
    height: "38px",
    padding: "7px",
    background: "rgba(71, 77, 164, 0.43)",
    borderRadius: "13px",
    fontSize: "24px",
    color: "#FFFFFF",
  },
  btnIconUploadDownload: {
    width: "48px",
    height: "48px",
    padding: "10px",
    background: "rgba(71, 77, 164, 0.43)",
    borderRadius: "13px",
    fontSize: "24px",
    color: "#FFFFFF",
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