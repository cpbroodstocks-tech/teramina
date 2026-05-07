import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  btnLanguage: {
    display: "flex",
    gap: "12px",
    padding: (props) => (props.isDashboard ? "6px 12px" : "12px 20px"),
    borderRadius: "8px",

    [theme.breakpoints.between("481", "1025")]: {
      padding: (props) => !props.isDashboard && "8px 16px",
    },
    [theme.breakpoints.down("480")]: {
      padding: (props) => !props.isDashboard && "10px 16px",
    },
  },
  textLanguage: {
    fontFamily: "Lato",
    fontSize: (props) => (props.isDashboard ? "14px" : "18px"),
    lineHeight: "normal",

    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "14px",
    },
    [theme.breakpoints.down("480")]: {
      fontSize: (props) => (props.isDashboard ? "14px" : "20px"),
    },
  },
  menuLanguage: {
    mt: "8px",

    "& .MuiPaper-root": {
      boxShadow: "0px 4px 24px 0px #AAACB44D",
      borderRadius: "12px",
      padding: "8px 0",
    },
  },
  menuItemLanguage: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
  },
  labelLanguage: {
    fontFamily: "Lato",
    fontSize: (props) => (props.isDashboard ? "14px" : "16px"),
    lineHeight: "normal",

    [theme.breakpoints.between("481", "1025")]: {
      fontSize: "14px",
    },
    [theme.breakpoints.down("480")]: {
      fontSize: (props) => (props.isDashboard ? "14px" : "12px"),
    },
  },
}));

export { useStyles };
