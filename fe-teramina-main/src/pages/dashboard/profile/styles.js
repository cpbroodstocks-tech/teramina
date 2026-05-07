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
  containerProfileFoto: {
    width: "117px",
    height: "117px",
    position: "relative",
    borderRadius: "50%",
    overflow: "hidden",
  },
  wrapProfileFoto: {
    display: "flex",
    alignItems: "center",
    verticalAlign: "end",
    gap: "27px",
    marginBottom: "35px",
  },
  imgProfileFoto: {
    width: "100%",
    height: "auto",
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
  },
  wrapUsername: {
    flex: 1,
  },
  textUsername: {
    fontFamily: "Lato",
    fontSize: "32px",
    fontWeight: 600,
  },
  infoCard: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    border: "1px solid #E2E8F0",
    borderRadius: "10px",
    marginBottom: "12px",
    padding: "12px 20px",
    height: "80px",
  },
  titleField: {
    fontFamily: "Lato",
    fontStyle: "normal",
    fontSize: "14px",
    fontWeight: 400,
  },
  valueField: {
    fontFamily: "Lato",
    fontStyle: "normal",
    fontSize: "16px",
    fontWeight: 700,
  },
  btnEditProfile: {
    background: "#474DA4",
    fontSize: "16px",
    fontWeight: 800,
    marginTop: "20px",
    borderRadius: "15px",
    width: "100%",
    textTransform: "uppercase",
    padding: "8px",
    "&:hover": {
      background: "#101558",
      color: "#FFFFFF",
    },
  },

  title: {
    marginBottom: "32px",
    fontSize: "22px",
    fontWeight: 700,
  },
  input: {
    width: "100%",
  },
  label: {
    margin: "16px 0 8px 0",
    fontSize: "14px",
  },
  requiredLabel: {
    position: "relative",
    "&:after": {
      content: "\" *\"",
      position: "relative",
      color: "#EF3061",
    }
  },

  circular: {
    width: "29px !important",
    height: "29px !important",
  },
}));

export { useStyles };