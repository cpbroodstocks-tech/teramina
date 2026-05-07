import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  btnDelete: {
    minWidth: "unset !important",
    marginRight: "5px",
    padding: "10.5px",
    color: "#161616",
    background: "rgba(71, 77, 164, 0.32)",
    borderRadius: "6px",
    "&:hover": {
      color: "#161616",
      background: "rgba(71, 77, 164, 0.6)",
    },
    "& svg": {
      width: 20,
      height: 20,
    },
  },
}));

export { useStyles }