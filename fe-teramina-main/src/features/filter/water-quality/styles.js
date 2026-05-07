import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  containerPoppoverSiklus: {
    borderRadius: 8,
    width: 170,
    padding: "6px 16px",
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
  },
  itemSiklus: {
    display: "flex",
    alignItems: "center",
    padding: "5px 0",
    "& > span": {
      padding: 0,
      marginRight: 10,
    }
  },
  containerPoppoverKualitasAir: {
    borderRadius: 8,
    width: 294,
    padding: "6px 16px",
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
  },
  itemKualitasAir: {
    display: "flex",
    alignItems: "center",
    padding: "5px 0",
    "& > span": {
      padding: 0,
      marginRight: 10,
    }
  },
  filterWrapper: {
    display: "grid",
    gridTemplateColumns: "100px 100px 100px 100px 100px 100px",
    gap: 4,
    [theme.breakpoints.down("sm")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    [theme.breakpoints.between("481", "1100")]: {
      gridTemplateColumns: "1fr 1fr",
    },
    [theme.breakpoints.between("1100", "1201")]: {
      gridTemplateColumns: "1fr 1fr 1fr",
    },
  },
  filterFormControl: {
    backgroundColor: "white",
    border: "none",
    borderRadius: 6,
    "& fieldset": {
      boxShadow: "0px 1px 2px rgba(16, 24, 40, 0.05)",
      border: "none",
      borderRadius: 8,
    }
  },
  filterSelectOptionCustom: {
    paddingRight: "0 !important",
  },
  filterSelectOption: {
    height: 32,
    paddingLeft: 10,
    paddingRight: 10,
    paddingTop: 6,
    paddingBottom: 6,
    background: "#FCFCFC",
    boxShadow: "0px 1px 2px rgba(0, 0, 0, 0.12)",
    borderRadius: 6,
    border: "0.50px #D6D6D6 solid",
    justifyContent: "center",
    alignItems: "center",
    gap: 4,
    display: "inline-flex",
    color: "#004744",
    "& em": {
      fontStyle: "normal !important"
    },

  },
  filterButton: {
    width: "100%",
    alignSelf: "flex-start",
    padding: "7.82px 12px",
    whiteSpace: "nowrap",
    height: 32,
    paddingLeft: 10,
    paddingRight: 10,
    paddingTop: 6,
    paddingBottom: 6,
    background: "#FCFCFC",
    boxShadow: "0px 1px 2px rgba(0, 0, 0, 0.12)",
    borderRadius: 6,
    border: "0.50px #D6D6D6 solid",
    justifyContent: "center",
    alignItems: "center",
    gap: 4,
    display: "inline-flex",
    color: "#004744",
    fontWeight: "300",
    fontFamily: "Lato",
  },
  filterButtonDisabled: {
    background: "#6f74b3",
    color: "white !important",
    "&:hover": {
      background: "#6f74b3",
      color: "white !important",
    }
  },

  typeChartWrapper: {
    display: "inline-flex",
    border: "1px #E0E0E0 solid",
    flexWrap: "wrap",
    boxShadow: "none",
    [theme.breakpoints.down("sm")]: {
      marginTop: 20,
    }
  },
  groupedTypeCart: {
    margin: theme.spacing(0.5),
    border: 0,
    "&.Mui-disabled": {
      border: 0,
    },
    "&:not(:first-of-type)": {
      borderRadius: theme.shape.borderRadius,
    },
    "&:first-of-type": {
      borderRadius: theme.shape.borderRadius,
    },
  },

  typeChartButton: {
    borderRadius: "8px !important",
    padding: 10,
    margin: "0 5px",
    height: 44,
    width: 44,
    border: "none",
    display: "flex",
    alignItems: "baseline",
    "&.Mui-selected": {
      background: "#004744",
    },
  },

  wrapperToolbarFilter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
    [theme.breakpoints.down("sm")]: {
      flexDirection: "column",
      marginBottom: 10
    }
  },

  roundCheckbox: {
    "& svg": {
      width: "16px",
      height: "16px",
      color: "#008E87",
    }
  }
}))

export { useStyles };