import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  contentNotFound: {
    display: "flex",
    alignContent: "center",
    justifyContent: "center",
    flexDirection: "column",
    verticalAlign: "middle",
    textAlign: "center",
    height: "100vh",
  },
  lg404: {
    "& img": {
      height: "300px",
    }
  }

}));

export { useStyles };