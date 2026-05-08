import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  overlay: {
    position: "absolute",
    display: "block",
    width: "100%",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "#7277d2b3",
    zIndex: 2,
    cursor: "pointer",
  },
  headerLogo: {
    position: "fixed",
    top: "30px",
    left: "30px",
  },
  contentSignUp: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    [theme.breakpoints.down("sm")]: {
      flexDirection: "column",
      height: "calc(100vh - 170px)",
      alignItems: "center",
    },


  },
  leftContent: {
    backgroundImage: "url(/assets/images/bg-left.png)",
    backgroundRepeat: "no-repeat",
    backgroundPosition: "center",
    backgroundSize: "cover",
    backgroundColor: "#9FA2D6",
    display: "flex",
    flex: "45%",
    alignContent: "center",
    justifyContent: "center",
    flexWrap: "wrap",
    [theme.breakpoints.down("sm")]: {
      flex: "100%",
      position: "absolute",
      top: "30%",
      zIndex: 2,
    },

  },
  formWrapper: {
    width: "352px",
    height: "254px",
    padding: "46px",
    borderRadius: "5px",
    boxShadow: "0px 6px 8px rgba(0, 0, 0, 0.05)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    backgroundColor: "#fff",
    [theme.breakpoints.down("sm")]: {
      backgroundColor: "#fff",
    },
  },
  headingSmallSignUp: {
    fontSize: "14px",
    color: "#757575",
  },
  headingSignUp: {
    fontSize: "24px",
    marginBottom: "46px"
  },
  btnSignUp: {
    fontSize: "16px",
    fontFamily: "Lato",
    color: "#000",
    fontWeight: "500",
    fontStyle: "normal",
    padding: "10px 10px",
    border: "1px solid #1E1E1E",
    borderRadius: "3px"
  },
  avatarGoogle: {
    width: 23,
    height: 23
  },
  rightContent: {
    backgroundImage: "url(/assets/images/imgSignUp.png)",
    backgroundRepeat: "no-repeat",
    backgroundPosition: "center",
    backgroundSize: "cover",
    width: "55%",
    position: "relative",
    zIndex: "1",
    height: "calc(100vh - 174px)",
    [theme.breakpoints.down("sm")]: {
      boxShadow: "inset 0 0 0 2000px #474da447",
      flex: "100%",
      width: "100%",
    },

  }
}));

export { useStyles };