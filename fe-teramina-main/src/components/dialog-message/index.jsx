import * as React from "react";
import { Box, CircularProgress, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Slide, Button } from "@mui/material";

const Transition = React.forwardRef(function Transition(props, ref) {
  return <Slide direction="up" ref={ref} {...props} />;
});

const DialogMessage = ({ open, onClose, title, message, loading = false }) => {
  return (
    <Dialog
      open={open}
      slots={{ transition: Transition }}
      keepMounted
      onClose={loading ? undefined : onClose}
      aria-labelledby="alert-dialog-title"
      aria-describedby="alert-dialog-description"
    >
      <DialogTitle id="alert-dialog-title">{title}</DialogTitle>
      <DialogContent dividers>
        <DialogContentText id="alert-dialog-slide-description">
          {message}
        </DialogContentText>
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
            <CircularProgress size={28} />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default DialogMessage;
