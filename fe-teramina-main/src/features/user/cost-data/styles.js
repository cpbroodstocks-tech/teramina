import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  titlePage: {
    fontFamily: "Lato",
    fontWeight: 700,
    fontSize: "40px",
    textTransform: "uppercase",
  },
  container: {
    width: "514px",
    maxWidth: "100%",
    background: "#FFFFFF",
    boxShadow: "0px 6px 8px rgba(0, 0, 0, 0.05)",
    borderRadius: "7px",
    padding: "40px",
    marginTop: "40px",
    [theme.breakpoints.down("sm")]: {
      width: "100%",
      padding: "20px",
      marginTop: "40px",
    },
  },
  title: {
    marginBottom: "32px",
    fontSize: "22px",
    fontWeight: 700,
  },
  circular: {
    width: "29px !important",
    height: "29px !important",
  },
  uploadForm: {
    display: "none"
  },
  cardFooter: {
    paddingLeft: "15px",
    paddingBottom: "15px"
  },
  dateSelector: {
    marginBottom: "22px",
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
}));

export { useStyles };