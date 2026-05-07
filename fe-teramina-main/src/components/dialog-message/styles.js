import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  dialog: {
    transitionDelay: "0.5s",
  },
  dialogContent: {
    width: "400px",
    maxWidth: "100%",
    padding: "32px !important",
  },
  dialogImg: {
    width: "124px",
    maxWidth: "100%",
    margin: "0 auto",
    "& img": {
      width: "100%",
    },
  },
  dialogText: {
    marginTop: "24px",
    textAlign: "center",
    fontFamily: "Lato",
    fontWeight: 700,
    fontSize: "24px",
    lineHeight: "29px",
    color: "#4F4F4F",
  },
}));

export { useStyles };