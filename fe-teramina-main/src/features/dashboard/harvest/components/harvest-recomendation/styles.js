import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  harvestInfo: {
    marginTop: "12px",
  },
  table: {
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
