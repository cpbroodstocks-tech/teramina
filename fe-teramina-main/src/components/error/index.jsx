import { useStyles } from "components/error/styles";
import { Button, Stack, Typography } from "@mui/material";

const Error = ({
  title = "Something went wrong",
  message = "We could not load this page. Try again or return to a working area.",
  actionLabel = "Try again",
  onAction = () => window.location.reload(),
  secondaryLabel = "",
  onSecondary = null,
}) => {
  const { classes: styles } = useStyles();

  return (
    <div className={styles.contentError}>
      <div className={styles.lgError}>
        <img src="/assets/images/error.png" alt="Error" />
      </div>
      <Stack gap={1.5} sx={{ alignItems: "center", px: 2 }}>
        <Typography variant="h5" fontWeight={700}>{title}</Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 520 }}>{message}</Typography>
        <Stack direction="row" gap={1}>
          {onAction && <Button variant="contained" onClick={onAction}>{actionLabel}</Button>}
          {secondaryLabel && onSecondary && <Button variant="outlined" onClick={onSecondary}>{secondaryLabel}</Button>}
        </Stack>
      </Stack>
    </div>
  );
};

export default Error;
