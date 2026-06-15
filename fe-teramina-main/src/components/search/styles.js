import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  wrapperSearch: {
    display: "inline-flex",
    maxWidth: "100%",
    flex: "1 1 260px",
    "& input": {
      width: "342px",
      [theme.breakpoints.down("sm")]: {
        width: "100%",
      }
    },
    "& label": {
      top: "-5px"
    },
    "& fieldset": {
      border: "1px solid #E2E8F0",
      borderRadius: 3,
    },
    "& .MuiTextField-root": {
      maxWidth: "100%",
    },

  },
  bgIcon: {
    marginLeft: "12px",
    backgroundColor: "#474DA4",
    borderRadius: "50%",
    width: "40px",
    height: "40px",
    padding: "10px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    "& svg": {
      color: "#fff",
    }
  }

}));

export { useStyles };
