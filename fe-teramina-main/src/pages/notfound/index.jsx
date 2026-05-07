import React from "react";
import { Button } from "@mui/material";
import { Link } from "react-router-dom";
import { useStyles } from "pages/notfound/styles";

const NotFound = () => {
  const { classes: styles } = useStyles();
  return (
    <div className={styles.contentNotFound}>
      <div className={styles.lg404}>
        <img src="/assets/images/404.png" alt="404" />
      </div>
      <div className={styles.contentNotFound__button}>
        <Link to="/">
          <Button variant="contained" className={styles.button}>
            Go to home
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
