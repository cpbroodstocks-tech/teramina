import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  contentError: {
    display: "flex",
    alignContent: "center",
    flexDirection: "column",
    verticalAlign: "middle",
    textAlign: "center",
    height: "50vh",
    justifyContent: "center",
  },
  lgError: {
    "& img": {
      height: "400px",
      [theme.breakpoints.down("sm")]: {
        height: "300px",
      },
    },
        
  }

}));

export { useStyles };