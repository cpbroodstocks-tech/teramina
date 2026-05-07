import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  filterWrapper: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr 1fr",
    gap: 18,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    }
  },
  filterFormControl: {
    width: "100%",
    backgroundColor: "white",
    border: "none",
    borderRadius: 8,

    "& svg": {
      background: "#0000001f",
      borderRadius: "50%",
    },
    "& fieldset": {
      boxShadow: "0px 1px 2px rgba(16, 24, 40, 0.05)",
      border: "none",
      borderRadius: 8,
    }
  },
  filterSelectOption: {
    borderRadius: 10,
    color: "black",
    border: "none",
    fontSize: 14,
    "& em": {
      fontStyle: "normal !important"
    },
    "&:hover": {
      "& fieldset": {
        border: "2px solid #5383b3bf!important"
      }
    }
  },
  filterButton: {
    alignSelf: "flex-start",
    padding: "7.82px 12px",
    whiteSpace: "nowrap",
    background: "#474DA4",
    color: "white",
    "&:hover": {
      background: "#101558",
      color: "white"
    }
  },
  filterButtonDisabled: {
    background: "#6f74b3",
    color: "white !important",
    "&:hover": {
      background: "#6f74b3",
      color: "white !important",
    }
  }
}))

export { useStyles };