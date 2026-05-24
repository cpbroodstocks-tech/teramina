import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()((theme) => ({
  container: {
    maxWidth: 888,
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: 18,
    [theme.breakpoints.down("lg")]: {
      gridTemplateColumns: "1fr",
    }
  },
  column: {
    alignSelf: "flex-start",
    width: "444px",
    maxWidth: "100%",
    background: "#FFFFFF",
    boxShadow: "0px 6px 8px rgba(0, 0, 0, 0.05)",
    borderRadius: "7px",
    padding: "40px",
    marginTop: "40px",
    [theme.breakpoints.down("sm")]: {
      width: "100%",
      padding: "20px",
      marginTop: "60px",
    },
  },
  title: {
    marginBottom: "32px",
    fontSize: "22px",
    fontWeight: 700,
  },
  input: {
    width: "100%",
  },
  label: {
    margin: "16px 0 8px 0",
    fontSize: "14px",
  },
  requiredLabel: {
    position: "relative",
    "&:after": {
      content: "\" *\"",
      position: "relative",
      color: "#EF3061",
    }
  },
  btnSubmit: {
    background: "#474DA4",
    fontSize: "16px",
    fontWeight: 800,
    borderRadius: "3px",
    marginTop: "37px",
    width: "100%",
    textTransform: "uppercase",
    padding: "8px",
    "&:hover": {
      background: "#101558",
      color: "#FFFFFF",
    },
  },
  circular: {
    width: "29px !important",
    height: "29px !important",
  },
}));

export { useStyles };