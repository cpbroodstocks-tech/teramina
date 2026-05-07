import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  containerHome: {
    [theme.breakpoints.up("sm")]: {
      minHeight: "calc(100vh - 254px)",
    },
    [theme.breakpoints.down("sm")]: {
      marginBottom: 40,
    },
    [theme.breakpoints.between("sm", "md")]: {
      maxWidth: "700px",
    },
  },
  contentHome: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: "80px",
    [theme.breakpoints.up("sm")]: {
      flexWrap: "wrap",
    },
    [theme.breakpoints.down("sm")]: {
      marginTop: "40px",
      flexDirection: "column-reverse",
    },

  },
  leftContent: {
    display: "flex",
    flex: "50%",
    flexDirection: "column",
    verticalAlign: "middle",
    alignContent: "center",
    justifyContent: "center",
  },
  headingHome: {
    fontSize: 48,
    marginBottom: "24px",
    [theme.breakpoints.down("sm")]: {
      fontSize: 32,
    },
    [theme.breakpoints.between("sm", "md")]: {
      fontSize: "32px",
    },
  },
  captionHome: {
    fontSize: 24,
    marginBottom: "48px",
    [theme.breakpoints.down("sm")]: {
      fontSize: "16px",
    },
    [theme.breakpoints.between("sm", "md")]: {
      fontSize: "14px",
    },
  },
  btnSignUp: {
    fontSize: "24px",
    [theme.breakpoints.down("sm")]: {
      fontSize: "16px",
    },
    [theme.breakpoints.between("sm", "md")]: {
      fontSize: "16px",
    },
  },
  rightContent: {
    display: "flex",
    flex: "50%",
    justifyContent: "end",
    [theme.breakpoints.down("sm")]: {
      justifyContent: "center",
      margin: "0 0 40px 0",
    },
  },
  lgIntersect: {
    width: "auto",
    [theme.breakpoints.down("sm")]: {
      height: "250px",
    },
    [theme.breakpoints.between("sm", "md")]: {
      height: "250px",
    },
  }
}));

export { useStyles };