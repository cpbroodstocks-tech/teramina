import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  loader: {
    display: "flex",
    justifyContent: "center",
    marginTop: "20vh",
  },
  imgLoading: {
    height: "50px",
  }
}));

export { useStyles };