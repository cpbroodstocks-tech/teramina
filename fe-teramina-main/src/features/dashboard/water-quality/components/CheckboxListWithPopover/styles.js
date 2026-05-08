import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  cardCheckboxContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    width: 300,
  },
  checkbox: {
    display: "flex",
    alignItems: "center",
  },
  columns: {
    display: "flex",
    justifyContent: "space-between",
  },
  column: {
    flex: "1 1 33%",
  },
  popoverContent: {
    padding: theme.spacing(2),
  },
}));

export { useStyles }