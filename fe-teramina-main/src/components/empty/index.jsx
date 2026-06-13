import { useStyles } from "components/empty/styles";
import { Button, Stack, Typography } from "@mui/material";

const Empty = ({
  title = "No data to show yet",
  message = "Complete setup or adjust the selected filters to populate this view.",
  actionLabel,
  onAction,
}) => {
  const { classes: styles } = useStyles();

  return (
    <div className={styles.contentEmpty}>
      <div className={styles.lgEmpty}>
        <img src="/assets/images/empty.png" alt="empty" />
      </div>
      <Stack gap={1.25} sx={{ alignItems: "center", px: 2 }}>
        <Typography variant="h5" fontWeight={700}>{title}</Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 520 }}>{message}</Typography>
        {actionLabel && onAction && <Button variant="contained" onClick={onAction}>{actionLabel}</Button>}
      </Stack>
    </div>
  );
};

export default Empty;
