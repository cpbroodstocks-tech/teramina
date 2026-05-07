import React, { Fragment } from "react";
import { Typography, Button } from "@mui/material";
import { useStyles } from "features/farm/start/styles";

const Start = ({ onSubmit }) => {
  const { classes: styles } = useStyles();
  return (
    <Fragment>
      <div className={styles.container}>
        <img
          src="/assets/images/blogging-bw.png"
          alt="content"
          className={styles.imgStart}
        />
        <Typography variant="h5" className={styles.descOne} align="center">
          We’re off to a good start
        </Typography>
        <Typography variant="h6" className={styles.descTwo} align="center">
          Let’s start your operation
        </Typography>
        <Button
          variant="contained"
          className={styles.btnStart}
          onClick={onSubmit}
        >
          Start
        </Button>
      </div>
    </Fragment>
  );
};

export default Start;
