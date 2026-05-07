import { makeStyles } from "tss-react/mui";

const useStyles = makeStyles()(theme => ({
  pageWrapper: {
    position: "relative",
    paddingTop: 80,
    marginLeft: 270,
    padding: "15px 60px",
    [theme.breakpoints.down("sm")]: {
      marginLeft: 0,
      padding: "70px 15px 15px 15px",
    },
    [theme.breakpoints.between("sm", "md")]: {
      marginLeft: 220,
      padding: "70px 15px 15px 15px",
    },
  },
  maincontent: {
    position: "relative",
    margin: "auto"
  }
}))

export { useStyles }