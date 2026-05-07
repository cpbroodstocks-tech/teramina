import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  container: {
    width: "444px",
    maxWidth: "100%",
    marginTop: "40px",
    [theme.breakpoints.down("sm")]: {
      width: "100%",
    },
  },
}));

export { useStyles };