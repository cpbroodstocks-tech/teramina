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
    zIndex: 3,
    [theme.breakpoints.down("sm")]: {
      top: 16,
      left: 16,
    },
  },
  contentSignIn: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: "calc(100vh - 60px)",
    [theme.breakpoints.down("sm")]: {
      minHeight: "calc(100vh - 55px)",
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
      flex: "1 1 100%",
      width: "100%",
      padding: "96px 16px 32px",
      zIndex: 2,
    },

  },
  formWrapper: {
    width: "min(420px, calc(100vw - 32px))",
    minHeight: "254px",
    padding: "46px",
    borderRadius: "12px",
    boxShadow: "0px 6px 8px rgba(0, 0, 0, 0.05)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    backgroundColor: "#fff",
    [theme.breakpoints.down("sm")]: {
      padding: "32px 24px",
    },
  },
  headingSmallSignIn: {
    fontSize: "14px",
    color: "#757575",
  },
  headingSignIn: {
    fontSize: "24px",
    marginBottom: "46px"
  },
  btnSignIn: {
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
    width: "75%",
    position: "relative",
    zIndex: "1",
    height: "calc(100vh - 60px)",
    [theme.breakpoints.down("sm")]: {
      display: "none",
    },

  }
}));

export { useStyles };
