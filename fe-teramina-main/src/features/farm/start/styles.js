import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  container: {
    margin: "0 auto",
    width: "500px",
    maxWidth: "100%",
    marginTop: "40px",
    display: "flex",
    flexDirection: "column",
    flexWrap: "wrap",
    justifyContent: "center",
    alignItems: "center",
    [theme.breakpoints.down("sm")]: {
      width: "100%",
      marginTop: "60px",
    },
  },
  imgStart: {
    display: "block",
    width: "400px",
    maxWidth: "100%",
    height: "auto",
  },
  descOne: {
    fontWeight: 400,
    fontSize: "24px",
    lineHeight: "29px",
    marginTop: "32px",
    [theme.breakpoints.down("sm")]: {
      fontSize: "18px",
      lineHeight: "23px",
    },
  },
  descTwo: {
    fontWeight: 700,
    fontSize: "40px",
    lineHeight: "48px",
    marginTop: "8px",
    [theme.breakpoints.down("sm")]: {
      fontSize: "32px",
      lineHeight: "40px",
    },
  },
  btnStart: {
    background: "#474DA4",
    fontSize: "16px",
    fontWeight: 800,
    borderRadius: "3px",
    marginTop: "37px",
    width: "364px",
    maxWidth: "100%",
    textTransform: "uppercase",
    padding: "8px",
    "&:hover": {
      background: "#474DA4",
      color: "#FFFFFF",
    },
    [theme.breakpoints.down("sm")]: {
      marginBottom: "20px",
    },
  }
}));

export { useStyles };