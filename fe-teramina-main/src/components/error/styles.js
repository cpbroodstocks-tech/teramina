import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  contentError: {
    display: "flex",
    alignContent: "center",
    flexDirection: "column",
    verticalAlign: "middle",
    textAlign: "center",
    minHeight: "50vh",
    justifyContent: "center",
  },
  lgError: {
    "& img": {
      height: "220px",
      [theme.breakpoints.down("sm")]: {
        height: "180px",
      },
    },
        
  }

}));

export { useStyles };
