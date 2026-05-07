import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  button: {
    position: "relative",
    display: "flex",
    alignSelf: "flex-start",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "6.07px 6px",
    cursor: "pointer",
    borderRadius: 10,
    color: "#000000",
    border: "2px solid transparent",
    boxShadow: "0px 1px 2px rgb(16 24 40 / 5%)",
    background: "white",
    "&:hover": {
      border: "2px solid #5383b3bf"
    },
    "& svg": {
      background: "#0000001f",
      borderRadius: "50%",
    },
  },
  buttonIcon: {
    color: "rgba(0, 0, 0, 0.54)",
  },
  calendar: {
    width: "100%",
    borderRadius: "3px",
  },
}))

export { useStyles };