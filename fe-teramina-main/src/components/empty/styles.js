import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  contentEmpty: {
    display: "flex",
    alignContent: "center",
    flexDirection: "column",
    verticalAlign: "middle",
    textAlign: "center",
    minHeight: "70vh",
    justifyContent: "center",
  },
  lgEmpty: {
    "& img": {
      width: "360px",
      [theme.breakpoints.down("sm")]: {
        width: "240px",
      },
    }
  }

}));

export { useStyles };
