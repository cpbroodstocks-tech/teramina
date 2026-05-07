import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  dialogContent: {
    maxWidth: "100%",
  },
  dialogText: {
    color: "rgba(0, 0, 0, 0.87)",
  },
  btnYesModal: {
    background: "#474DA4",
    "&:hover": {
      background: "#474DA4",
      color: "#FFFFFF",
    },
  }
}));

export { useStyles };