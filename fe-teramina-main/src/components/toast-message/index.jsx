import * as React from "react";
import { Dialog, DialogContent, Slide } from "@mui/material";
import { useToastStore } from "store/toast.store";
import { useStyles } from "components/toast-message/styles";

const Transition = React.forwardRef(function Transition(props, ref) {
  return <Slide direction="up" ref={ref} {...props} />;
});

const ToastMessage = () => {
  const { classes: styles } = useStyles();
  const { open, variant, text, setToast: handleSetToast } = useToastStore();

  const dialogIconUrl = {
    success: "/assets/images/succes-icon.png",
    error: "/assets/images/error-icon.png",
    info: "/assets/images/warning-icon.png",
  }

  return (
    <Dialog
      className={styles.dialog}
      open={open}
      onClose={() => handleSetToast({ open: false })}
      TransitionComponent={Transition}
      aria-labelledby="alert-dialog-title"
      aria-describedby="alert-dialog-description"
    >
      <DialogContent className={styles.dialogContent}>
        <div className={styles.dialogImg}>
          <img src={dialogIconUrl[variant]} alt="icon" />
        </div>
        <div className={styles.dialogText}>
          {text}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ToastMessage;
