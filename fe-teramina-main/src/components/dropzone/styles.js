import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()({
  dropzone: {
    padding: 15,
    borderRadius: 8,
    width: "100%",
    minHeight: 250,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "column",
    flexWrap: "wrap",
    background: "rgba(109, 125, 147, 0.15)",
    border: "2px dashed rgba(56, 78, 183, 0.3)",
  },
  uploadIcon: {
    color: "#474DA4",
    fontSize: "56px",
  },
  description: {
    marginTop: "12px",
    fontWeight: "700",
    fontSize: "16px",
    lineHeight: "24px",
    display: "flex",
    alignItems: "center",
    textAlign: "center",
    color: "#0F0F0F",
    "& span": {
      cursor: "pointer",
      color: "#474DA4",
      textDecoration: "underline",
      "&:hover": {
        color: "#101558",
      },
    },
  },
  subDescription: {
    marginTop: "12px",
    fontWeight: 400,
    fontSize: "12px",
    lineHeight: "18px",
    color: "#676767",
  },
})

export { useStyles }