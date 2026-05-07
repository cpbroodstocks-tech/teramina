import React from "react";
import { Fragment } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  Typography,
} from "@mui/material";
import { useStyles } from "./styles";
import { useTranslation } from "react-i18next";

const ConfirmDelete = ({
  open,
  handleClose,
  handleConfirmed,
  message = "DELETE_CONFIRM_MESSAGE",
}) => {
  const { t } = useTranslation();
  const { classes: styles } = useStyles();

  return (
    <Fragment>
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogContent className={styles.dialogContent}>
          <DialogContentText id="alert-dialog-description">
            <Typography variant="h6" className={styles.dialogText}>
              {t(message)}
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>{t("NO")}</Button>
          <Button
            className={styles.btnYesModal}
            onClick={handleConfirmed}
            variant="contained"
          >
            {t("YES")}
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  );
};

export default ConfirmDelete;
