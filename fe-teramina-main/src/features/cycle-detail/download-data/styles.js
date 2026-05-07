import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(() => ({
  btnDownload: {
    color: "#161616",
    minWidth: "unset !important",
    background: "rgba(71, 77, 164, 0.32)",
    marginRight: "5px",
    borderRadius: "6px",
    padding: "10.5px",
    "&:hover": {
      color: "#161616",
      background: "rgba(71, 77, 164, 0.6)"
    },
    "& svg": {
      width: "20px",
      height: "20px"
    }
  },
  btnDownloadIcon: {
    paddingRight: "7px"
  }
}));

export { useStyles }
