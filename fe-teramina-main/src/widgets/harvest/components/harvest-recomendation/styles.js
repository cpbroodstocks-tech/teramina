import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  harvestInfo: {
    marginTop: "12px",
  },
  table: {
    [theme.breakpoints.down("sm")]: {
      width: "1000px",
    },
    "& th": {
      fontFamily: "Lato",
      background: "#F8FAFC",
    },
    "& td": {
      fontFamily: "Lato",
    }
  },

}));

export { useStyles }