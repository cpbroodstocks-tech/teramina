import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  footer: {
    left: 0,
    bottom: 0,
    width: "100%",
    backgroundColor: theme.custom.background.main,
    color: "white",
    textAlign: "center",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding:"20px",
    // height: "174px",

    "& h5": {
      color: "white",
    }
  },
  copyrigth: {
    fontSize: "24px",
    [theme.breakpoints.down("sm")]: {
      fontSize: "16px",
    }
  },
  lgFooter: {
    height: "75px",
    width: "auto",
    [theme.breakpoints.between("sm", "md")]: {
      height: "50px",
    },
  }

}));

export { useStyles };