import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(theme => ({
  pageWrapper: {
    position: "relative",
    marginLeft: 270,
    minHeight: "100vh",
    padding: "0 40px 32px",
    background: theme.palette.background.default,
    [theme.breakpoints.down("sm")]: {
      marginLeft: 0,
      padding: "0 12px 24px",
    },
    [theme.breakpoints.between("sm", "md")]: {
      marginLeft: 220,
      padding: "0 20px 24px",
    },
  },
  maincontent: {
    position: "relative",
    margin: "auto",
    maxWidth: 1440,
  }
}))

export { useStyles }
